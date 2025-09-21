"""
Enhanced AI Enrichment Examples.

This module demonstrates how to use the enhanced enrichment service
with separate pipelines for articles, posts, and comments.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_enrichment.services.enhanced_enrichment_service import EnhancedEnrichmentService
from ai_enrichment.services.enhanced_enrichment_service_helpers import EnhancedEnrichmentServiceHelpers

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_article_enrichment():
    """Example: Run article enrichment pipeline."""
    logger.info("=== ARTICLE ENRICHMENT EXAMPLE ===")
    
    # Initialize service
    service = EnhancedEnrichmentService()
    helpers = EnhancedEnrichmentServiceHelpers(service.db_manager, service.ollama_client)
    
    # Merge helpers into service
    for method_name in dir(helpers):
        if method_name.startswith('_get_') or method_name.startswith('_perform_') or method_name.startswith('_detect_'):
            setattr(service, method_name, getattr(helpers, method_name))
    
    try:
        # Run article enrichment with limit
        stats = service.enrich_articles(limit=5, force_reprocess=False)
        
        logger.info(f"Article Enrichment Results:")
        logger.info(f"  Total: {stats.total_items}")
        logger.info(f"  Successful: {stats.successful_items}")
        logger.info(f"  Failed: {stats.failed_items}")
        logger.info(f"  Average Confidence: {stats.average_confidence:.3f}")
        logger.info(f"  Processing Time: {stats.processing_time_ms / 1000:.2f}s")
        
    except Exception as e:
        logger.error(f"Article enrichment failed: {e}")

def example_post_enrichment():
    """Example: Run Facebook post enrichment pipeline."""
    logger.info("=== FACEBOOK POST ENRICHMENT EXAMPLE ===")
    
    # Initialize service
    service = EnhancedEnrichmentService()
    helpers = EnhancedEnrichmentServiceHelpers(service.db_manager, service.ollama_client)
    
    # Merge helpers into service
    for method_name in dir(helpers):
        if method_name.startswith('_get_') or method_name.startswith('_perform_') or method_name.startswith('_detect_'):
            setattr(service, method_name, getattr(helpers, method_name))
    
    try:
        # Run post enrichment with limit
        stats = service.enrich_posts(limit=10, force_reprocess=False)
        
        logger.info(f"Post Enrichment Results:")
        logger.info(f"  Total: {stats.total_items}")
        logger.info(f"  Successful: {stats.successful_items}")
        logger.info(f"  Failed: {stats.failed_items}")
        logger.info(f"  Average Confidence: {stats.average_confidence:.3f}")
        logger.info(f"  Processing Time: {stats.processing_time_ms / 1000:.2f}s")
        
    except Exception as e:
        logger.error(f"Post enrichment failed: {e}")

def example_enhanced_comment_enrichment():
    """Example: Run enhanced comment enrichment pipeline."""
    logger.info("=== ENHANCED COMMENT ENRICHMENT EXAMPLE ===")
    
    # Initialize service
    service = EnhancedEnrichmentService()
    helpers = EnhancedEnrichmentServiceHelpers(service.db_manager, service.ollama_client)
    
    # Merge helpers into service
    for method_name in dir(helpers):
        if method_name.startswith('_get_') or method_name.startswith('_perform_') or method_name.startswith('_detect_'):
            setattr(service, method_name, getattr(helpers, method_name))
    
    try:
        # Run enhanced comment enrichment with limit
        stats = service.enrich_comments(limit=25, force_reprocess=False)
        
        logger.info(f"Enhanced Comment Enrichment Results:")
        logger.info(f"  Total: {stats.total_items}")
        logger.info(f"  Successful: {stats.successful_items}")
        logger.info(f"  Failed: {stats.failed_items}")
        logger.info(f"  Average Confidence: {stats.average_confidence:.3f}")
        logger.info(f"  Processing Time: {stats.processing_time_ms / 1000:.2f}s")
        
        # Check analytics after enrichment
        logger.info("\nChecking enrichment analytics...")
        
        from config.database import DatabaseManager
        db = DatabaseManager()
        
        # Query analytics
        analytics = db.client.table("streamlined_enrichment_analytics") \
            .select("*") \
            .eq("content_type", "social_media_comments") \
            .execute()
        
        if analytics.data:
            data = analytics.data[0]
            logger.info(f"Comment Analytics:")
            logger.info(f"  Total Comments: {data['total_items']}")
            logger.info(f"  Enriched: {data['enriched_items']}")
            logger.info(f"  Keywords Extracted: {data['keywords_extracted']}")
            logger.info(f"  Entities Extracted: {data['entities_extracted']}")
            logger.info(f"  Enrichment %: {data['enrichment_percentage']}%")
        
    except Exception as e:
        logger.error(f"Enhanced comment enrichment failed: {e}")

def example_run_all_pipelines():
    """Example: Run all three pipelines together."""
    logger.info("=== RUN ALL PIPELINES EXAMPLE ===")
    
    # Initialize service
    service = EnhancedEnrichmentService()
    helpers = EnhancedEnrichmentServiceHelpers(service.db_manager, service.ollama_client)
    
    # Merge helpers into service
    for method_name in dir(helpers):
        if method_name.startswith('_') and not method_name.startswith('__'):
            setattr(service, method_name, getattr(helpers, method_name))
    
    try:
        # Run all pipelines with different limits
        results = service.run_all_pipelines(
            article_limit=3,
            post_limit=5,
            comment_limit=15,
            force_reprocess=False
        )
        
        logger.info("All Pipelines Results:")
        for pipeline_name, stats in results.items():
            logger.info(f"\n{pipeline_name.upper()}:")
            logger.info(f"  Total: {stats.total_items}")
            logger.info(f"  Successful: {stats.successful_items}")
            logger.info(f"  Failed: {stats.failed_items}")
            logger.info(f"  Time: {stats.processing_time_ms / 1000:.2f}s")
        
        # Overall summary
        total_successful = sum(stats.successful_items for stats in results.values())
        total_items = sum(stats.total_items for stats in results.values())
        total_time = sum(stats.processing_time_ms for stats in results.values())
        
        logger.info(f"\nOVERALL SUMMARY:")
        logger.info(f"  Total Items: {total_items}")
        logger.info(f"  Total Successful: {total_successful}")
        logger.info(f"  Success Rate: {(total_successful/total_items*100) if total_items > 0 else 0:.1f}%")
        logger.info(f"  Total Time: {total_time / 1000:.2f}s")
        
    except Exception as e:
        logger.error(f"All pipelines execution failed: {e}")

def example_pipeline_status():
    """Example: Check pipeline status."""
    logger.info("=== PIPELINE STATUS EXAMPLE ===")
    
    # Initialize service
    service = EnhancedEnrichmentService()
    
    try:
        # Get pipeline status
        status = service.get_pipeline_status()
        
        logger.info("Current Pipeline Status:")
        for pipeline, status_value in status['pipelines'].items():
            logger.info(f"  {pipeline.upper()}: {status_value}")
        
        logger.info(f"Last Updated: {status['timestamp']}")
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")

def main():
    """Run all examples."""
    logger.info("Tunisia Intelligence - Enhanced AI Enrichment Examples")
    logger.info("=" * 60)
    
    try:
        # Run individual pipeline examples
        example_article_enrichment()
        print("\n" + "="*60 + "\n")
        
        example_post_enrichment()
        print("\n" + "="*60 + "\n")
        
        example_enhanced_comment_enrichment()
        print("\n" + "="*60 + "\n")
        
        # Run all pipelines together
        example_run_all_pipelines()
        print("\n" + "="*60 + "\n")
        
        # Check status
        example_pipeline_status()
        
        logger.info("All examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Examples failed: {e}")

if __name__ == "__main__":
    main()
