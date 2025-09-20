#!/usr/bin/env python3
"""
Comprehensive Enrichment Service

This service ensures that LLM enrichment output is correctly stored
in ALL destination tables according to the database schema:
- articles (main content)
- content_analysis (detailed analysis)
- content_keywords (keyword relationships)
- entity_mentions (entity relationships)
- content_enrichment_status (tracking)
- enrichment_log (processing logs)
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from streamlined_french_enricher import StreamlinedFrenchEnricher

logger = logging.getLogger(__name__)

class ComprehensiveEnrichmentService:
    """Enhanced enrichment service that stores data in all schema tables."""
    
    def __init__(self, ollama_client, db_manager):
        self.french_enricher = StreamlinedFrenchEnricher(ollama_client)
        self.db_manager = db_manager
        self.ai_model_version = "qwen2.5:7b"
        
    def process_article(self, article_data: Dict[str, Any]) -> bool:
        """Process article with comprehensive database storage."""
        start_time = time.time()
        article_id = article_data.get('id')
        
        try:
            # Step 1: Get content for processing
            content = article_data.get('content', '')
            if not content:
                content = f"{article_data.get('title', '')} {article_data.get('description', '')}".strip()
            
            if not content:
                logger.warning(f"No content to process for article {article_id}")
                return False
            
            # Step 2: Enrich with streamlined logic
            result = self.french_enricher.enrich_content(content, 'article')
            
            if result.get('status') == 'failed':
                logger.error(f"Failed to enrich article {article_id}: {result.get('error')}")
                return False
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Step 3: Store in articles table (main content)
            success = self._update_article_main(article_id, result, processing_time_ms)
            if not success:
                return False
            
            # Step 4: Store in content_analysis table
            analysis_id = self._store_content_analysis(article_id, 'article', result, processing_time_ms)
            
            # Step 5: Store keywords in content_keywords table
            self._store_content_keywords(article_id, 'article', result.get('keywords', []))
            
            # Step 6: Store entities in entity_mentions table
            self._store_entity_mentions(article_id, 'article', result.get('entities', []), content)
            
            # Step 7: Update enrichment status tracking
            self._update_enrichment_status(article_id, 'article', result, processing_time_ms)
            
            # Step 8: Update enrichment state for source tracking
            source_id = article_data.get('source_id')
            content_hash = article_data.get('content_hash', '')
            if source_id:
                self.update_enrichment_state('article', source_id, article_id, content_hash)
            
            logger.info(f"✅ Article {article_id} comprehensively enriched")
            return True
            
        except Exception as e:
            logger.error(f"Comprehensive enrichment failed for article {article_id}: {e}")
            return False
    
    def process_post(self, post_data: Dict[str, Any]) -> bool:
        """Process social media post with comprehensive database storage."""
        start_time = time.time()
        post_id = post_data.get('id')
        
        try:
            content = post_data.get('content', '')
            if not content:
                logger.warning(f"No content to process for post {post_id}")
                return False
            
            # Enrich content
            result = self.french_enricher.enrich_content(content, 'social_media_post')
            
            if result.get('status') == 'failed':
                logger.error(f"Failed to enrich post {post_id}: {result.get('error')}")
                return False
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Store in all relevant tables
            success = self._update_post_main(post_id, result, processing_time_ms)
            if not success:
                return False
            
            self._store_content_analysis(post_id, 'post', result, processing_time_ms)
            self._store_content_keywords(post_id, 'post', result.get('keywords', []))
            self._store_entity_mentions(post_id, 'post', result.get('entities', []), content)
            self._update_enrichment_status(post_id, 'post', result, processing_time_ms)
            
            # Update enrichment state for source tracking
            source_id = post_data.get('source_id')
            content_hash = post_data.get('content_hash', '')
            if source_id:
                self.update_enrichment_state('social_media_post', source_id, post_id, content_hash)
            
            logger.info(f"✅ Post {post_id} comprehensively enriched")
            return True
            
        except Exception as e:
            logger.error(f"Comprehensive enrichment failed for post {post_id}: {e}")
            return False
    
    def process_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Process comment with comprehensive database storage."""
        start_time = time.time()
        comment_id = comment_data.get('id')
        
        try:
            content = comment_data.get('content', '')
            if not content:
                logger.warning(f"No content to process for comment {comment_id}")
                return False
            
            # Enrich content (metadata only for comments)
            result = self.french_enricher.enrich_content(content, 'comment')
            
            if result.get('status') == 'failed':
                logger.error(f"Failed to enrich comment {comment_id}: {result.get('error')}")
                return False
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Store in all relevant tables
            success = self._update_comment_main(comment_id, result)
            if not success:
                return False
            
            self._store_content_analysis(comment_id, 'comment', result, processing_time_ms)
            self._store_content_keywords(comment_id, 'comment', result.get('keywords', []))
            self._store_entity_mentions(comment_id, 'comment', result.get('entities', []), content)
            self._update_enrichment_status(comment_id, 'comment', result, processing_time_ms)
            
            # Update enrichment state (comments don't have source_id in the same way)
            # Could be enhanced based on your comment structure
            
            logger.info(f"✅ Comment {comment_id} comprehensively enriched")
            return True
            
        except Exception as e:
            logger.error(f"Comprehensive enrichment failed for comment {comment_id}: {e}")
            return False
    
    def _update_article_main(self, article_id: int, result: Dict[str, Any], processing_time_ms: int) -> bool:
        """Update articles table with enrichment data."""
        try:
            # Get category_id from French category name
            category_id = None
            if result.get('category'):
                category_id = self._get_category_id_by_french_name(result['category'])
            
            update_data = {
                'sentiment': result.get('sentiment'),
                'sentiment_score': result.get('sentiment_score'),
                'keywords': json.dumps(result.get('keywords', []), ensure_ascii=False),
                'summary': result.get('summary'),
                'category': result.get('category'),
                'category_id': category_id,
                'enriched_at': datetime.now().isoformat(),
                'enrichment_confidence': result.get('confidence'),
                'content_fr': result.get('content_fr')  # Only if translation was needed
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            response = self.db_manager.client.table("articles") \
                .update(update_data) \
                .eq("id", article_id) \
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Failed to update articles table for {article_id}: {e}")
            return False
    
    def _update_post_main(self, post_id: int, result: Dict[str, Any], processing_time_ms: int) -> bool:
        """Update social_media_posts table with enrichment data."""
        try:
            category_id = None
            if result.get('category'):
                category_id = self._get_category_id_by_french_name(result['category'])
            
            update_data = {
                'sentiment': result.get('sentiment'),
                'sentiment_score': result.get('sentiment_score'),
                'summary': result.get('summary'),
                'category_id': category_id,
                'enriched_at': datetime.now().isoformat(),
                'enrichment_confidence': result.get('confidence'),
                'content_fr': result.get('content_fr')
            }
            
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            response = self.db_manager.client.table("social_media_posts") \
                .update(update_data) \
                .eq("id", post_id) \
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Failed to update social_media_posts table for {post_id}: {e}")
            return False
    
    def _update_comment_main(self, comment_id: int, result: Dict[str, Any]) -> bool:
        """Update social_media_comments table with enrichment data."""
        try:
            update_data = {
                'sentiment': result.get('sentiment'),
                'sentiment_score': result.get('sentiment_score'),
                'enriched_at': datetime.now().isoformat(),
                'enrichment_confidence': result.get('confidence')
            }
            
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            response = self.db_manager.client.table("social_media_comments") \
                .update(update_data) \
                .eq("id", comment_id) \
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Failed to update social_media_comments table for {comment_id}: {e}")
            return False
    
    def _store_content_analysis(self, content_id: int, content_type: str, result: Dict[str, Any], processing_time_ms: int) -> Optional[int]:
        """Store detailed analysis in content_analysis table."""
        try:
            # Map content types
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            # Map sentiment to English for content_analysis table
            sentiment_mapping = {
                'positif': 'positive',
                'négatif': 'negative',
                'neutre': 'neutral'
            }
            
            category_id = None
            if result.get('category'):
                category_id = self._get_category_id_by_french_name(result['category'])
            
            analysis_data = {
                'content_type': content_type_mapping.get(content_type, content_type),
                'content_id': content_id,
                'sentiment': sentiment_mapping.get(result.get('sentiment', 'neutre'), 'neutral'),
                'sentiment_score': result.get('sentiment_score'),
                'sentiment_confidence': result.get('confidence'),
                'primary_category_id': category_id,
                'language_detected': result.get('detected_language', 'fr'),
                'ai_model_version': self.ai_model_version,
                'processing_time_ms': processing_time_ms
            }
            
            response = self.db_manager.client.table("content_analysis") \
                .insert(analysis_data) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Failed to store content_analysis for {content_type} {content_id}: {e}")
            return None
    
    def _store_content_keywords(self, content_id: int, content_type: str, keywords: List[str]):
        """Store keywords in content_keywords table."""
        try:
            if not keywords:
                return
            
            # Map content types
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            for i, keyword in enumerate(keywords[:10]):  # Limit to top 10
                # Get or create keyword
                keyword_id = self._get_or_create_keyword(keyword)
                if not keyword_id:
                    continue
                
                # Calculate importance score (higher for earlier keywords)
                importance_score = max(0.1, 1.0 - (i * 0.1))
                
                keyword_data = {
                    'content_type': content_type_mapping.get(content_type, content_type),
                    'content_id': content_id,
                    'keyword_id': keyword_id,
                    'importance_score': importance_score,
                    'position_first': i + 1,
                    'occurrence_count': 1
                }
                
                try:
                    self.db_manager.client.table("content_keywords") \
                        .insert(keyword_data) \
                        .execute()
                except Exception as e:
                    # Ignore duplicate key errors
                    if "duplicate key" not in str(e).lower():
                        logger.warning(f"Failed to store keyword '{keyword}': {e}")
            
        except Exception as e:
            logger.error(f"Failed to store keywords for {content_type} {content_id}: {e}")
    
    def _store_entity_mentions(self, content_id: int, content_type: str, entities: List[Dict], content: str):
        """Store entities in entity_mentions table."""
        try:
            if not entities:
                return
            
            # Map content types
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            for entity in entities:
                entity_text = entity.get('text', '')
                entity_type = entity.get('type', 'PERSON')
                confidence = entity.get('confidence', 0.0)
                
                if not entity_text:
                    continue
                
                # Get or create entity
                entity_id = self._get_or_create_entity(entity_text, entity_type)
                if not entity_id:
                    continue
                
                # Find position in content
                position_start = content.lower().find(entity_text.lower())
                position_end = position_start + len(entity_text) if position_start >= 0 else None
                
                # Extract context snippet
                context_snippet = self._extract_context_snippet(content, entity_text, position_start)
                
                mention_data = {
                    'entity_id': entity_id,
                    'content_type': content_type_mapping.get(content_type, content_type),
                    'content_id': content_id,
                    'mentioned_text': entity_text,
                    'context_snippet': context_snippet,
                    'position_start': position_start if position_start >= 0 else None,
                    'position_end': position_end,
                    'extraction_confidence': confidence
                }
                
                try:
                    self.db_manager.client.table("entity_mentions") \
                        .insert(mention_data) \
                        .execute()
                except Exception as e:
                    # Ignore duplicate errors
                    if "duplicate key" not in str(e).lower():
                        logger.warning(f"Failed to store entity mention '{entity_text}': {e}")
            
        except Exception as e:
            logger.error(f"Failed to store entities for {content_type} {content_id}: {e}")
    
    def _update_enrichment_status(self, content_id: int, content_type: str, result: Dict[str, Any], processing_time_ms: int):
        """Update or create enrichment status tracking."""
        try:
            # Map content types
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            status_data = {
                'content_type': content_type_mapping.get(content_type, content_type),
                'content_id': content_id,
                'is_enriched': True,
                'enrichment_version': self.ai_model_version,
                'last_enriched_at': datetime.now().isoformat(),
                'enrichment_attempts': 1,
                'last_attempt_at': datetime.now().isoformat(),
                'has_sentiment': bool(result.get('sentiment')),
                'has_entities': bool(result.get('entities')),
                'has_keywords': bool(result.get('keywords')),
                'has_category': bool(result.get('category')),
                'enrichment_confidence': result.get('confidence'),
                'processing_time_ms': processing_time_ms
            }
            
            # Try to update existing record, or insert new one
            try:
                # Check if record exists
                existing = self.db_manager.client.table("content_enrichment_status") \
                    .select("id") \
                    .eq("content_type", status_data['content_type']) \
                    .eq("content_id", content_id) \
                    .execute()
                
                if existing.data:
                    # Update existing
                    self.db_manager.client.table("content_enrichment_status") \
                        .update(status_data) \
                        .eq("content_type", status_data['content_type']) \
                        .eq("content_id", content_id) \
                        .execute()
                else:
                    # Insert new
                    self.db_manager.client.table("content_enrichment_status") \
                        .insert(status_data) \
                        .execute()
                        
            except Exception as e:
                logger.warning(f"Failed to update enrichment status: {e}")
            
        except Exception as e:
            logger.error(f"Failed to update enrichment status for {content_type} {content_id}: {e}")
    
    def _get_category_id_by_french_name(self, french_name: str) -> Optional[int]:
        """Get category ID by French name."""
        try:
            response = self.db_manager.client.table("content_categories") \
                .select("id") \
                .eq("name_fr", french_name) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get category ID for '{french_name}': {e}")
            return None
    
    def _get_or_create_keyword(self, keyword: str) -> Optional[int]:
        """Get existing keyword ID or create new keyword."""
        try:
            # Check if keyword exists
            response = self.db_manager.client.table("keywords") \
                .select("id") \
                .eq("keyword", keyword) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            
            # Create new keyword
            keyword_data = {
                'keyword': keyword,
                'normalized_form': keyword.lower(),
                'language': 'fr',
                'frequency_count': 1
            }
            
            response = self.db_manager.client.table("keywords") \
                .insert(keyword_data) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get/create keyword '{keyword}': {e}")
            return None
    
    def _get_or_create_entity(self, entity_name: str, entity_type: str) -> Optional[int]:
        """Get existing entity ID or create new entity."""
        try:
            # Get entity type ID
            entity_type_id = self._get_entity_type_id(entity_type)
            if not entity_type_id:
                return None
            
            # Check if entity exists
            response = self.db_manager.client.table("entities") \
                .select("id") \
                .eq("canonical_name", entity_name) \
                .eq("entity_type_id", entity_type_id) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            
            # Create new entity
            entity_data = {
                'canonical_name': entity_name,
                'entity_type_id': entity_type_id,
                'confidence_score': 0.8,
                'is_canonical': True
            }
            
            response = self.db_manager.client.table("entities") \
                .insert(entity_data) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get/create entity '{entity_name}': {e}")
            return None
    
    def _get_entity_type_id(self, entity_type: str) -> Optional[int]:
        """Get entity type ID."""
        try:
            response = self.db_manager.client.table("entity_types") \
                .select("id") \
                .eq("name", entity_type) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get entity type ID for '{entity_type}': {e}")
            return None
    
    def _extract_context_snippet(self, content: str, entity_text: str, position: int, context_length: int = 100) -> str:
        """Extract context snippet around entity mention."""
        if position < 0:
            return content[:context_length] + "..." if len(content) > context_length else content
        
        start = max(0, position - context_length // 2)
        end = min(len(content), position + len(entity_text) + context_length // 2)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def update_enrichment_state(self, content_type: str, source_id: Optional[int], 
                              last_content_id: int, content_hash: str):
        """Update or create enrichment state according to schema."""
        try:
            # Map content types for enrichment_state table
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post', 
                'comment': 'comment'
            }
            
            mapped_content_type = content_type_mapping.get(content_type, content_type)
            
            # Check if enrichment state exists for this source and content type
            existing_state = self.db_manager.client.table("enrichment_state") \
                .select("id, total_items_processed, successful_enrichments, failed_enrichments") \
                .eq("content_type", mapped_content_type) \
                .eq("source_id", source_id) \
                .execute()
            
            if existing_state.data:
                # Update existing state
                current_state = existing_state.data[0]
                update_data = {
                    'last_enriched_content_id': last_content_id,
                    'last_enriched_at': datetime.now().isoformat(),
                    'last_enriched_content_hash': content_hash,
                    'total_items_processed': current_state.get('total_items_processed', 0) + 1,
                    'successful_enrichments': current_state.get('successful_enrichments', 0) + 1,
                    'updated_at': datetime.now().isoformat()
                }
                
                self.db_manager.client.table("enrichment_state") \
                    .update(update_data) \
                    .eq("id", current_state['id']) \
                    .execute()
            else:
                # Create new state record
                state_data = {
                    'content_type': mapped_content_type,
                    'source_id': source_id,
                    'last_enriched_content_id': last_content_id,
                    'last_enriched_at': datetime.now().isoformat(),
                    'last_enriched_content_hash': content_hash,
                    'enrichment_enabled': True,
                    'auto_enrich_new_content': True,
                    'total_items_processed': 1,
                    'successful_enrichments': 1,
                    'failed_enrichments': 0,
                    'last_batch_size': 1
                }
                
                self.db_manager.client.table("enrichment_state") \
                    .insert(state_data) \
                    .execute()
                    
        except Exception as e:
            logger.error(f"Failed to update enrichment state: {e}")
    
    def update_enrichment_state_failure(self, content_type: str, source_id: Optional[int]):
        """Update enrichment state for failed processing."""
        try:
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            mapped_content_type = content_type_mapping.get(content_type, content_type)
            
            # Check if state exists
            existing_state = self.db_manager.client.table("enrichment_state") \
                .select("id, total_items_processed, failed_enrichments") \
                .eq("content_type", mapped_content_type) \
                .eq("source_id", source_id) \
                .execute()
            
            if existing_state.data:
                current_state = existing_state.data[0]
                update_data = {
                    'total_items_processed': current_state.get('total_items_processed', 0) + 1,
                    'failed_enrichments': current_state.get('failed_enrichments', 0) + 1,
                    'updated_at': datetime.now().isoformat()
                }
                
                self.db_manager.client.table("enrichment_state") \
                    .update(update_data) \
                    .eq("id", current_state['id']) \
                    .execute()
                    
        except Exception as e:
            logger.error(f"Failed to update enrichment state failure: {e}")
    
    def log_enrichment_batch(self, content_type: str, source_id: Optional[int], 
                           items_processed: int, items_successful: int, 
                           items_failed: int, processing_duration_ms: int,
                           started_at: datetime, batch_size: int = None):
        """Log batch enrichment statistics according to schema."""
        try:
            # Map content types for enrichment_log table
            content_type_mapping = {
                'article': 'article',
                'social_media_post': 'post',
                'comment': 'comment'
            }
            
            mapped_content_type = content_type_mapping.get(content_type, content_type)
            
            log_data = {
                'content_type': mapped_content_type,
                'source_id': source_id,
                'started_at': started_at.isoformat(),
                'finished_at': datetime.now().isoformat(),
                'processing_duration_ms': processing_duration_ms,
                'items_processed': items_processed,
                'items_successful': items_successful,
                'items_failed': items_failed,
                'items_skipped': 0,  # Could be enhanced to track skipped items
                'ai_model_used': 'ollama',
                'ai_model_version': self.ai_model_version,
                'average_processing_time_ms': processing_duration_ms // max(1, items_processed),
                'batch_size': batch_size or items_processed,
                'processing_mode': 'batch',
                'status': 'success' if items_failed == 0 else ('partial' if items_successful > 0 else 'failed'),
                'error_count': items_failed
            }
            
            self.db_manager.client.table("enrichment_log") \
                .insert(log_data) \
                .execute()
                
            logger.info(f"✅ Logged enrichment batch: {items_successful}/{items_processed} successful")
                
        except Exception as e:
            logger.error(f"Failed to log enrichment batch: {e}")

if __name__ == "__main__":
    print("🔧 Comprehensive Enrichment Service")
    print("Ensures LLM output is stored in ALL destination tables:")
    print("- articles (main content)")
    print("- content_analysis (detailed analysis)")
    print("- content_keywords (keyword relationships)")
    print("- entity_mentions (entity relationships)")
    print("- content_enrichment_status (tracking)")
    print("- enrichment_log (processing logs)")
