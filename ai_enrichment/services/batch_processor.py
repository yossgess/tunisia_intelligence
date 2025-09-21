"""
Batch Processing Service for AI Enrichment.

This module provides batch processing capabilities for enriching large amounts
of existing content in the database.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .enrichment_service import EnrichmentService
from ..models.enrichment_models import (
    BatchProcessingResult, EnrichmentResult, ProcessingStatus
)

# Import existing database components
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Service for batch processing AI enrichment on existing content.
    
    Handles large-scale enrichment operations with progress tracking,
    error handling, and resumability.
    """
    
    def __init__(
        self,
        enrichment_service: Optional[EnrichmentService] = None,
        db_manager: Optional[DatabaseManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the batch processor.
        
        Args:
            enrichment_service: Enrichment service instance
            db_manager: Database manager instance
            config: Batch processing configuration
        """
        self.enrichment_service = enrichment_service or EnrichmentService()
        self.db_manager = db_manager or DatabaseManager()
        
        # Default configuration
        self.default_config = {
            'batch_size': 50,  # Process items in batches
            'max_workers': 4,  # Parallel processing workers
            'delay_between_batches': 1.0,  # Seconds to wait between batches
            'save_progress': True,  # Save progress to resume later
            'skip_existing': True,  # Skip already enriched content
            'max_retries': 2,  # Retry failed items
            'timeout_per_item': 60,  # Timeout per item in seconds
            'log_interval': 10  # Log progress every N items
        }
        
        self.config = {**self.default_config, **(config or {})}
        
        # Progress tracking
        self.current_batch_id = None
        self.progress_file = "batch_processing_progress.json"
    
    def process_articles(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        source_ids: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> BatchProcessingResult:
        """
        Process articles from the database with AI enrichment.
        
        Args:
            limit: Maximum number of articles to process
            offset: Starting offset for articles
            source_ids: Filter by specific source IDs
            date_from: Process articles from this date
            date_to: Process articles until this date
            force_reprocess: Reprocess already enriched articles
            
        Returns:
            BatchProcessingResult with processing statistics
        """
        logger.info("Starting batch processing of articles")
        start_time = datetime.now()
        
        try:
            # Get articles to process
            articles = self._get_articles_to_process(
                limit=limit,
                offset=offset,
                source_ids=source_ids,
                date_from=date_from,
                date_to=date_to,
                force_reprocess=force_reprocess
            )
            
            if not articles:
                logger.info("No articles found to process")
                return BatchProcessingResult(
                    total_items=0,
                    processed_items=0,
                    successful_items=0,
                    failed_items=0,
                    skipped_items=0,
                    success_rate=0.0,
                    average_confidence=0.0,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    total_processing_time=0.0
                )
            
            logger.info(f"Found {len(articles)} articles to process")
            
            # Process articles in batches
            results = self._process_content_batch(
                content_items=articles,
                content_type="article"
            )
            
            # Calculate final statistics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            successful_results = [r for r in results if r.status == ProcessingStatus.SUCCESS]
            failed_results = [r for r in results if r.status == ProcessingStatus.FAILED]
            
            avg_confidence = (
                sum(r.confidence for r in successful_results) / len(successful_results)
                if successful_results else 0.0
            )
            
            batch_result = BatchProcessingResult(
                total_items=len(articles),
                processed_items=len(results),
                successful_items=len(successful_results),
                failed_items=len(failed_results),
                skipped_items=len(articles) - len(results),
                success_rate=len(successful_results) / len(results) if results else 0.0,
                average_confidence=avg_confidence,
                started_at=start_time,
                completed_at=end_time,
                total_processing_time=total_time,
                sentiment_results=sum(1 for r in successful_results if r.sentiment),
                entity_results=sum(1 for r in successful_results if r.entities),
                keyword_results=sum(1 for r in successful_results if r.keywords),
                category_results=sum(1 for r in successful_results if r.category)
            )
            
            logger.info(f"Batch processing completed: {batch_result.success_rate:.2%} success rate")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return BatchProcessingResult(
                total_items=0,
                processed_items=0,
                successful_items=0,
                failed_items=1,
                skipped_items=0,
                success_rate=0.0,
                average_confidence=0.0,
                started_at=start_time,
                completed_at=end_time,
                total_processing_time=total_time,
                error_summary={"batch_error": 1}
            )
    
    def process_social_media_posts(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        account_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> BatchProcessingResult:
        """
        Process social media posts from the database with AI enrichment.
        
        Args:
            limit: Maximum number of posts to process
            offset: Starting offset for posts
            account_filter: Filter by specific account
            date_from: Process posts from this date
            date_to: Process posts until this date
            force_reprocess: Reprocess already enriched posts
            
        Returns:
            BatchProcessingResult with processing statistics
        """
        logger.info("Starting batch processing of social media posts")
        start_time = datetime.now()
        
        try:
            # Get posts to process
            posts = self._get_social_media_posts_to_process(
                limit=limit,
                offset=offset,
                account_filter=account_filter,
                date_from=date_from,
                date_to=date_to,
                force_reprocess=force_reprocess
            )
            
            if not posts:
                logger.info("No social media posts found to process")
                return BatchProcessingResult(
                    total_items=0,
                    processed_items=0,
                    successful_items=0,
                    failed_items=0,
                    skipped_items=0,
                    success_rate=0.0,
                    average_confidence=0.0,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    total_processing_time=0.0
                )
            
            logger.info(f"Found {len(posts)} social media posts to process")
            
            # Process posts in batches
            results = self._process_content_batch(
                content_items=posts,
                content_type="social_media_post"
            )
            
            # Calculate final statistics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            successful_results = [r for r in results if r.status == ProcessingStatus.SUCCESS]
            failed_results = [r for r in results if r.status == ProcessingStatus.FAILED]
            
            avg_confidence = (
                sum(r.confidence for r in successful_results) / len(successful_results)
                if successful_results else 0.0
            )
            
            return BatchProcessingResult(
                total_items=len(posts),
                processed_items=len(results),
                successful_items=len(successful_results),
                failed_items=len(failed_results),
                skipped_items=len(posts) - len(results),
                success_rate=len(successful_results) / len(results) if results else 0.0,
                average_confidence=avg_confidence,
                started_at=start_time,
                completed_at=end_time,
                total_processing_time=total_time,
                sentiment_results=sum(1 for r in successful_results if r.sentiment),
                entity_results=sum(1 for r in successful_results if r.entities),
                keyword_results=sum(1 for r in successful_results if r.keywords),
                category_results=sum(1 for r in successful_results if r.category)
            )
            
        except Exception as e:
            logger.error(f"Social media batch processing failed: {e}")
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return BatchProcessingResult(
                total_items=0,
                processed_items=0,
                successful_items=0,
                failed_items=1,
                skipped_items=0,
                success_rate=0.0,
                average_confidence=0.0,
                started_at=start_time,
                completed_at=end_time,
                total_processing_time=total_time,
                error_summary={"batch_error": 1}
            )
    
    def _get_articles_to_process(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        source_ids: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> List[Dict[str, Any]]:
        """Get articles from database that need processing."""
        try:
            query = self.db_manager.client.table("articles").select("*")
            
            # Apply filters
            if source_ids:
                query = query.in_("source_id", source_ids)
            
            if date_from:
                query = query.gte("pub_date", date_from.isoformat())
            
            if date_to:
                query = query.lte("pub_date", date_to.isoformat())
            
            # Skip already enriched articles unless force reprocessing
            if not force_reprocess:
                query = query.is_("sentiment", "null")
            
            # Apply pagination
            if offset > 0:
                query = query.range(offset, offset + (limit or 1000) - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to fetch articles: {e}")
            return []
    
    def _get_social_media_posts_to_process(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        account_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> List[Dict[str, Any]]:
        """Get social media posts from database that need processing."""
        try:
            query = self.db_manager.client.table("social_media_posts").select("*")
            
            # Apply filters
            if account_filter:
                query = query.eq("account", account_filter)
            
            if date_from:
                query = query.gte("publish_date", date_from.isoformat())
            
            if date_to:
                query = query.lte("publish_date", date_to.isoformat())
            
            # Skip already enriched posts unless force reprocessing
            if not force_reprocess:
                query = query.is_("sentiment_score", "null")
            
            # Apply pagination
            if offset > 0:
                query = query.range(offset, offset + (limit or 1000) - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to fetch social media posts: {e}")
            return []
    
    def _process_content_batch(
        self,
        content_items: List[Dict[str, Any]],
        content_type: str
    ) -> List[EnrichmentResult]:
        """
        Process a batch of content items with AI enrichment.
        
        Args:
            content_items: List of content items from database
            content_type: Type of content being processed
            
        Returns:
            List of EnrichmentResult objects
        """
        results = []
        total_items = len(content_items)
        
        # Process in smaller batches
        for batch_start in range(0, total_items, self.config['batch_size']):
            batch_end = min(batch_start + self.config['batch_size'], total_items)
            batch_items = content_items[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//self.config['batch_size'] + 1}: items {batch_start+1}-{batch_end}")
            
            # Process batch items in parallel
            batch_results = self._process_batch_parallel(batch_items, content_type)
            results.extend(batch_results)
            
            # Log progress
            if batch_end % self.config['log_interval'] == 0 or batch_end == total_items:
                successful = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
                logger.info(f"Progress: {batch_end}/{total_items} processed, {successful} successful")
            
            # Delay between batches to avoid overwhelming the system
            if batch_end < total_items:
                time.sleep(self.config['delay_between_batches'])
        
        return results
    
    def _process_batch_parallel(
        self,
        batch_items: List[Dict[str, Any]],
        content_type: str
    ) -> List[EnrichmentResult]:
        """Process a batch of items in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            # Submit all items in the batch
            future_to_item = {}
            for item in batch_items:
                content = self._extract_content_from_item(item, content_type)
                if content:
                    future = executor.submit(
                        self.enrichment_service.enrich_content,
                        content,
                        content_type,
                        item.get('id')
                    )
                    future_to_item[future] = item
            
            # Collect results
            for future in as_completed(future_to_item, timeout=self.config['timeout_per_item'] * len(batch_items)):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process item {item.get('id')}: {e}")
                    # Create failed result
                    failed_result = EnrichmentResult(
                        content_id=item.get('id'),
                        content_type=content_type,
                        status=ProcessingStatus.FAILED,
                        confidence=0.0,
                        error_message=str(e)
                    )
                    results.append(failed_result)
        
        return results
    
    def _extract_content_from_item(self, item: Dict[str, Any], content_type: str) -> Optional[str]:
        """Extract text content from database item."""
        if content_type == "article":
            # Try content first, then description, then title
            content = item.get('content') or item.get('description') or item.get('title', '')
        elif content_type == "social_media_post":
            content = item.get('content', '')
        elif content_type == "comment":
            content = item.get('content', '')
        else:
            content = str(item)
        
        return content.strip() if content else None
    
    def save_progress(self, progress_data: Dict[str, Any]) -> None:
        """Save batch processing progress to file."""
        if not self.config['save_progress']:
            return
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Progress saved to {self.progress_file}")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def load_progress(self) -> Optional[Dict[str, Any]]:
        """Load batch processing progress from file."""
        if not self.config['save_progress']:
            return None
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            logger.info(f"Progress loaded from {self.progress_file}")
            return progress_data
        except FileNotFoundError:
            logger.info("No previous progress file found")
            return None
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return None
    
    def get_processing_statistics(
        self,
        content_type: str = "article",
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get statistics about content that needs processing.
        
        Args:
            content_type: Type of content to analyze
            days_back: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        try:
            if content_type == "article":
                table_name = "articles"
                date_field = "pub_date"
                enriched_field = "sentiment"
            elif content_type == "social_media_post":
                table_name = "social_media_posts"
                date_field = "publish_date"
                enriched_field = "sentiment_score"
            else:
                return {"error": f"Unsupported content type: {content_type}"}
            
            # Get total count
            total_response = self.db_manager.client.table(table_name) \
                .select("id", count="exact") \
                .execute()
            total_count = total_response.count or 0
            
            # Get enriched count
            enriched_response = self.db_manager.client.table(table_name) \
                .select("id", count="exact") \
                .not_.is_(enriched_field, "null") \
                .execute()
            enriched_count = enriched_response.count or 0
            
            # Get recent content count
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=days_back)
            recent_response = self.db_manager.client.table(table_name) \
                .select("id", count="exact") \
                .gte(date_field, recent_date.isoformat()) \
                .execute()
            recent_count = recent_response.count or 0
            
            # Get recent enriched count
            recent_enriched_response = self.db_manager.client.table(table_name) \
                .select("id", count="exact") \
                .gte(date_field, recent_date.isoformat()) \
                .not_.is_(enriched_field, "null") \
                .execute()
            recent_enriched_count = recent_enriched_response.count or 0
            
            return {
                "content_type": content_type,
                "total_items": total_count,
                "enriched_items": enriched_count,
                "pending_items": total_count - enriched_count,
                "enrichment_rate": (enriched_count / total_count * 100) if total_count > 0 else 0,
                "recent_items": recent_count,
                "recent_enriched": recent_enriched_count,
                "recent_pending": recent_count - recent_enriched_count,
                "days_analyzed": days_back
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing statistics: {e}")
            return {"error": str(e)}
