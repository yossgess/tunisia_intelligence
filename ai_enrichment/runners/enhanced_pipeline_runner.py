"""
Enhanced Pipeline Runner for Tunisia Intelligence AI Enrichment.

This module provides a command-line interface to run the three AI enrichment
pipelines individually or together, with comprehensive logging and monitoring.
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import Optional, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enrichment_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import the enhanced enrichment service
from ai_enrichment.services.enhanced_enrichment_service import EnhancedEnrichmentService
from ai_enrichment.services.enhanced_enrichment_service_helpers import EnhancedEnrichmentServiceHelpers

class EnhancedPipelineRunner:
    """
    Command-line runner for AI enrichment pipelines.
    
    Supports running individual pipelines or all together with various options:
    - Article enrichment pipeline
    - Facebook post enrichment pipeline  
    - Enhanced comment enrichment pipeline
    """
    
    def __init__(self):
        """Initialize the pipeline runner."""
        self.service = EnhancedEnrichmentService()
        self.helpers = EnhancedEnrichmentServiceHelpers(
            self.service.db_manager, 
            self.service.ollama_client
        )
        
        # Merge helper methods into service
        for method_name in dir(self.helpers):
            if not method_name.startswith('_') or method_name.startswith('_get_') or method_name.startswith('_perform_') or method_name.startswith('_detect_') or method_name.startswith('_translate_') or method_name.startswith('_start_') or method_name.startswith('_complete_') or method_name.startswith('_update_'):
                if hasattr(self.helpers, method_name):
                    setattr(self.service, method_name, getattr(self.helpers, method_name))
        
        logger.info("Enhanced pipeline runner initialized")
    
    def run_article_pipeline(self, 
                           limit: Optional[int] = None,
                           source_ids: Optional[List[int]] = None,
                           force_reprocess: bool = False) -> bool:
        """Run the article enrichment pipeline."""
        try:
            logger.info("=" * 60)
            logger.info("STARTING ARTICLE ENRICHMENT PIPELINE")
            logger.info("=" * 60)
            
            stats = self.service.enrich_articles(
                limit=limit,
                source_ids=source_ids,
                force_reprocess=force_reprocess
            )
            
            # Print results
            self._print_pipeline_results("Articles", stats)
            return stats.failed_items == 0
            
        except Exception as e:
            logger.error(f"Article pipeline failed: {e}")
            return False
    
    def run_post_pipeline(self,
                         limit: Optional[int] = None,
                         source_ids: Optional[List[int]] = None,
                         force_reprocess: bool = False) -> bool:
        """Run the Facebook post enrichment pipeline."""
        try:
            logger.info("=" * 60)
            logger.info("STARTING FACEBOOK POST ENRICHMENT PIPELINE")
            logger.info("=" * 60)
            
            stats = self.service.enrich_posts(
                limit=limit,
                source_ids=source_ids,
                force_reprocess=force_reprocess
            )
            
            # Print results
            self._print_pipeline_results("Facebook Posts", stats)
            return stats.failed_items == 0
            
        except Exception as e:
            logger.error(f"Post pipeline failed: {e}")
            return False
    
    def run_comment_pipeline(self,
                           limit: Optional[int] = None,
                           post_ids: Optional[List[int]] = None,
                           force_reprocess: bool = False) -> bool:
        """Run the enhanced comment enrichment pipeline."""
        try:
            logger.info("=" * 60)
            logger.info("STARTING ENHANCED COMMENT ENRICHMENT PIPELINE")
            logger.info("=" * 60)
            
            stats = self.service.enrich_comments(
                limit=limit,
                post_ids=post_ids,
                force_reprocess=force_reprocess
            )
            
            # Print results
            self._print_pipeline_results("Comments", stats)
            return stats.failed_items == 0
            
        except Exception as e:
            logger.error(f"Comment pipeline failed: {e}")
            return False
    
    def run_all_pipelines(self,
                         article_limit: Optional[int] = None,
                         post_limit: Optional[int] = None,
                         comment_limit: Optional[int] = None,
                         force_reprocess: bool = False) -> bool:
        """Run all three enrichment pipelines in sequence."""
        try:
            logger.info("=" * 60)
            logger.info("STARTING ALL ENRICHMENT PIPELINES")
            logger.info("=" * 60)
            
            results = self.service.run_all_pipelines(
                article_limit=article_limit,
                post_limit=post_limit,
                comment_limit=comment_limit,
                force_reprocess=force_reprocess
            )
            
            # Print comprehensive results
            self._print_comprehensive_results(results)
            
            # Check if all pipelines succeeded
            all_success = all(
                stats.failed_items == 0 for stats in results.values()
            )
            
            return all_success
            
        except Exception as e:
            logger.error(f"All pipelines execution failed: {e}")
            return False
    
    def get_pipeline_status(self):
        """Get and display current pipeline status."""
        try:
            status = self.service.get_pipeline_status()
            
            logger.info("=" * 50)
            logger.info("CURRENT PIPELINE STATUS")
            logger.info("=" * 50)
            
            for pipeline, status_value in status['pipelines'].items():
                logger.info(f"{pipeline.upper()}: {status_value}")
            
            logger.info(f"Last Updated: {status['timestamp']}")
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return None
    
    def _print_pipeline_results(self, pipeline_name: str, stats):
        """Print results for a single pipeline."""
        logger.info("-" * 50)
        logger.info(f"{pipeline_name.upper()} ENRICHMENT RESULTS")
        logger.info("-" * 50)
        logger.info(f"Total Items: {stats.total_items}")
        logger.info(f"Processed: {stats.processed_items}")
        logger.info(f"Successful: {stats.successful_items}")
        logger.info(f"Failed: {stats.failed_items}")
        logger.info(f"Skipped: {stats.skipped_items}")
        logger.info(f"Processing Time: {stats.processing_time_ms / 1000:.2f} seconds")
        logger.info(f"Average Confidence: {stats.average_confidence:.3f}")
        
        if stats.total_items > 0:
            success_rate = (stats.successful_items / stats.total_items) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("-" * 50)
    
    def _print_comprehensive_results(self, results: dict):
        """Print comprehensive results for all pipelines."""
        logger.info("=" * 60)
        logger.info("COMPREHENSIVE ENRICHMENT RESULTS")
        logger.info("=" * 60)
        
        total_items = 0
        total_processed = 0
        total_successful = 0
        total_failed = 0
        total_time = 0
        
        for pipeline_name, stats in results.items():
            logger.info(f"\n{pipeline_name.upper()}:")
            logger.info(f"  Items: {stats.total_items}")
            logger.info(f"  Successful: {stats.successful_items}")
            logger.info(f"  Failed: {stats.failed_items}")
            logger.info(f"  Time: {stats.processing_time_ms / 1000:.2f}s")
            logger.info(f"  Confidence: {stats.average_confidence:.3f}")
            
            total_items += stats.total_items
            total_processed += stats.processed_items
            total_successful += stats.successful_items
            total_failed += stats.failed_items
            total_time += stats.processing_time_ms
        
        logger.info("\n" + "=" * 40)
        logger.info("OVERALL SUMMARY:")
        logger.info(f"  Total Items: {total_items}")
        logger.info(f"  Total Processed: {total_processed}")
        logger.info(f"  Total Successful: {total_successful}")
        logger.info(f"  Total Failed: {total_failed}")
        logger.info(f"  Total Time: {total_time / 1000:.2f} seconds")
        
        if total_items > 0:
            overall_success_rate = (total_successful / total_items) * 100
            logger.info(f"  Overall Success Rate: {overall_success_rate:.1f}%")
        
        logger.info("=" * 60)

def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Enhanced AI Enrichment Pipeline Runner for Tunisia Intelligence"
    )
    
    # Pipeline selection
    parser.add_argument(
        '--pipeline', 
        choices=['articles', 'posts', 'comments', 'all'],
        default='all',
        help='Which pipeline(s) to run'
    )
    
    # Limits
    parser.add_argument('--article-limit', type=int, help='Limit for article processing')
    parser.add_argument('--post-limit', type=int, help='Limit for post processing')
    parser.add_argument('--comment-limit', type=int, help='Limit for comment processing')
    parser.add_argument('--limit', type=int, help='General limit (applies to selected pipeline)')
    
    # Filtering
    parser.add_argument('--source-ids', nargs='+', type=int, help='Specific source IDs to process')
    parser.add_argument('--post-ids', nargs='+', type=int, help='Specific post IDs for comment processing')
    
    # Options
    parser.add_argument('--force-reprocess', action='store_true', help='Reprocess already enriched content')
    parser.add_argument('--status', action='store_true', help='Show pipeline status and exit')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Initialize runner
    runner = EnhancedPipelineRunner()
    
    # Show status if requested
    if args.status:
        runner.get_pipeline_status()
        return
    
    success = False
    
    try:
        if args.pipeline == 'articles':
            success = runner.run_article_pipeline(
                limit=args.limit,
                source_ids=args.source_ids,
                force_reprocess=args.force_reprocess
            )
        
        elif args.pipeline == 'posts':
            success = runner.run_post_pipeline(
                limit=args.limit,
                source_ids=args.source_ids,
                force_reprocess=args.force_reprocess
            )
        
        elif args.pipeline == 'comments':
            success = runner.run_comment_pipeline(
                limit=args.limit,
                post_ids=args.post_ids,
                force_reprocess=args.force_reprocess
            )
        
        elif args.pipeline == 'all':
            success = runner.run_all_pipelines(
                article_limit=args.article_limit,
                post_limit=args.post_limit,
                comment_limit=args.comment_limit,
                force_reprocess=args.force_reprocess
            )
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
