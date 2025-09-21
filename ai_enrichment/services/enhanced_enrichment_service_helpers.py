"""
Helper methods for Enhanced AI Enrichment Service.
This file contains the remaining helper methods and utility functions.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class EnhancedEnrichmentServiceHelpers:
    """Helper methods for the Enhanced Enrichment Service."""
    
    def __init__(self, db_manager, ollama_client):
        self.db_manager = db_manager
        self.ollama_client = ollama_client
    
    # =====================================================
    # Unified Pipeline Runner
    # =====================================================
    
    def run_all_pipelines(self,
                         article_limit: Optional[int] = None,
                         post_limit: Optional[int] = None,
                         comment_limit: Optional[int] = None,
                         force_reprocess: bool = False) -> Dict[str, Any]:
        """Run all three enrichment pipelines in sequence."""
        logger.info("Starting all enrichment pipelines")
        results = {}
        
        try:
            # Run article pipeline
            logger.info("=== ARTICLE ENRICHMENT PIPELINE ===")
            results['articles'] = self.enrich_articles(
                limit=article_limit,
                force_reprocess=force_reprocess
            )
            
            # Run post pipeline
            logger.info("=== POST ENRICHMENT PIPELINE ===")
            results['posts'] = self.enrich_posts(
                limit=post_limit,
                force_reprocess=force_reprocess
            )
            
            # Run comment pipeline
            logger.info("=== COMMENT ENRICHMENT PIPELINE ===")
            results['comments'] = self.enrich_comments(
                limit=comment_limit,
                force_reprocess=force_reprocess
            )
            
            # Summary
            total_processed = sum(stats.processed_items for stats in results.values())
            total_successful = sum(stats.successful_items for stats in results.values())
            
            logger.info(f"All pipelines completed: {total_successful}/{total_processed} items successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    # =====================================================
    # Data Retrieval Methods
    # =====================================================
    
    def _get_articles_for_enrichment(self, limit=None, source_ids=None, force_reprocess=False):
        """Get articles that need enrichment."""
        query = self.db_manager.client.table("articles").select("*")
        
        if not force_reprocess:
            query = query.is_("enriched_at", "null")
        
        if source_ids:
            query = query.in_("source_id", source_ids)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
    
    def _get_posts_for_enrichment(self, limit=None, source_ids=None, force_reprocess=False):
        """Get posts that need enrichment."""
        query = self.db_manager.client.table("social_media_posts").select("*")
        
        if not force_reprocess:
            query = query.is_("enriched_at", "null")
        
        if source_ids:
            query = query.in_("source_id", source_ids)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
    
    def _get_comments_for_enrichment(self, limit=None, post_ids=None, force_reprocess=False):
        """Get comments that need enrichment."""
        query = self.db_manager.client.table("social_media_comments").select("*")
        
        if not force_reprocess:
            query = query.is_("enriched_at", "null")
        
        if post_ids:
            query = query.in_("post_id", post_ids)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
    
    # =====================================================
    # Language Processing Methods
    # =====================================================
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of content."""
        # Simple heuristic - check for Arabic characters
        arabic_chars = sum(1 for char in content if '\u0600' <= char <= '\u06FF')
        if arabic_chars > len(content) * 0.3:
            return 'ar'
        return 'fr'
    
    def _translate_to_french(self, content: str) -> str:
        """Translate Arabic content to French using Ollama."""
        try:
            prompt = f"""Translate the following Arabic text to French. Return only the French translation, no explanations:

{content}"""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            return response.get('response', content)
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return content
    
    # =====================================================
    # AI Enrichment Methods
    # =====================================================
    
    def _perform_full_enrichment(self, content: str, language: str) -> Dict[str, Any]:
        """Perform full AI enrichment for articles and posts."""
        try:
            prompt = f"""Analyze the following French content and provide AI enrichment in JSON format.

Content: {content}

Requirements:
1. Sentiment analysis (positive/negative/neutral)
2. Extract top 10 keywords with importance scores
3. Identify named entities (persons, organizations, locations)
4. Classify into primary and secondary categories
5. Generate Arabic summary (max 500 chars)

Focus on Tunisian context and entities. Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.85,
  "keywords": [
    {{"text": "keyword", "importance": 0.95, "category": "politics", "normalized_form": "normalized"}}
  ],
  "entities": [
    {{"text": "entity", "type": "PERSON", "canonical_name": "Name", "confidence": 0.95, "is_tunisian": true}}
  ],
  "category": {{
    "primary_category": "politics",
    "secondary_categories": ["government"],
    "confidence": 0.88
  }},
  "summary": "Arabic summary",
  "confidence": 0.89
}}"""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            # Parse JSON response
            result = json.loads(response.get('response', '{}'))
            
            # Validate and set defaults
            result.setdefault('sentiment', 'neutral')
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('keywords', [])
            result.setdefault('entities', [])
            result.setdefault('category', {'primary_category': 'other', 'confidence': 0.5})
            result.setdefault('summary', '')
            result.setdefault('confidence', 0.7)
            
            return result
            
        except Exception as e:
            logger.error(f"Full enrichment failed: {e}")
            return {
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'keywords': [],
                'entities': [],
                'category': {'primary_category': 'other', 'confidence': 0.5},
                'summary': '',
                'confidence': 0.1
            }
    
    def _perform_enhanced_comment_enrichment(self, content: str, language: str) -> Dict[str, Any]:
        """Perform enhanced AI enrichment specifically for comments."""
        try:
            prompt = f"""Analyze the following French comment and provide enhanced AI enrichment in JSON format.

Comment: {content}

Requirements:
1. Sentiment analysis (positive/negative/neutral)
2. Extract top 5 keywords with importance scores
3. Identify named entities (persons, organizations, locations)
4. Provide French translation of keywords and entities
5. Detect language

Focus on Tunisian context. Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.72,
  "keywords": [
    {{"text": "ممتاز", "importance": 0.85, "category": "opinion", "normalized_form": "excellent"}}
  ],
  "entities": [
    {{"text": "تونس", "type": "LOCATION", "canonical_name": "Tunisia", "confidence": 0.95, "is_tunisian": true}}
  ],
  "keywords_fr": [
    {{"text": "excellent", "importance": 0.85, "original_text": "ممتاز"}}
  ],
  "entities_fr": [
    {{"text": "Tunisie", "canonical_name": "Tunisia", "original_text": "تونس"}}
  ],
  "confidence": 0.85
}}"""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            # Parse JSON response
            result = json.loads(response.get('response', '{}'))
            
            # Validate and set defaults
            result.setdefault('sentiment', 'neutral')
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('keywords', [])
            result.setdefault('entities', [])
            result.setdefault('keywords_fr', [])
            result.setdefault('entities_fr', [])
            result.setdefault('confidence', 0.7)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced comment enrichment failed: {e}")
            return {
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'keywords': [],
                'entities': [],
                'keywords_fr': [],
                'entities_fr': [],
                'confidence': 0.1
            }
    
    # =====================================================
    # Database Helper Methods
    # =====================================================
    
    def _get_category_id(self, category_name: str) -> Optional[int]:
        """Get category ID by name."""
        try:
            response = self.db_manager.client.table("content_categories") \
                .select("id") \
                .eq("name_en", category_name) \
                .limit(1) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get category ID for {category_name}: {e}")
            return None
    
    # =====================================================
    # State Management and Logging
    # =====================================================
    
    def _start_enrichment_log(self, content_type, source_ids: Optional[List[int]] = None) -> int:
        """Start enrichment logging."""
        try:
            log_data = {
                'content_type': content_type.value if hasattr(content_type, 'value') else content_type,
                'source_id': source_ids[0] if source_ids else None,
                'started_at': datetime.now().isoformat(),
                'ai_model_used': 'qwen2.5:7b',
                'ai_model_version': '1.0',
                'processing_mode': 'batch',
                'status': 'running'
            }
            
            response = self.db_manager.client.table("enrichment_log") \
                .insert(log_data) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return 0
            
        except Exception as e:
            logger.warning(f"Failed to start enrichment log: {e}")
            return 0
    
    def _complete_enrichment_log(self, log_id: int, stats):
        """Complete enrichment logging."""
        try:
            if log_id == 0:
                return
                
            update_data = {
                'finished_at': datetime.now().isoformat(),
                'processing_duration_ms': stats.processing_time_ms,
                'items_processed': stats.processed_items,
                'items_successful': stats.successful_items,
                'items_failed': stats.failed_items,
                'items_skipped': stats.skipped_items,
                'average_confidence_score': stats.average_confidence,
                'status': 'completed' if stats.failed_items == 0 else 'partial'
            }
            
            self.db_manager.client.table("enrichment_log") \
                .update(update_data) \
                .eq("id", log_id) \
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to complete enrichment log: {e}")
    
    def _update_enrichment_state(self, content_type, stats):
        """Update enrichment state tracking."""
        try:
            state_data = {
                'content_type': content_type.value if hasattr(content_type, 'value') else content_type,
                'last_enriched_at': datetime.now().isoformat(),
                'total_items_processed': stats.processed_items,
                'successful_enrichments': stats.successful_items,
                'failed_enrichments': stats.failed_items,
                'last_batch_size': stats.processed_items
            }
            
            # Try to update existing state, or insert new one
            response = self.db_manager.client.table("enrichment_state") \
                .upsert(state_data, on_conflict="content_type") \
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to update enrichment state: {e}")
