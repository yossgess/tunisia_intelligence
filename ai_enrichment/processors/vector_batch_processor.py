"""
Vector Batch Processor for Tunisia Intelligence System.

This module provides batch processing capabilities for generating and storing
vectors for existing content in the database.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

from ..core.vector_service import VectorService, VectorConfig, VectorResult
from ..core.vector_database import VectorDatabase, VectorStats
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class BatchProcessingConfig:
    """Configuration for batch vector processing."""
    batch_size: int = 20
    max_workers: int = 4
    content_types: List[str] = None
    force_regenerate: bool = False
    skip_existing: bool = True
    min_content_length: int = 50
    max_items_per_run: Optional[int] = None
    processing_delay: float = 0.5  # Delay between batches in seconds
    
    def __post_init__(self):
        if self.content_types is None:
            self.content_types = ['article', 'social_post']  # Remove comment and entity for now

@dataclass
class BatchProcessingStats:
    """Statistics for batch processing run."""
    total_items: int = 0
    processed_items: int = 0
    successful_vectors: int = 0
    failed_vectors: int = 0
    skipped_items: int = 0
    processing_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class VectorBatchProcessor:
    """
    Batch processor for generating vectors for existing content.
    
    Handles large-scale vector generation with progress tracking,
    error handling, and performance optimization.
    """
    
    def __init__(
        self,
        config: Optional[BatchProcessingConfig] = None,
        vector_config: Optional[VectorConfig] = None
    ):
        """Initialize the batch processor."""
        self.config = config or BatchProcessingConfig()
        self.db_manager = DatabaseManager()
        self.vector_service = VectorService(vector_config)
        self.vector_db = VectorDatabase()
        
        logger.info(f"VectorBatchProcessor initialized with batch_size={self.config.batch_size}")
    
    def process_all_content(self) -> BatchProcessingStats:
        """
        Process all content types in the database.
        
        Returns:
            BatchProcessingStats: Statistics for the processing run
        """
        logger.info("Starting batch vector processing for all content types")
        
        stats = BatchProcessingStats(start_time=datetime.now())
        
        try:
            # Process each content type
            for content_type in self.config.content_types:
                logger.info(f"Processing {content_type} content...")
                
                type_stats = self._process_content_type(content_type)
                
                # Aggregate stats
                stats.total_items += type_stats.total_items
                stats.processed_items += type_stats.processed_items
                stats.successful_vectors += type_stats.successful_vectors
                stats.failed_vectors += type_stats.failed_vectors
                stats.skipped_items += type_stats.skipped_items
                stats.errors.extend(type_stats.errors)
                
                logger.info(f"Completed {content_type}: {type_stats.successful_vectors}/{type_stats.total_items} successful")
        
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
        
        finally:
            stats.end_time = datetime.now()
            stats.processing_time = (stats.end_time - stats.start_time).total_seconds()
            
            logger.info(f"Batch processing completed: {stats.successful_vectors}/{stats.total_items} successful in {stats.processing_time:.2f}s")
        
        return stats
    
    def _process_content_type(self, content_type: str) -> BatchProcessingStats:
        """Process a specific content type."""
        stats = BatchProcessingStats()
        
        try:
            # Get content items to process
            content_items = self._get_content_items(content_type)
            stats.total_items = len(content_items)
            
            if not content_items:
                logger.info(f"No {content_type} items to process")
                return stats
            
            logger.info(f"Found {len(content_items)} {content_type} items to process")
            
            # Apply max items limit if specified
            if self.config.max_items_per_run:
                content_items = content_items[:self.config.max_items_per_run]
                logger.info(f"Limited to {len(content_items)} items per max_items_per_run setting")
            
            # Process in batches
            for i in range(0, len(content_items), self.config.batch_size):
                batch = content_items[i:i + self.config.batch_size]
                batch_stats = self._process_batch(batch, content_type)
                
                # Aggregate batch stats
                stats.processed_items += batch_stats.processed_items
                stats.successful_vectors += batch_stats.successful_vectors
                stats.failed_vectors += batch_stats.failed_vectors
                stats.skipped_items += batch_stats.skipped_items
                stats.errors.extend(batch_stats.errors)
                
                # Log progress
                progress = min(i + self.config.batch_size, len(content_items))
                logger.info(f"Progress: {progress}/{len(content_items)} {content_type} items processed")
                
                # Delay between batches
                if i + self.config.batch_size < len(content_items):
                    time.sleep(self.config.processing_delay)
        
        except Exception as e:
            error_msg = f"Error processing {content_type}: {str(e)}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
        
        return stats
    
    def _get_content_items(self, content_type: str) -> List[Dict[str, Any]]:
        """Get content items to process for a specific type."""
        try:
            if content_type == 'article':
                return self._get_articles()
            elif content_type == 'social_post':
                return self._get_social_posts()
            elif content_type == 'comment':
                return self._get_social_comments()
            elif content_type == 'entity':
                return self._get_entities()
            else:
                logger.error(f"Unknown content type: {content_type}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting {content_type} items: {e}")
            return []
    
    def _get_articles(self) -> List[Dict[str, Any]]:
        """Get articles that need vectorization."""
        if self.config.skip_existing:
            # Get articles that don't have embeddings yet by checking content_embeddings table
            response = self.db_manager.client.table("articles").select(
                "id, title, description, content, created_at"
            ).execute()
            
            # Filter out articles that already have embeddings
            if response.data:
                article_ids = [str(article['id']) for article in response.data]
                existing_embeddings = self.db_manager.client.table("content_embeddings").select(
                    "content_id"
                ).eq("content_type", "article").in_("content_id", article_ids).execute()
                
                existing_ids = {str(emb['content_id']) for emb in existing_embeddings.data}
                response.data = [article for article in response.data if str(article['id']) not in existing_ids]
        else:
            # Get all articles
            response = self.db_manager.client.table("articles").select(
                "id, title, description, content, created_at"
            ).order("created_at", desc=True).execute()
        
        articles = []
        for article in response.data:
            # Combine title, description, and content
            content_parts = []
            if article.get('title'):
                content_parts.append(article['title'])
            if article.get('description'):
                content_parts.append(article['description'])
            if article.get('content'):
                content_parts.append(article['content'])
            
            full_content = ' '.join(content_parts)
            
            if len(full_content) >= self.config.min_content_length:
                articles.append({
                    'id': article['id'],
                    'type': 'article',
                    'content': full_content,
                    'metadata': {
                        'title': article.get('title'),
                        'created_at': article.get('created_at')
                    }
                })
        
        return articles
    
    def _get_social_posts(self) -> List[Dict[str, Any]]:
        """Get social media posts that need vectorization."""
        if self.config.skip_existing:
            # Get posts that don't have embeddings yet
            response = self.db_manager.client.table("social_media_posts").select(
                "id, content, publish_date, source_id"
            ).execute()
            
            # Filter out posts that already have embeddings
            if response.data:
                post_ids = [str(post['id']) for post in response.data]
                existing_embeddings = self.db_manager.client.table("content_embeddings").select(
                    "content_id"
                ).eq("content_type", "post").in_("content_id", post_ids).execute()
                
                existing_ids = {str(emb['content_id']) for emb in existing_embeddings.data}
                response.data = [post for post in response.data if str(post['id']) not in existing_ids]
        else:
            response = self.db_manager.client.table("social_media_posts").select(
                "id, content, publish_date, source_id"
            ).order("publish_date", desc=True).execute()
        
        posts = []
        for post in response.data:
            content = post.get('content', '')
            
            if len(content) >= self.config.min_content_length:
                posts.append({
                    'id': post['id'],
                    'type': 'social_post',
                    'content': content,
                    'metadata': {
                        'publish_date': post.get('publish_date'),
                        'source_id': post.get('source_id')
                    }
                })
        
        return posts
    
    def _get_social_comments(self) -> List[Dict[str, Any]]:
        """Get social media comments that need vectorization."""
        if self.config.skip_existing:
            # Get comments that don't have embeddings yet
            response = self.db_manager.client.table("social_media_comments").select(
                "id, content, comment_date, post_id"
            ).execute()
            
            # Filter out comments that already have embeddings
            if response.data:
                comment_ids = [str(comment['id']) for comment in response.data]
                existing_embeddings = self.db_manager.client.table("content_embeddings").select(
                    "content_id"
                ).eq("content_type", "comment").in_("content_id", comment_ids).execute()
                
                existing_ids = {str(emb['content_id']) for emb in existing_embeddings.data}
                response.data = [comment for comment in response.data if str(comment['id']) not in existing_ids]
        else:
            response = self.db_manager.client.table("social_media_comments").select(
                "id, content, comment_date, post_id"
            ).order("comment_date", desc=True).execute()
        
        comments = []
        for comment in response.data:
            content = comment.get('content', '')
            
            if len(content) >= self.config.min_content_length:
                comments.append({
                    'id': comment['id'],
                    'type': 'comment',
                    'content': content,
                    'metadata': {
                        'comment_date': comment.get('comment_date'),
                        'post_id': comment.get('post_id')
                    }
                })
        
        return comments
    
    def _get_entities(self) -> List[Dict[str, Any]]:
        """Get entities that need vectorization."""
        if self.config.skip_existing:
            # Get entities that don't have embeddings yet
            response = self.db_manager.client.table("entities").select(
                "id, canonical_name, entity_type_id"
            ).execute()
            
            # Filter out entities that already have embeddings
            if response.data:
                entity_ids = [str(entity['id']) for entity in response.data]
                existing_embeddings = self.db_manager.client.table("content_embeddings").select(
                    "content_id"
                ).eq("content_type", "entity").in_("content_id", entity_ids).execute()
                
                existing_ids = {str(emb['content_id']) for emb in existing_embeddings.data}
                response.data = [entity for entity in response.data if str(entity['id']) not in existing_ids]
        else:
            response = self.db_manager.client.table("entities").select(
                "id, canonical_name, entity_type_id"
            ).execute()
        
        entities = []
        for entity in response.data:
            # Use canonical_name as the main content
            content_parts = []
            if entity.get('canonical_name'):
                content_parts.append(entity['canonical_name'])
            
            full_content = ' '.join(content_parts)
            
            if len(full_content) >= self.config.min_content_length:
                entities.append({
                    'id': entity['id'],
                    'type': 'entity',
                    'content': full_content,
                    'metadata': {
                        'canonical_name': entity.get('canonical_name'),
                        'entity_type_id': entity.get('entity_type_id')
                    }
                })
        
        return entities
    
    
    def _process_batch(self, batch: List[Dict[str, Any]], content_type: str) -> BatchProcessingStats:
        """Process a batch of content items."""
        stats = BatchProcessingStats()
        
        try:
            # Generate vectors for the batch
            vector_results = self.vector_service.batch_generate_vectors(
                content_items=batch,
                force_regenerate=self.config.force_regenerate
            )
            
            # Store vectors in database
            successful_count, failed_count = self.vector_db.batch_store_vectors(vector_results)
            
            stats.processed_items = len(batch)
            stats.successful_vectors = successful_count
            stats.failed_vectors = failed_count
            
            # Log any errors
            for result in vector_results:
                if result.error:
                    stats.errors.append(f"{content_type} {result.content_id}: {result.error}")
        
        except Exception as e:
            error_msg = f"Batch processing error for {content_type}: {str(e)}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            stats.failed_vectors = len(batch)
        
        return stats
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics."""
        try:
            # Get vector statistics
            vector_stats = self.vector_db.get_vector_stats()
            
            # Get content counts by type
            content_counts = {}
            
            for content_type in ['article', 'social_post', 'comment', 'entity', 'report']:
                try:
                    items = self._get_content_items(content_type)
                    content_counts[content_type] = {
                        'total_items': len(items),
                        'needs_vectorization': len(items) if self.config.skip_existing else 0
                    }
                except Exception as e:
                    logger.error(f"Error getting count for {content_type}: {e}")
                    content_counts[content_type] = {'total_items': 0, 'needs_vectorization': 0}
            
            return {
                'vector_stats': {
                    'total_vectors': vector_stats.total_vectors,
                    'by_content_type': vector_stats.by_content_type,
                    'avg_dimensions': vector_stats.avg_dimensions,
                    'storage_size_mb': vector_stats.storage_size_mb
                },
                'content_counts': content_counts,
                'service_health': {
                    'vector_service': self.vector_service.health_check(),
                    'vector_database': self.vector_db.health_check()
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {
                'error': str(e),
                'vector_stats': {'total_vectors': 0},
                'content_counts': {},
                'service_health': {'vector_service': False, 'vector_database': {'status': 'unhealthy'}}
            }
    
    def process_recent_content(self, hours: int = 24) -> BatchProcessingStats:
        """
        Process only recent content (useful for incremental updates).
        
        Args:
            hours: Number of hours back to consider as "recent"
            
        Returns:
            BatchProcessingStats: Processing statistics
        """
        logger.info(f"Processing content from the last {hours} hours")
        
        # Temporarily modify config to process recent content
        original_skip_existing = self.config.skip_existing
        self.config.skip_existing = False  # Process even if vectors exist (for updates)
        
        try:
            stats = BatchProcessingStats(start_time=datetime.now())
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Process each content type with time filter
            for content_type in self.config.content_types:
                type_stats = self._process_recent_content_type(content_type, cutoff_time)
                
                # Aggregate stats
                stats.total_items += type_stats.total_items
                stats.processed_items += type_stats.processed_items
                stats.successful_vectors += type_stats.successful_vectors
                stats.failed_vectors += type_stats.failed_vectors
                stats.skipped_items += type_stats.skipped_items
                stats.errors.extend(type_stats.errors)
            
            stats.end_time = datetime.now()
            stats.processing_time = (stats.end_time - stats.start_time).total_seconds()
            
            logger.info(f"Recent content processing completed: {stats.successful_vectors}/{stats.total_items} successful")
            
        finally:
            # Restore original config
            self.config.skip_existing = original_skip_existing
        
        return stats
    
    def _process_recent_content_type(self, content_type: str, cutoff_time: datetime) -> BatchProcessingStats:
        """Process recent content for a specific type."""
        stats = BatchProcessingStats()
        
        try:
            # Get recent content items
            if content_type == 'article':
                query = self.db_manager.client.table("news_articles").select(
                    "id, title, description, content, created_at"
                ).gte("created_at", cutoff_time.isoformat())
            elif content_type == 'social_post':
                query = self.db_manager.client.table("social_media_posts").select(
                    "id, content, publish_date, source_id"
                ).gte("publish_date", cutoff_time.isoformat())
            elif content_type == 'comment':
                query = self.db_manager.client.table("social_media_comments").select(
                    "id, content, created_time, post_id"
                ).gte("created_time", cutoff_time.isoformat())
            else:
                return stats  # Skip entities and reports for recent processing
            
            response = query.execute()
            
            # Convert to processing format
            content_items = []
            for item in response.data:
                if content_type == 'article':
                    content_parts = [item.get('title', ''), item.get('description', ''), item.get('content', '')]
                    full_content = ' '.join(filter(None, content_parts))
                else:
                    full_content = item.get('content', '')
                
                if len(full_content) >= self.config.min_content_length:
                    content_items.append({
                        'id': item['id'],
                        'type': content_type,
                        'content': full_content
                    })
            
            stats.total_items = len(content_items)
            
            if content_items:
                # Process the items
                type_stats = self._process_content_items(content_items, content_type)
                stats.processed_items = type_stats.processed_items
                stats.successful_vectors = type_stats.successful_vectors
                stats.failed_vectors = type_stats.failed_vectors
                stats.errors = type_stats.errors
        
        except Exception as e:
            error_msg = f"Error processing recent {content_type}: {str(e)}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
        
        return stats
    
    def _process_content_items(self, content_items: List[Dict[str, Any]], content_type: str) -> BatchProcessingStats:
        """Process a list of content items."""
        stats = BatchProcessingStats()
        
        # Process in batches
        for i in range(0, len(content_items), self.config.batch_size):
            batch = content_items[i:i + self.config.batch_size]
            batch_stats = self._process_batch(batch, content_type)
            
            # Aggregate stats
            stats.processed_items += batch_stats.processed_items
            stats.successful_vectors += batch_stats.successful_vectors
            stats.failed_vectors += batch_stats.failed_vectors
            stats.errors.extend(batch_stats.errors)
        
        return stats
