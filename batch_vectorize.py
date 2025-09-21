#!/usr/bin/env python3
"""
Batch Vectorization Script for Tunisia Intelligence System.

Simple script to run batch vector processing on existing content.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_enrichment.core.vector_service import VectorService, VectorConfig
from ai_enrichment.core.vector_database import VectorDatabase
from ai_enrichment.processors.vector_batch_processor import VectorBatchProcessor, BatchProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_vectorization.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main batch vectorization function."""
    print("="*60)
    print("TUNISIA INTELLIGENCE - BATCH VECTORIZATION")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        vector_service = VectorService()
        vector_db = VectorDatabase()
        
        # Check health
        print("🏥 Checking service health...")
        if not vector_service.health_check():
            print("❌ Vector service is not healthy. Please check Ollama connection.")
            return 1
        
        db_health = vector_db.health_check()
        if db_health['status'] != 'healthy':
            print("❌ Vector database is not healthy:")
            for error in db_health.get('errors', []):
                print(f"   - {error}")
            
            # Try to setup database
            print("🔧 Attempting to setup vector database...")
            if vector_db.setup_vector_extensions():
                print("✅ Vector database setup completed")
            else:
                print("❌ Failed to setup vector database")
                return 1
        
        print("✅ All services are healthy")
        print()
        
        # Configure batch processing
        config = BatchProcessingConfig(
            batch_size=15,  # Smaller batches for stability
            max_workers=3,  # Conservative worker count
            content_types=['article', 'social_post'],  # Start with main content types
            force_regenerate=False,  # Skip existing vectors
            skip_existing=True,
            max_items_per_run=100,  # Limit for initial run
            processing_delay=1.0  # Longer delay between batches
        )
        
        processor = VectorBatchProcessor(config)
        
        # Show current status
        print("📊 Current status:")
        status = processor.get_processing_status()
        vector_stats = status.get('vector_stats', {})
        content_counts = status.get('content_counts', {})
        
        print(f"   Existing vectors: {vector_stats.get('total_vectors', 0)}")
        print(f"   Storage size: {vector_stats.get('storage_size_mb', 0):.2f} MB")
        print()
        
        for content_type in config.content_types:
            counts = content_counts.get(content_type, {})
            total = counts.get('total_items', 0)
            needs_vec = counts.get('needs_vectorization', 0)
            print(f"   {content_type}: {total} total, {needs_vec} need vectorization")
        print()
        
        # Ask for confirmation
        total_to_process = sum(
            content_counts.get(ct, {}).get('needs_vectorization', 0) 
            for ct in config.content_types
        )
        
        if total_to_process == 0:
            print("✅ No items need vectorization. All done!")
            return 0
        
        print(f"🚀 Ready to process {min(total_to_process, config.max_items_per_run or total_to_process)} items")
        print(f"   Content types: {', '.join(config.content_types)}")
        print(f"   Batch size: {config.batch_size}")
        print(f"   Max workers: {config.max_workers}")
        print()
        
        response = input("Continue with batch processing? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Processing cancelled by user")
            return 0
        
        # Run batch processing
        print("\n🔄 Starting batch vector processing...")
        print("-" * 40)
        
        stats = processor.process_all_content()
        
        # Display results
        print("\n" + "="*60)
        print("BATCH PROCESSING RESULTS")
        print("="*60)
        print(f"Total items: {stats.total_items}")
        print(f"Processed items: {stats.processed_items}")
        print(f"Successful vectors: {stats.successful_vectors}")
        print(f"Failed vectors: {stats.failed_vectors}")
        print(f"Skipped items: {stats.skipped_items}")
        print(f"Processing time: {stats.processing_time:.2f} seconds")
        
        if stats.successful_vectors > 0:
            avg_time = stats.processing_time / stats.successful_vectors
            print(f"Average time per vector: {avg_time:.2f} seconds")
        
        success_rate = (stats.successful_vectors / stats.total_items * 100) if stats.total_items > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        # Show errors if any
        if stats.errors:
            print(f"\n⚠️  Errors encountered ({len(stats.errors)}):")
            for i, error in enumerate(stats.errors[:5], 1):  # Show first 5 errors
                print(f"   {i}. {error}")
            if len(stats.errors) > 5:
                print(f"   ... and {len(stats.errors) - 5} more errors")
        
        # Final status
        print(f"\n📊 Final vector statistics:")
        final_status = processor.get_processing_status()
        final_vector_stats = final_status.get('vector_stats', {})
        print(f"   Total vectors: {final_vector_stats.get('total_vectors', 0)}")
        print(f"   Storage size: {final_vector_stats.get('storage_size_mb', 0):.2f} MB")
        
        by_type = final_vector_stats.get('by_content_type', {})
        for content_type, count in by_type.items():
            print(f"   {content_type}: {count} vectors")
        
        print(f"\n✅ Batch vectorization completed at: {datetime.now()}")
        
        return 0 if success_rate > 80 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during batch processing: {e}")
        logger.error(f"Batch processing error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
