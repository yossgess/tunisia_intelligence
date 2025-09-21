"""
Configurable Batch AI Enrichment Script for Tunisia Intelligence System

This script uses the new configurable AI enrichment system to process articles,
posts, and comments with tunable parameters and dashboard integration.
"""

import logging
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('configurable_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import configuration and services
from config.ai_enrichment_config import (
    get_ai_enrichment_config, ContentType, ProcessingMode,
    get_article_settings, get_post_settings, get_comment_settings
)
from config.ai_enrichment_prompts import get_ai_enrichment_prompts
from ai_enrichment.services.configurable_enrichment_service import ConfigurableEnrichmentService
from config.database import DatabaseManager

@dataclass
class BatchStats:
    """Statistics for batch processing."""
    content_type: ContentType
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    total_processing_time_ms: int = 0
    average_confidence: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ConfigurableBatchEnrichment:
    """
    Configurable batch enrichment processor.
    
    Features:
    - Uses new configuration system for all parameters
    - Content type specific processing
    - Rate limiting and quality control
    - Comprehensive statistics and logging
    - Dashboard integration ready
    """
    
    def __init__(self):
        """Initialize the batch enrichment processor."""
        self.config = get_ai_enrichment_config()
        self.prompts = get_ai_enrichment_prompts()
        self.enrichment_service = ConfigurableEnrichmentService()
        self.db_manager = DatabaseManager()
        
        logger.info("Configurable batch enrichment initialized")
        logger.info(f"Configuration version: {self.config.config_version}")
        logger.info(f"AI enrichment enabled: {self.config.enabled}")
    
    def process_articles(self, limit: Optional[int] = None, force_reprocess: bool = False) -> BatchStats:
        """Process articles using configurable parameters."""
        if not self.config.is_content_type_enabled(ContentType.ARTICLE):
            logger.warning("Article processing is disabled in configuration")
            return BatchStats(ContentType.ARTICLE)
        
        settings = self.config.articles
        logger.info(f"Starting article processing with batch size: {settings.batch_size}")
        
        stats = BatchStats(ContentType.ARTICLE)
        stats.start_time = datetime.now()
        
        try:
            # Get articles to process
            articles = self._get_articles_for_processing(
                limit=limit or settings.max_items_per_run,
                force_reprocess=force_reprocess
            )
            
            stats.total_items = len(articles)
            logger.info(f"Found {stats.total_items} articles to process")
            
            if stats.total_items == 0:
                logger.info("No articles to process")
                return stats
            
            # Process in batches
            batch_size = settings.batch_size
            total_confidence = 0.0
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(articles) + batch_size - 1) // batch_size
                
                logger.info(f"Processing article batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                for article in batch:
                    try:
                        # Prepare content
                        content = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
                        
                        # Process with configurable service
                        result = self.enrichment_service.enrich_content(
                            content_id=article['id'],
                            content_type=ContentType.ARTICLE,
                            content=content,
                            force_reprocess=force_reprocess
                        )
                        
                        if result.success:
                            stats.successful_items += 1
                            total_confidence += result.confidence
                            logger.debug(f"Article {article['id']} processed successfully (confidence: {result.confidence:.2f})")
                        else:
                            stats.failed_items += 1
                            logger.error(f"Article {article['id']} processing failed: {result.error}")
                        
                        stats.processed_items += 1
                        stats.total_processing_time_ms += result.processing_time_ms
                        
                        # Rate limiting delay
                        if settings.processing_priority > 1:
                            time.sleep(self.config.rate_limiting.base_delay_seconds)
                        
                    except Exception as e:
                        logger.error(f"Error processing article {article['id']}: {e}")
                        stats.failed_items += 1
                        stats.processed_items += 1
                
                # Progress update
                progress = (stats.processed_items / stats.total_items) * 100
                logger.info(f"Article progress: {stats.processed_items}/{stats.total_items} ({progress:.1f}%)")
                
                # Inter-batch delay
                if batch_num < total_batches:
                    time.sleep(2.0)
            
            # Calculate final statistics
            if stats.successful_items > 0:
                stats.average_confidence = total_confidence / stats.successful_items
            
            stats.end_time = datetime.now()
            
            logger.info(f"Article processing completed: {stats.successful_items}/{stats.total_items} successful")
            logger.info(f"Average confidence: {stats.average_confidence:.2f}")
            logger.info(f"Total processing time: {stats.total_processing_time_ms/1000:.1f}s")
            
            return stats
            
        except Exception as e:
            logger.error(f"Article batch processing failed: {e}")
            stats.end_time = datetime.now()
            return stats
    
    def process_posts(self, limit: Optional[int] = None, force_reprocess: bool = False) -> BatchStats:
        """Process social media posts using configurable parameters."""
        if not self.config.is_content_type_enabled(ContentType.POST):
            logger.warning("Post processing is disabled in configuration")
            return BatchStats(ContentType.POST)
        
        settings = self.config.posts
        logger.info(f"Starting post processing with batch size: {settings.batch_size}")
        
        stats = BatchStats(ContentType.POST)
        stats.start_time = datetime.now()
        
        try:
            # Get posts to process
            posts = self._get_posts_for_processing(
                limit=limit or settings.max_items_per_run,
                force_reprocess=force_reprocess
            )
            
            stats.total_items = len(posts)
            logger.info(f"Found {stats.total_items} posts to process")
            
            if stats.total_items == 0:
                logger.info("No posts to process")
                return stats
            
            # Process in batches
            batch_size = settings.batch_size
            total_confidence = 0.0
            
            for i in range(0, len(posts), batch_size):
                batch = posts[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(posts) + batch_size - 1) // batch_size
                
                logger.info(f"Processing post batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                for post in batch:
                    try:
                        content = post.get('content', '')
                        
                        # Skip if content is too short
                        if len(content) < settings.min_content_length:
                            stats.skipped_items += 1
                            stats.processed_items += 1
                            continue
                        
                        # Process with configurable service
                        result = self.enrichment_service.enrich_content(
                            content_id=post['id'],
                            content_type=ContentType.POST,
                            content=content,
                            force_reprocess=force_reprocess
                        )
                        
                        if result.success:
                            stats.successful_items += 1
                            total_confidence += result.confidence
                            logger.debug(f"Post {post['id']} processed successfully (confidence: {result.confidence:.2f})")
                        else:
                            stats.failed_items += 1
                            logger.error(f"Post {post['id']} processing failed: {result.error}")
                        
                        stats.processed_items += 1
                        stats.total_processing_time_ms += result.processing_time_ms
                        
                        # Rate limiting delay
                        time.sleep(self.config.rate_limiting.base_delay_seconds * 0.5)  # Posts process faster
                        
                    except Exception as e:
                        logger.error(f"Error processing post {post['id']}: {e}")
                        stats.failed_items += 1
                        stats.processed_items += 1
                
                # Progress update
                progress = (stats.processed_items / stats.total_items) * 100
                logger.info(f"Post progress: {stats.processed_items}/{stats.total_items} ({progress:.1f}%)")
            
            # Calculate final statistics
            if stats.successful_items > 0:
                stats.average_confidence = total_confidence / stats.successful_items
            
            stats.end_time = datetime.now()
            
            logger.info(f"Post processing completed: {stats.successful_items}/{stats.total_items} successful")
            logger.info(f"Average confidence: {stats.average_confidence:.2f}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Post batch processing failed: {e}")
            stats.end_time = datetime.now()
            return stats
    
    def process_comments(self, limit: Optional[int] = None, force_reprocess: bool = False) -> BatchStats:
        """Process comments using configurable parameters."""
        if not self.config.is_content_type_enabled(ContentType.COMMENT):
            logger.warning("Comment processing is disabled in configuration")
            return BatchStats(ContentType.COMMENT)
        
        settings = self.config.comments
        logger.info(f"Starting comment processing with batch size: {settings.batch_size}")
        logger.info(f"Processing mode: {settings.processing_mode.value}")
        
        stats = BatchStats(ContentType.COMMENT)
        stats.start_time = datetime.now()
        
        try:
            # Get comments to process
            comments = self._get_comments_for_processing(
                limit=limit or settings.max_items_per_run,
                force_reprocess=force_reprocess
            )
            
            stats.total_items = len(comments)
            logger.info(f"Found {stats.total_items} comments to process")
            
            if stats.total_items == 0:
                logger.info("No comments to process")
                return stats
            
            # Process in batches
            batch_size = settings.batch_size
            total_confidence = 0.0
            
            for i in range(0, len(comments), batch_size):
                batch = comments[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(comments) + batch_size - 1) // batch_size
                
                logger.info(f"Processing comment batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                for comment in batch:
                    try:
                        content = comment.get('content', '')
                        
                        # Skip if content is too short
                        if len(content) < settings.min_content_length:
                            stats.skipped_items += 1
                            stats.processed_items += 1
                            continue
                        
                        # Process with configurable service
                        result = self.enrichment_service.enrich_content(
                            content_id=comment['id'],
                            content_type=ContentType.COMMENT,
                            content=content,
                            force_reprocess=force_reprocess
                        )
                        
                        if result.success:
                            stats.successful_items += 1
                            total_confidence += result.confidence
                            logger.debug(f"Comment {comment['id']} processed successfully (confidence: {result.confidence:.2f})")
                        else:
                            stats.failed_items += 1
                            logger.error(f"Comment {comment['id']} processing failed: {result.error}")
                        
                        stats.processed_items += 1
                        stats.total_processing_time_ms += result.processing_time_ms
                        
                        # Minimal delay for comments (they process quickly)
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing comment {comment['id']}: {e}")
                        stats.failed_items += 1
                        stats.processed_items += 1
                
                # Progress update
                progress = (stats.processed_items / stats.total_items) * 100
                logger.info(f"Comment progress: {stats.processed_items}/{stats.total_items} ({progress:.1f}%)")
            
            # Calculate final statistics
            if stats.successful_items > 0:
                stats.average_confidence = total_confidence / stats.successful_items
            
            stats.end_time = datetime.now()
            
            logger.info(f"Comment processing completed: {stats.successful_items}/{stats.total_items} successful")
            logger.info(f"Average confidence: {stats.average_confidence:.2f}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Comment batch processing failed: {e}")
            stats.end_time = datetime.now()
            return stats
    
    def _get_articles_for_processing(self, limit: int, force_reprocess: bool) -> List[Dict[str, Any]]:
        """Get articles that need processing."""
        try:
            query = self.db_manager.client.table("articles").select("id, title, description, content, sentiment")
            
            if not force_reprocess:
                query = query.is_("sentiment", None)
            
            query = query.limit(limit)
            response = query.execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting articles for processing: {e}")
            return []
    
    def _get_posts_for_processing(self, limit: int, force_reprocess: bool) -> List[Dict[str, Any]]:
        """Get posts that need processing."""
        try:
            query = self.db_manager.client.table("social_media_posts").select("id, content, sentiment_score")
            
            if not force_reprocess:
                query = query.is_("sentiment_score", None)
            
            query = query.limit(limit)
            response = query.execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting posts for processing: {e}")
            return []
    
    def _get_comments_for_processing(self, limit: int, force_reprocess: bool) -> List[Dict[str, Any]]:
        """Get comments that need processing."""
        try:
            query = self.db_manager.client.table("social_media_comments").select("id, content, sentiment_score")
            
            if not force_reprocess:
                query = query.is_("sentiment_score", None)
            
            query = query.limit(limit)
            response = query.execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting comments for processing: {e}")
            return []
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            'config_enabled': self.config.enabled,
            'content_types': {
                'articles': {
                    'enabled': self.config.articles.enabled,
                    'processing_mode': self.config.articles.processing_mode.value,
                    'batch_size': self.config.articles.batch_size
                },
                'posts': {
                    'enabled': self.config.posts.enabled,
                    'processing_mode': self.config.posts.processing_mode.value,
                    'batch_size': self.config.posts.batch_size
                },
                'comments': {
                    'enabled': self.config.comments.enabled,
                    'processing_mode': self.config.comments.processing_mode.value,
                    'batch_size': self.config.comments.batch_size
                }
            },
            'enrichment_service': self.enrichment_service.get_service_status()
        }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Configurable AI Enrichment Batch Processing')
    parser.add_argument('--content-type', choices=['articles', 'posts', 'comments', 'all'], 
                       default='all', help='Content type to process')
    parser.add_argument('--limit', type=int, help='Limit number of items to process')
    parser.add_argument('--force-reprocess', action='store_true', 
                       help='Force reprocessing of already enriched content')
    parser.add_argument('--status', action='store_true', help='Show service status and exit')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = ConfigurableBatchEnrichment()
    
    if args.status:
        status = processor.get_service_status()
        print(f"Service Status: {status}")
        return
    
    # Process content based on arguments
    results = {}
    
    if args.content_type in ['articles', 'all']:
        logger.info("=" * 50)
        logger.info("PROCESSING ARTICLES")
        logger.info("=" * 50)
        results['articles'] = processor.process_articles(args.limit, args.force_reprocess)
    
    if args.content_type in ['posts', 'all']:
        logger.info("=" * 50)
        logger.info("PROCESSING POSTS")
        logger.info("=" * 50)
        results['posts'] = processor.process_posts(args.limit, args.force_reprocess)
    
    if args.content_type in ['comments', 'all']:
        logger.info("=" * 50)
        logger.info("PROCESSING COMMENTS")
        logger.info("=" * 50)
        results['comments'] = processor.process_comments(args.limit, args.force_reprocess)
    
    # Print final summary
    logger.info("=" * 50)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 50)
    
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    for content_type, stats in results.items():
        logger.info(f"{content_type.upper()}:")
        logger.info(f"  Processed: {stats.processed_items}/{stats.total_items}")
        logger.info(f"  Successful: {stats.successful_items}")
        logger.info(f"  Failed: {stats.failed_items}")
        logger.info(f"  Skipped: {stats.skipped_items}")
        logger.info(f"  Average Confidence: {stats.average_confidence:.2f}")
        
        if stats.start_time and stats.end_time:
            duration = (stats.end_time - stats.start_time).total_seconds()
            logger.info(f"  Duration: {duration:.1f}s")
        
        total_processed += stats.processed_items
        total_successful += stats.successful_items
        total_failed += stats.failed_items
    
    success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
    logger.info(f"OVERALL SUCCESS RATE: {success_rate:.1f}% ({total_successful}/{total_processed})")


if __name__ == "__main__":
    main()
