"""
Enhanced AI Enrichment Service with Separate Pipelines.

This module provides three separate AI enrichment pipelines:
1. Article Enrichment Pipeline
2. Facebook Post Enrichment Pipeline  
3. Comment Enrichment Pipeline (Enhanced)

Each pipeline can be run independently or together, with comprehensive
state management and logging.
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

from ..core.ollama_client import OllamaClient, OllamaConfig
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

class ContentType(str, Enum):
    """Content types for enrichment pipelines."""
    ARTICLE = "article"
    POST = "post" 
    COMMENT = "comment"

class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class EnrichmentStats:
    """Statistics for enrichment operations."""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    processing_time_ms: int = 0
    average_confidence: float = 0.0

class EnhancedEnrichmentService:
    """
    Enhanced AI Enrichment Service with separate pipelines for each content type.
    
    Features:
    - Separate pipelines for articles, posts, and comments
    - Enhanced comment enrichment with keywords and entities
    - Comprehensive state management and logging
    - Individual or batch processing capabilities
    - Performance monitoring and error handling
    """
    
    def __init__(self, ollama_config: Optional[OllamaConfig] = None):
        """Initialize the enhanced enrichment service."""
        self.db_manager = DatabaseManager()
        self.ollama_client = OllamaClient(ollama_config or OllamaConfig())
        
        # Pipeline status tracking
        self.pipeline_status = {
            ContentType.ARTICLE: PipelineStatus.PAUSED,
            ContentType.POST: PipelineStatus.PAUSED,
            ContentType.COMMENT: PipelineStatus.PAUSED
        }
        
        logger.info("Enhanced enrichment service initialized")
    
    # =====================================================
    # Article Enrichment Pipeline
    # =====================================================
    
    def enrich_articles(self, 
                       limit: Optional[int] = None,
                       source_ids: Optional[List[int]] = None,
                       force_reprocess: bool = False) -> EnrichmentStats:
        """Run the article enrichment pipeline."""
        content_type = ContentType.ARTICLE
        self.pipeline_status[content_type] = PipelineStatus.RUNNING
        
        logger.info(f"Starting article enrichment pipeline (limit={limit})")
        
        try:
            log_id = self._start_enrichment_log(content_type, source_ids)
            stats = EnrichmentStats()
            start_time = time.time()
            
            # Get articles to process
            articles = self._get_articles_for_enrichment(
                limit=limit, source_ids=source_ids, force_reprocess=force_reprocess
            )
            
            stats.total_items = len(articles)
            logger.info(f"Found {stats.total_items} articles to enrich")
            
            # Process each article
            for article in articles:
                try:
                    result = self._enrich_single_article(article)
                    if result['success']:
                        stats.successful_items += 1
                        stats.average_confidence += result.get('confidence', 0.0)
                    else:
                        stats.failed_items += 1
                    
                    stats.processed_items += 1
                    
                    if stats.processed_items % 10 == 0:
                        logger.info(f"Article progress: {stats.processed_items}/{stats.total_items}")
                        
                except Exception as e:
                    logger.error(f"Failed to enrich article {article.get('id')}: {e}")
                    stats.failed_items += 1
                    stats.processed_items += 1
            
            # Calculate final statistics
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            if stats.successful_items > 0:
                stats.average_confidence /= stats.successful_items
            
            self._update_enrichment_state(content_type, stats)
            self._complete_enrichment_log(log_id, stats)
            
            self.pipeline_status[content_type] = PipelineStatus.COMPLETED
            logger.info(f"Article enrichment completed: {stats.successful_items}/{stats.total_items} successful")
            
            return stats
            
        except Exception as e:
            logger.error(f"Article enrichment pipeline failed: {e}")
            self.pipeline_status[content_type] = PipelineStatus.FAILED
            raise
    
    def _enrich_single_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single article with full AI analysis."""
        start_time = time.time()
        
        try:
            # Prepare content for analysis
            content = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
            
            # Detect language and translate if needed
            language_detected = self._detect_language(content)
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform AI enrichment on French content
            enrichment_result = self._perform_full_enrichment(content_fr, language_detected)
            
            # Update article in database
            success = self.db_manager.client.rpc('update_article_enrichment', {
                'p_article_id': article['id'],
                'p_sentiment': enrichment_result['sentiment'],
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_keywords': json.dumps(enrichment_result['keywords']),
                'p_summary': enrichment_result['summary'],
                'p_category': enrichment_result['category']['primary_category'],
                'p_category_id': self._get_category_id(enrichment_result['category']['primary_category']),
                'p_confidence': enrichment_result['confidence'],
                'p_content_fr': content_fr
            }).execute()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'confidence': enrichment_result['confidence'],
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich article {article['id']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    # =====================================================
    # Facebook Post Enrichment Pipeline
    # =====================================================
    
    def enrich_posts(self,
                    limit: Optional[int] = None,
                    source_ids: Optional[List[int]] = None,
                    force_reprocess: bool = False) -> EnrichmentStats:
        """Run the Facebook post enrichment pipeline."""
        content_type = ContentType.POST
        self.pipeline_status[content_type] = PipelineStatus.RUNNING
        
        logger.info(f"Starting post enrichment pipeline (limit={limit})")
        
        try:
            log_id = self._start_enrichment_log(content_type, source_ids)
            stats = EnrichmentStats()
            start_time = time.time()
            
            # Get posts to process
            posts = self._get_posts_for_enrichment(
                limit=limit, source_ids=source_ids, force_reprocess=force_reprocess
            )
            
            stats.total_items = len(posts)
            logger.info(f"Found {stats.total_items} posts to enrich")
            
            # Process each post
            for post in posts:
                try:
                    result = self._enrich_single_post(post)
                    if result['success']:
                        stats.successful_items += 1
                        stats.average_confidence += result.get('confidence', 0.0)
                    else:
                        stats.failed_items += 1
                    
                    stats.processed_items += 1
                    
                    if stats.processed_items % 10 == 0:
                        logger.info(f"Post progress: {stats.processed_items}/{stats.total_items}")
                        
                except Exception as e:
                    logger.error(f"Failed to enrich post {post.get('id')}: {e}")
                    stats.failed_items += 1
                    stats.processed_items += 1
            
            # Calculate final statistics
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            if stats.successful_items > 0:
                stats.average_confidence /= stats.successful_items
            
            self._update_enrichment_state(content_type, stats)
            self._complete_enrichment_log(log_id, stats)
            
            self.pipeline_status[content_type] = PipelineStatus.COMPLETED
            logger.info(f"Post enrichment completed: {stats.successful_items}/{stats.total_items} successful")
            
            return stats
            
        except Exception as e:
            logger.error(f"Post enrichment pipeline failed: {e}")
            self.pipeline_status[content_type] = PipelineStatus.FAILED
            raise
    
    def _enrich_single_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single Facebook post with full AI analysis."""
        start_time = time.time()
        
        try:
            content = post.get('content', '')
            
            # Detect language and translate if needed
            language_detected = self._detect_language(content)
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform AI enrichment on French content
            enrichment_result = self._perform_full_enrichment(content_fr, language_detected)
            
            # Update post in database
            success = self.db_manager.client.rpc('update_post_enrichment', {
                'p_post_id': post['id'],
                'p_sentiment': enrichment_result['sentiment'],
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_summary': enrichment_result['summary'],
                'p_category_id': self._get_category_id(enrichment_result['category']['primary_category']),
                'p_confidence': enrichment_result['confidence'],
                'p_content_fr': content_fr
            }).execute()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'confidence': enrichment_result['confidence'],
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich post {post['id']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    # =====================================================
    # Comment Enrichment Pipeline (Enhanced)
    # =====================================================
    
    def enrich_comments(self,
                       limit: Optional[int] = None,
                       post_ids: Optional[List[int]] = None,
                       force_reprocess: bool = False) -> EnrichmentStats:
        """Run the enhanced comment enrichment pipeline."""
        content_type = ContentType.COMMENT
        self.pipeline_status[content_type] = PipelineStatus.RUNNING
        
        logger.info(f"Starting enhanced comment enrichment pipeline (limit={limit})")
        
        try:
            log_id = self._start_enrichment_log(content_type, post_ids)
            stats = EnrichmentStats()
            start_time = time.time()
            
            # Get comments to process
            comments = self._get_comments_for_enrichment(
                limit=limit, post_ids=post_ids, force_reprocess=force_reprocess
            )
            
            stats.total_items = len(comments)
            logger.info(f"Found {stats.total_items} comments to enrich")
            
            # Process each comment
            for comment in comments:
                try:
                    result = self._enrich_single_comment(comment)
                    if result['success']:
                        stats.successful_items += 1
                        stats.average_confidence += result.get('confidence', 0.0)
                    else:
                        stats.failed_items += 1
                    
                    stats.processed_items += 1
                    
                    if stats.processed_items % 25 == 0:
                        logger.info(f"Comment progress: {stats.processed_items}/{stats.total_items}")
                        
                except Exception as e:
                    logger.error(f"Failed to enrich comment {comment.get('id')}: {e}")
                    stats.failed_items += 1
                    stats.processed_items += 1
            
            # Calculate final statistics
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            if stats.successful_items > 0:
                stats.average_confidence /= stats.successful_items
            
            self._update_enrichment_state(content_type, stats)
            self._complete_enrichment_log(log_id, stats)
            
            # Populate cross-reference tables
            logger.info("Populating comment keywords and entities...")
            keyword_result = self.db_manager.client.rpc('populate_comment_keywords').execute()
            entity_result = self.db_manager.client.rpc('populate_comment_entities').execute()
            
            keyword_count = keyword_result.data if keyword_result.data else 0
            entity_count = entity_result.data if entity_result.data else 0
            
            logger.info(f"Populated {keyword_count} keywords and {entity_count} entities")
            
            self.pipeline_status[content_type] = PipelineStatus.COMPLETED
            logger.info(f"Comment enrichment completed: {stats.successful_items}/{stats.total_items} successful")
            
            return stats
            
        except Exception as e:
            logger.error(f"Comment enrichment pipeline failed: {e}")
            self.pipeline_status[content_type] = PipelineStatus.FAILED
            raise
    
    def _enrich_single_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single comment with enhanced AI analysis."""
        start_time = time.time()
        
        try:
            content = comment.get('content', '')
            content_length = len(content)
            
            # Detect language and translate if needed
            language_detected = self._detect_language(content)
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform enhanced comment enrichment
            enrichment_result = self._perform_enhanced_comment_enrichment(content_fr, language_detected)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Update comment in database using the new enhanced function
            success = self.db_manager.client.rpc('update_comment_enrichment', {
                'p_comment_id': comment['id'],
                'p_sentiment': enrichment_result['sentiment'],
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_keywords': json.dumps(enrichment_result['keywords']),
                'p_entities': json.dumps(enrichment_result['entities']),
                'p_content_fr': content_fr,
                'p_keywords_fr': json.dumps(enrichment_result['keywords_fr']),
                'p_entities_fr': json.dumps(enrichment_result['entities_fr']),
                'p_language_detected': language_detected,
                'p_confidence': enrichment_result['confidence'],
                'p_processing_time_ms': processing_time_ms,
                'p_content_length': content_length,
                'p_ai_model_version': 'qwen2.5:7b'
            }).execute()
            
            return {
                'success': True,
                'confidence': enrichment_result['confidence'],
                'processing_time_ms': processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich comment {comment['id']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
