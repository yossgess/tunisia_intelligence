"""
Vector Database Integration for Tunisia Intelligence System.

This module provides pgvector database integration for storing and querying
semantic embeddings with optimized indexing and similarity search.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
import json
import numpy as np

from config.database import DatabaseManager
from .vector_service import VectorResult

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    """Result of vector similarity search."""
    content_id: str
    content_type: str
    similarity_score: float
    content_preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class VectorStats:
    """Statistics about vector storage."""
    total_vectors: int
    by_content_type: Dict[str, int]
    avg_dimensions: float
    storage_size_mb: float

class VectorDatabase:
    """
    Database interface for vector storage and retrieval using pgvector.
    
    Handles vector storage, similarity search, and index management.
    """
    
    def __init__(self):
        """Initialize the vector database interface."""
        self.db_manager = DatabaseManager()
        self.client = self.db_manager.client
        logger.info("VectorDatabase initialized")
    
    def setup_vector_extensions(self) -> bool:
        """
        Set up pgvector extension and create necessary indexes.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Enable pgvector extension
            self.client.rpc('enable_pgvector_extension').execute()
            
            # Create vector indexes for all embedding columns
            vector_indexes = [
                # News articles
                {
                    'table': 'news_articles',
                    'column': 'embedding',
                    'index_name': 'idx_news_articles_embedding_hnsw'
                },
                # Social media posts
                {
                    'table': 'social_media_posts',
                    'column': 'embedding',
                    'index_name': 'idx_social_media_posts_embedding_hnsw'
                },
                # Social media comments
                {
                    'table': 'social_media_comments',
                    'column': 'embedding',
                    'index_name': 'idx_social_media_comments_embedding_hnsw'
                },
                # Entities
                {
                    'table': 'entities',
                    'column': 'embedding',
                    'index_name': 'idx_entities_embedding_hnsw'
                },
                # Reports
                {
                    'table': 'reports',
                    'column': 'embedding',
                    'index_name': 'idx_reports_embedding_hnsw'
                }
            ]
            
            for index_config in vector_indexes:
                try:
                    # Create HNSW index for fast approximate nearest neighbor search
                    self.client.rpc('create_vector_index', {
                        'table_name': index_config['table'],
                        'column_name': index_config['column'],
                        'index_name': index_config['index_name'],
                        'index_type': 'hnsw',
                        'distance_metric': 'cosine'
                    }).execute()
                    
                    logger.info(f"Created vector index: {index_config['index_name']}")
                    
                except Exception as e:
                    # Index might already exist
                    logger.warning(f"Could not create index {index_config['index_name']}: {e}")
            
            logger.info("Vector extensions and indexes setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup vector extensions: {e}")
            return False
    
    def store_vector(
        self,
        vector_result: VectorResult,
        update_existing: bool = True
    ) -> bool:
        """
        Store a vector in the content_embeddings table.
        
        Args:
            vector_result: VectorResult containing vector and metadata
            update_existing: Whether to update existing vectors
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        if not vector_result.vector:
            logger.warning(f"No vector to store for {vector_result.content_id}")
            return False
        
        try:
            # Prepare vector data for content_embeddings table
            vector_data = {
                'content_type': vector_result.content_type,
                'content_id': int(vector_result.content_id),
                'content_embedding': vector_result.vector,
                'embedding_model': 'qwen2.5:7b',
                'embedding_version': '1.0',
                'content_length': len(str(vector_result.content_hash or '')),
                'embedding_quality_score': 1.0,  # Default quality score
                'updated_at': 'now()'
            }
            
            # Check if embedding already exists
            existing = self.client.table("content_embeddings") \
                .select("id") \
                .eq("content_type", vector_result.content_type) \
                .eq("content_id", int(vector_result.content_id)) \
                .limit(1) \
                .execute()
            
            if existing.data and update_existing:
                # Update existing embedding
                response = self.client.table("content_embeddings") \
                    .update(vector_data) \
                    .eq("content_type", vector_result.content_type) \
                    .eq("content_id", int(vector_result.content_id)) \
                    .execute()
            elif not existing.data:
                # Insert new embedding
                response = self.client.table("content_embeddings") \
                    .insert(vector_data) \
                    .execute()
            else:
                # Skip if exists and not updating
                logger.debug(f"Vector already exists for {vector_result.content_type} {vector_result.content_id}")
                return True
            
            if response.data:
                logger.debug(f"Vector stored for {vector_result.content_type} {vector_result.content_id}")
                return True
            else:
                logger.warning(f"Failed to store vector for {vector_result.content_type} {vector_result.content_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing vector for {vector_result.content_id}: {e}")
            return False
    
    def batch_store_vectors(
        self,
        vector_results: List[VectorResult],
        batch_size: int = 50
    ) -> Tuple[int, int]:
        """
        Store multiple vectors in batches.
        
        Args:
            vector_results: List of VectorResult objects
            batch_size: Number of vectors to process per batch
            
        Returns:
            Tuple[int, int]: (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        # Group by content type for efficient batch processing
        by_type = {}
        for result in vector_results:
            if result.vector:  # Only process results with vectors
                content_type = result.content_type
                if content_type not in by_type:
                    by_type[content_type] = []
                by_type[content_type].append(result)
        
        # Process each content type separately
        for content_type, results in by_type.items():
            logger.info(f"Batch storing {len(results)} vectors for {content_type}")
            
            # Process in batches
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                
                for result in batch:
                    if self.store_vector(result):
                        successful += 1
                    else:
                        failed += 1
                
                # Log progress
                if i + batch_size < len(results):
                    logger.debug(f"Processed {i + batch_size}/{len(results)} {content_type} vectors")
        
        logger.info(f"Batch vector storage completed: {successful} successful, {failed} failed")
        return successful, failed
    
    def similarity_search(
        self,
        query_vector: List[float],
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        include_content: bool = False
    ) -> List[VectorSearchResult]:
        """
        Perform similarity search across vector-enabled tables.
        
        Args:
            query_vector: Vector to search for similar content
            content_types: List of content types to search in (None for all)
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            include_content: Whether to include content preview in results
            
        Returns:
            List of VectorSearchResult objects
        """
        if not query_vector:
            return []
        
        # Default to all content types if none specified
        if content_types is None:
            content_types = ['article', 'social_post', 'comment', 'entity', 'report']
        
        all_results = []
        
        # Search in each content type
        for content_type in content_types:
            try:
                results = self._search_in_table(
                    query_vector=query_vector,
                    content_type=content_type,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                    include_content=include_content
                )
                all_results.extend(results)
                
            except Exception as e:
                logger.error(f"Error searching in {content_type}: {e}")
        
        # Sort by similarity score (descending) and limit results
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return all_results[:limit]
    
    def _search_in_table(
        self,
        query_vector: List[float],
        content_type: str,
        limit: int,
        similarity_threshold: float,
        include_content: bool
    ) -> List[VectorSearchResult]:
        """Search for similar vectors in a specific table."""
        # Map content type to table
        table_mapping = {
            'article': 'news_articles',
            'social_post': 'social_media_posts',
            'comment': 'social_media_comments',
            'entity': 'entities',
            'report': 'reports'
        }
        
        table_name = table_mapping.get(content_type)
        if not table_name:
            return []
        
        try:
            # Use RPC function for vector similarity search
            response = self.client.rpc('vector_similarity_search', {
                'content_type_filter': content_type,
                'query_vector': query_vector,
                'similarity_threshold': similarity_threshold,
                'result_limit': limit,
                'include_content': include_content
            }).execute()
            
            results = []
            for row in response.data:
                result = VectorSearchResult(
                    content_id=str(row['id']),
                    content_type=content_type,
                    similarity_score=float(row['similarity_score']),
                    content_preview=row.get('content_preview') if include_content else None,
                    metadata={
                        'title': row.get('title'),
                        'created_at': row.get('created_at'),
                        'source_id': row.get('source_id')
                    }
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in table search for {table_name}: {e}")
            return []
    
    def find_similar_content(
        self,
        content_id: str,
        content_type: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[VectorSearchResult]:
        """
        Find content similar to a specific item.
        
        Args:
            content_id: ID of the content to find similar items for
            content_type: Type of the source content
            limit: Maximum number of similar items to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar content items
        """
        # First, get the vector for the source content
        source_vector = self._get_content_vector(content_id, content_type)
        if not source_vector:
            logger.warning(f"No vector found for {content_type} {content_id}")
            return []
        
        # Search for similar content
        results = self.similarity_search(
            query_vector=source_vector,
            content_types=None,  # Search all types
            limit=limit + 1,  # +1 to account for the source item itself
            similarity_threshold=similarity_threshold,
            include_content=True
        )
        
        # Filter out the source item itself
        filtered_results = [
            r for r in results 
            if not (r.content_id == content_id and r.content_type == content_type)
        ]
        
        return filtered_results[:limit]
    
    def _get_content_vector(self, content_id: str, content_type: str) -> Optional[List[float]]:
        """Get the vector for a specific content item."""
        table_mapping = {
            'article': 'news_articles',
            'social_post': 'social_media_posts',
            'comment': 'social_media_comments',
            'entity': 'entities',
            'report': 'reports'
        }
        
        table_name = table_mapping.get(content_type)
        if not table_name:
            return None
        
        try:
            response = self.client.table(table_name) \
                .select('embedding') \
                .eq('id', content_id) \
                .limit(1) \
                .execute()
            
            if response.data and response.data[0].get('embedding'):
                return response.data[0]['embedding']
            
        except Exception as e:
            logger.error(f"Error getting vector for {content_type} {content_id}: {e}")
        
        return None
    
    def get_vector_stats(self) -> VectorStats:
        """Get statistics about stored vectors."""
        try:
            # Use RPC function to get comprehensive vector statistics
            response = self.client.rpc('get_vector_statistics').execute()
            
            if response.data:
                stats_data = response.data[0]
                return VectorStats(
                    total_vectors=stats_data.get('total_vectors', 0),
                    by_content_type=stats_data.get('by_content_type', {}),
                    avg_dimensions=stats_data.get('avg_dimensions', 0.0),
                    storage_size_mb=stats_data.get('storage_size_mb', 0.0)
                )
            
        except Exception as e:
            logger.error(f"Error getting vector statistics: {e}")
        
        # Return empty stats if error
        return VectorStats(
            total_vectors=0,
            by_content_type={},
            avg_dimensions=0.0,
            storage_size_mb=0.0
        )
    
    def delete_vectors(
        self,
        content_ids: List[str],
        content_type: str
    ) -> int:
        """
        Delete vectors for specific content items.
        
        Args:
            content_ids: List of content IDs to delete vectors for
            content_type: Type of content
            
        Returns:
            int: Number of vectors deleted
        """
        table_mapping = {
            'article': 'news_articles',
            'social_post': 'social_media_posts',
            'comment': 'social_media_comments',
            'entity': 'entities',
            'report': 'reports'
        }
        
        table_name = table_mapping.get(content_type)
        if not table_name:
            logger.error(f"Unknown content type: {content_type}")
            return 0
        
        try:
            # Set embedding to NULL for specified content
            response = self.client.table(table_name) \
                .update({'embedding': None, 'content_hash': None}) \
                .in_('id', content_ids) \
                .execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Deleted {deleted_count} vectors for {content_type}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting vectors for {content_type}: {e}")
            return 0
    
    def rebuild_indexes(self) -> bool:
        """
        Rebuild vector indexes for better performance.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use RPC function to rebuild all vector indexes
            self.client.rpc('rebuild_vector_indexes').execute()
            logger.info("Vector indexes rebuilt successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding vector indexes: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector database.
        
        Returns:
            Dict with health status and metrics
        """
        health_status = {
            'status': 'healthy',
            'pgvector_enabled': False,
            'indexes_exist': False,
            'total_vectors': 0,
            'errors': []
        }
        
        try:
            # Check if pgvector extension is enabled
            response = self.client.rpc('check_pgvector_extension').execute()
            health_status['pgvector_enabled'] = response.data[0].get('enabled', False) if response.data else False
            
            # Check if indexes exist
            response = self.client.rpc('check_vector_indexes').execute()
            health_status['indexes_exist'] = response.data[0].get('all_exist', False) if response.data else False
            
            # Get vector count
            stats = self.get_vector_stats()
            health_status['total_vectors'] = stats.total_vectors
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['errors'].append(str(e))
            logger.error(f"Vector database health check failed: {e}")
        
        return health_status
