"""
Vector Management CLI for Tunisia Intelligence System.

Command-line interface for managing vector generation, storage, and analysis.
"""

import argparse
import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

from ..core.vector_service import VectorService, VectorConfig
from ..core.vector_database import VectorDatabase
from ..processors.vector_batch_processor import VectorBatchProcessor, BatchProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorCLI:
    """Command-line interface for vector operations."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.vector_service = None
        self.vector_db = None
        self.batch_processor = None
    
    def _init_services(self):
        """Initialize services if not already done."""
        if not self.vector_service:
            self.vector_service = VectorService()
        if not self.vector_db:
            self.vector_db = VectorDatabase()
        if not self.batch_processor:
            self.batch_processor = VectorBatchProcessor()
    
    def setup_database(self, args) -> int:
        """Set up pgvector extensions and indexes."""
        try:
            self._init_services()
            
            print("Setting up pgvector extensions and indexes...")
            success = self.vector_db.setup_vector_extensions()
            
            if success:
                print("✅ Vector database setup completed successfully")
                return 0
            else:
                print("❌ Vector database setup failed")
                return 1
                
        except Exception as e:
            print(f"❌ Error setting up vector database: {e}")
            logger.error(f"Database setup error: {e}")
            return 1
    
    def health_check(self, args) -> int:
        """Check the health of vector services."""
        try:
            self._init_services()
            
            print("Checking vector services health...")
            
            # Check vector service
            vector_service_healthy = self.vector_service.health_check()
            print(f"Vector Service: {'✅ Healthy' if vector_service_healthy else '❌ Unhealthy'}")
            
            # Check vector database
            db_health = self.vector_db.health_check()
            print(f"Vector Database: {'✅ Healthy' if db_health['status'] == 'healthy' else '❌ Unhealthy'}")
            
            if db_health['status'] != 'healthy':
                print("Database issues:")
                for error in db_health.get('errors', []):
                    print(f"  - {error}")
            
            print(f"pgvector enabled: {'✅' if db_health.get('pgvector_enabled') else '❌'}")
            print(f"Indexes exist: {'✅' if db_health.get('indexes_exist') else '❌'}")
            print(f"Total vectors: {db_health.get('total_vectors', 0)}")
            
            # Overall health
            overall_healthy = vector_service_healthy and db_health['status'] == 'healthy'
            print(f"\nOverall Status: {'✅ All systems healthy' if overall_healthy else '❌ Issues detected'}")
            
            return 0 if overall_healthy else 1
            
        except Exception as e:
            print(f"❌ Error checking health: {e}")
            logger.error(f"Health check error: {e}")
            return 1
    
    def batch_process(self, args) -> int:
        """Run batch vector processing."""
        try:
            self._init_services()
            
            # Configure batch processing
            config = BatchProcessingConfig(
                batch_size=args.batch_size,
                max_workers=args.max_workers,
                content_types=args.content_types if args.content_types else None,
                force_regenerate=args.force_regenerate,
                skip_existing=not args.force_regenerate,
                max_items_per_run=args.max_items,
                processing_delay=args.delay
            )
            
            processor = VectorBatchProcessor(config)
            
            print(f"Starting batch vector processing...")
            print(f"Content types: {config.content_types}")
            print(f"Batch size: {config.batch_size}")
            print(f"Max workers: {config.max_workers}")
            print(f"Force regenerate: {config.force_regenerate}")
            
            if args.recent_hours:
                print(f"Processing recent content (last {args.recent_hours} hours)")
                stats = processor.process_recent_content(args.recent_hours)
            else:
                print("Processing all content")
                stats = processor.process_all_content()
            
            # Display results
            print("\n" + "="*50)
            print("BATCH PROCESSING RESULTS")
            print("="*50)
            print(f"Total items: {stats.total_items}")
            print(f"Processed items: {stats.processed_items}")
            print(f"Successful vectors: {stats.successful_vectors}")
            print(f"Failed vectors: {stats.failed_vectors}")
            print(f"Skipped items: {stats.skipped_items}")
            print(f"Processing time: {stats.processing_time:.2f} seconds")
            
            if stats.errors:
                print(f"\nErrors ({len(stats.errors)}):")
                for error in stats.errors[:10]:  # Show first 10 errors
                    print(f"  - {error}")
                if len(stats.errors) > 10:
                    print(f"  ... and {len(stats.errors) - 10} more errors")
            
            success_rate = (stats.successful_vectors / stats.total_items * 100) if stats.total_items > 0 else 0
            print(f"\nSuccess rate: {success_rate:.1f}%")
            
            return 0 if success_rate > 80 else 1
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
            logger.error(f"Batch processing error: {e}")
            return 1
    
    def status(self, args) -> int:
        """Show vector processing status."""
        try:
            self._init_services()
            
            print("Getting vector processing status...")
            status_info = self.batch_processor.get_processing_status()
            
            print("\n" + "="*50)
            print("VECTOR PROCESSING STATUS")
            print("="*50)
            
            # Vector statistics
            vector_stats = status_info.get('vector_stats', {})
            print(f"Total vectors: {vector_stats.get('total_vectors', 0)}")
            print(f"Average dimensions: {vector_stats.get('avg_dimensions', 0):.0f}")
            print(f"Storage size: {vector_stats.get('storage_size_mb', 0):.2f} MB")
            
            print("\nVectors by content type:")
            by_type = vector_stats.get('by_content_type', {})
            for content_type, count in by_type.items():
                print(f"  {content_type}: {count}")
            
            # Content counts
            print("\nContent available for vectorization:")
            content_counts = status_info.get('content_counts', {})
            for content_type, counts in content_counts.items():
                total = counts.get('total_items', 0)
                needs_vec = counts.get('needs_vectorization', 0)
                print(f"  {content_type}: {total} total, {needs_vec} need vectorization")
            
            # Service health
            print("\nService health:")
            health = status_info.get('service_health', {})
            vector_service_ok = health.get('vector_service', False)
            db_health = health.get('vector_database', {})
            db_ok = db_health.get('status') == 'healthy'
            
            print(f"  Vector service: {'✅ OK' if vector_service_ok else '❌ Error'}")
            print(f"  Vector database: {'✅ OK' if db_ok else '❌ Error'}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            logger.error(f"Status error: {e}")
            return 1
    
    def search(self, args) -> int:
        """Search for similar content using vector similarity."""
        try:
            self._init_services()
            
            if args.query:
                # Generate vector for query text
                print(f"Generating vector for query: '{args.query}'")
                result = self.vector_service.generate_vector(
                    content=args.query,
                    content_id="query",
                    content_type="query"
                )
                
                if not result.vector:
                    print(f"❌ Failed to generate vector for query: {result.error}")
                    return 1
                
                query_vector = result.vector
                
            elif args.content_id and args.content_type:
                # Use existing content's vector
                print(f"Finding similar content to {args.content_type} {args.content_id}")
                similar_results = self.vector_db.find_similar_content(
                    content_id=args.content_id,
                    content_type=args.content_type,
                    limit=args.limit,
                    similarity_threshold=args.threshold
                )
                
                print(f"\nFound {len(similar_results)} similar items:")
                for i, result in enumerate(similar_results, 1):
                    print(f"{i}. {result.content_type} {result.content_id}")
                    print(f"   Similarity: {result.similarity_score:.3f}")
                    if result.metadata and result.metadata.get('title'):
                        print(f"   Title: {result.metadata['title']}")
                    if result.content_preview:
                        print(f"   Preview: {result.content_preview[:100]}...")
                    print()
                
                return 0
            
            else:
                print("❌ Either --query or both --content-id and --content-type must be provided")
                return 1
            
            # Perform similarity search
            print(f"Searching for similar content (threshold: {args.threshold})...")
            results = self.vector_db.similarity_search(
                query_vector=query_vector,
                content_types=args.content_types if args.content_types else None,
                limit=args.limit,
                similarity_threshold=args.threshold,
                include_content=True
            )
            
            print(f"\nFound {len(results)} similar items:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.content_type} {result.content_id}")
                print(f"   Similarity: {result.similarity_score:.3f}")
                if result.metadata and result.metadata.get('title'):
                    print(f"   Title: {result.metadata['title']}")
                if result.content_preview:
                    print(f"   Preview: {result.content_preview[:100]}...")
                print()
            
            return 0
            
        except Exception as e:
            print(f"❌ Error in search: {e}")
            logger.error(f"Search error: {e}")
            return 1
    
    def rebuild_indexes(self, args) -> int:
        """Rebuild vector indexes."""
        try:
            self._init_services()
            
            print("Rebuilding vector indexes...")
            success = self.vector_db.rebuild_indexes()
            
            if success:
                print("✅ Vector indexes rebuilt successfully")
                return 0
            else:
                print("❌ Failed to rebuild vector indexes")
                return 1
                
        except Exception as e:
            print(f"❌ Error rebuilding indexes: {e}")
            logger.error(f"Index rebuild error: {e}")
            return 1
    
    def clear_cache(self, args) -> int:
        """Clear vector service cache."""
        try:
            self._init_services()
            
            print("Clearing vector service cache...")
            self.vector_service.clear_cache()
            print("✅ Cache cleared successfully")
            return 0
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            logger.error(f"Cache clear error: {e}")
            return 1

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vector Management CLI for Tunisia Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up pgvector extensions and indexes')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check vector services health')
    
    # Batch processing command
    batch_parser = subparsers.add_parser('batch', help='Run batch vector processing')
    batch_parser.add_argument('--batch-size', type=int, default=20, help='Batch size for processing')
    batch_parser.add_argument('--max-workers', type=int, default=4, help='Maximum worker threads')
    batch_parser.add_argument('--content-types', nargs='+', 
                             choices=['article', 'social_post', 'comment', 'entity', 'report'],
                             help='Content types to process')
    batch_parser.add_argument('--force-regenerate', action='store_true', 
                             help='Regenerate vectors even if they exist')
    batch_parser.add_argument('--max-items', type=int, help='Maximum items to process per run')
    batch_parser.add_argument('--delay', type=float, default=0.5, 
                             help='Delay between batches in seconds')
    batch_parser.add_argument('--recent-hours', type=int, 
                             help='Process only content from the last N hours')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show vector processing status')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for similar content')
    search_parser.add_argument('--query', help='Text query to search for')
    search_parser.add_argument('--content-id', help='ID of content to find similar items for')
    search_parser.add_argument('--content-type', 
                              choices=['article', 'social_post', 'comment', 'entity', 'report'],
                              help='Type of content for similarity search')
    search_parser.add_argument('--content-types', nargs='+',
                              choices=['article', 'social_post', 'comment', 'entity', 'report'],
                              help='Content types to search in')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum results to return')
    search_parser.add_argument('--threshold', type=float, default=0.7, 
                              help='Similarity threshold (0-1)')
    
    # Rebuild indexes command
    rebuild_parser = subparsers.add_parser('rebuild', help='Rebuild vector indexes')
    
    # Clear cache command
    cache_parser = subparsers.add_parser('clear-cache', help='Clear vector service cache')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create CLI instance and run command
    cli = VectorCLI()
    
    try:
        if args.command == 'setup':
            return cli.setup_database(args)
        elif args.command == 'health':
            return cli.health_check(args)
        elif args.command == 'batch':
            return cli.batch_process(args)
        elif args.command == 'status':
            return cli.status(args)
        elif args.command == 'search':
            return cli.search(args)
        elif args.command == 'rebuild':
            return cli.rebuild_indexes(args)
        elif args.command == 'clear-cache':
            return cli.clear_cache(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"CLI error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
