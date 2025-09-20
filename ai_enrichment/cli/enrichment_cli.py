"""
Command Line Interface for AI Enrichment Operations.

This module provides CLI commands for managing AI enrichment operations,
including batch processing, testing, and monitoring.
"""

import argparse
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..services.enrichment_service import EnrichmentService
from ..services.batch_processor import BatchProcessor
from ..core.ollama_client import OllamaConfig
from ..models.enrichment_models import EnrichmentRequest, ProcessingStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnrichmentCLI:
    """
    Command Line Interface for AI Enrichment operations.
    
    Provides commands for:
    - Testing AI processors
    - Running batch enrichment
    - Monitoring processing status
    - Managing configuration
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.enrichment_service = None
        self.batch_processor = None
    
    def _init_services(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        """Initialize services with configuration."""
        if not self.enrichment_service:
            ollama_config = OllamaConfig(base_url=ollama_url, model=model)
            self.enrichment_service = EnrichmentService(ollama_config=ollama_config)
            self.batch_processor = BatchProcessor(enrichment_service=self.enrichment_service)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="AI Enrichment CLI for Tunisia Intelligence",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Test all processors
  python -m ai_enrichment.cli.enrichment_cli test
  
  # Process articles in batch
  python -m ai_enrichment.cli.enrichment_cli batch articles --limit 100
  
  # Process social media posts
  python -m ai_enrichment.cli.enrichment_cli batch posts --limit 50
  
  # Check service status
  python -m ai_enrichment.cli.enrichment_cli status
  
  # Enrich single text
  python -m ai_enrichment.cli.enrichment_cli enrich "هذا نص للاختبار"
            """
        )
        
        # Global options
        parser.add_argument(
            '--ollama-url',
            default='http://localhost:11434',
            help='Ollama server URL (default: http://localhost:11434)'
        )
        parser.add_argument(
            '--model',
            default='qwen2.5:7b',
            help='Ollama model to use (default: qwen2.5:7b)'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Test command
        test_parser = subparsers.add_parser('test', help='Test AI processors')
        test_parser.add_argument(
            '--content',
            default='هذا نص تجريبي للاختبار. This is a test text.',
            help='Content to use for testing'
        )
        test_parser.add_argument(
            '--processor',
            choices=['sentiment', 'entities', 'keywords', 'categories', 'all'],
            default='all',
            help='Specific processor to test'
        )
        
        # Status command
        subparsers.add_parser('status', help='Check service status')
        
        # Enrich command
        enrich_parser = subparsers.add_parser('enrich', help='Enrich single text')
        enrich_parser.add_argument('content', help='Text content to enrich')
        enrich_parser.add_argument(
            '--type',
            choices=['article', 'social_media_post', 'comment'],
            default='article',
            help='Content type'
        )
        enrich_parser.add_argument(
            '--output',
            choices=['json', 'summary'],
            default='summary',
            help='Output format'
        )
        
        # Batch command
        batch_parser = subparsers.add_parser('batch', help='Run batch processing')
        batch_subparsers = batch_parser.add_subparsers(dest='batch_type', help='Batch processing type')
        
        # Batch articles
        articles_parser = batch_subparsers.add_parser('articles', help='Process articles')
        articles_parser.add_argument('--limit', type=int, help='Maximum number of articles to process')
        articles_parser.add_argument('--offset', type=int, default=0, help='Starting offset')
        articles_parser.add_argument('--source-ids', nargs='+', type=int, help='Filter by source IDs')
        articles_parser.add_argument('--days-back', type=int, help='Process articles from N days back')
        articles_parser.add_argument('--force', action='store_true', help='Reprocess already enriched articles')
        
        # Batch social media posts
        posts_parser = batch_subparsers.add_parser('posts', help='Process social media posts')
        posts_parser.add_argument('--limit', type=int, help='Maximum number of posts to process')
        posts_parser.add_argument('--offset', type=int, default=0, help='Starting offset')
        posts_parser.add_argument('--account', help='Filter by account name')
        posts_parser.add_argument('--days-back', type=int, help='Process posts from N days back')
        posts_parser.add_argument('--force', action='store_true', help='Reprocess already enriched posts')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show processing statistics')
        stats_parser.add_argument(
            '--type',
            choices=['articles', 'posts'],
            default='articles',
            help='Content type for statistics'
        )
        stats_parser.add_argument('--days', type=int, default=7, help='Days to analyze')
        
        return parser
    
    def run_test(self, args) -> None:
        """Run processor tests."""
        self._init_services(args.ollama_url, args.model)
        
        print("🧪 Testing AI Enrichment Processors")
        print("=" * 50)
        
        if args.processor == 'all':
            results = self.enrichment_service.test_processors(args.content)
        else:
            # Test specific processor
            if args.processor == 'sentiment':
                result = self.enrichment_service.sentiment_analyzer.process(args.content)
            elif args.processor == 'entities':
                result = self.enrichment_service.entity_extractor.process(args.content)
            elif args.processor == 'keywords':
                result = self.enrichment_service.keyword_extractor.process(args.content)
            elif args.processor == 'categories':
                result = self.enrichment_service.category_classifier.process(args.content)
            
            results = {args.processor: {
                'status': result.status.value,
                'confidence': result.confidence,
                'processing_time': result.processing_time
            }}
        
        # Display results
        for processor, result in results.items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            print(f"\n{status_emoji} {processor.upper()}")
            print(f"   Status: {result['status']}")
            if 'confidence' in result:
                print(f"   Confidence: {result['confidence']:.2f}")
            if 'processing_time' in result:
                print(f"   Time: {result['processing_time']:.2f}s")
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        print(f"\n📝 Test Content: {args.content[:100]}...")
    
    def run_status(self, args) -> None:
        """Check service status."""
        self._init_services(args.ollama_url, args.model)
        
        print("🔍 AI Enrichment Service Status")
        print("=" * 40)
        
        status = self.enrichment_service.get_service_status()
        
        # Ollama status
        ollama_emoji = "✅" if status['ollama_available'] else "❌"
        print(f"\n{ollama_emoji} Ollama Service")
        print(f"   Available: {status['ollama_available']}")
        print(f"   Model: {status['ollama_model']}")
        
        # Database status
        db_emoji = "✅" if status['database_connected'] else "❌"
        print(f"\n{db_emoji} Database")
        print(f"   Connected: {status['database_connected']}")
        
        # Processors status
        print(f"\n🤖 AI Processors")
        for processor, available in status['processors'].items():
            proc_emoji = "✅" if available else "❌"
            print(f"   {proc_emoji} {processor}")
        
        # Configuration
        print(f"\n⚙️  Configuration")
        config = status['configuration']
        print(f"   Parallel Processing: {config['parallel_processing']}")
        print(f"   Max Workers: {config['max_workers']}")
        print(f"   Save to Database: {config['save_to_database']}")
    
    def run_enrich(self, args) -> None:
        """Enrich single text content."""
        self._init_services(args.ollama_url, args.model)
        
        print(f"🔄 Enriching {args.type} content...")
        
        result = self.enrichment_service.enrich_content(
            content=args.content,
            content_type=args.type
        )
        
        if args.output == 'json':
            # Output full JSON result
            result_dict = result.dict()
            print(json.dumps(result_dict, ensure_ascii=False, indent=2, default=str))
        else:
            # Output summary
            print(f"\n📊 Enrichment Results")
            print("=" * 30)
            
            status_emoji = "✅" if result.status == ProcessingStatus.SUCCESS else "❌"
            print(f"\n{status_emoji} Status: {result.status.value}")
            print(f"🎯 Confidence: {result.confidence:.2f}")
            
            if result.processing_time:
                print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
            
            if result.sentiment:
                print(f"\n😊 Sentiment: {result.sentiment.sentiment.value} ({result.sentiment.confidence:.2f})")
                if result.sentiment.emotions:
                    print(f"   Emotions: {', '.join(result.sentiment.emotions)}")
            
            if result.entities:
                print(f"\n👥 Entities ({len(result.entities)}):")
                for entity in result.entities[:5]:  # Show top 5
                    print(f"   • {entity.text} ({entity.type.value}) - {entity.confidence:.2f}")
            
            if result.keywords:
                print(f"\n🔑 Keywords ({len(result.keywords)}):")
                for keyword in result.keywords[:10]:  # Show top 10
                    print(f"   • {keyword.text} ({keyword.importance:.2f})")
            
            if result.category:
                print(f"\n📂 Category: {result.category.primary_category} ({result.category.confidence:.2f})")
                if result.category.secondary_categories:
                    print(f"   Secondary: {', '.join(result.category.secondary_categories)}")
            
            if result.error_message:
                print(f"\n❌ Error: {result.error_message}")
    
    def run_batch(self, args) -> None:
        """Run batch processing."""
        self._init_services(args.ollama_url, args.model)
        
        # Calculate date range if days_back is specified
        date_from = None
        if hasattr(args, 'days_back') and args.days_back:
            date_from = datetime.now() - timedelta(days=args.days_back)
        
        if args.batch_type == 'articles':
            print(f"🔄 Starting batch processing of articles...")
            if args.limit:
                print(f"   Limit: {args.limit}")
            if args.source_ids:
                print(f"   Source IDs: {args.source_ids}")
            if date_from:
                print(f"   From: {date_from.strftime('%Y-%m-%d')}")
            
            result = self.batch_processor.process_articles(
                limit=args.limit,
                offset=args.offset,
                source_ids=args.source_ids,
                date_from=date_from,
                force_reprocess=args.force
            )
            
        elif args.batch_type == 'posts':
            print(f"🔄 Starting batch processing of social media posts...")
            if args.limit:
                print(f"   Limit: {args.limit}")
            if args.account:
                print(f"   Account: {args.account}")
            if date_from:
                print(f"   From: {date_from.strftime('%Y-%m-%d')}")
            
            result = self.batch_processor.process_social_media_posts(
                limit=args.limit,
                offset=args.offset,
                account_filter=args.account,
                date_from=date_from,
                force_reprocess=args.force
            )
        else:
            print("❌ Invalid batch type. Use 'articles' or 'posts'.")
            return
        
        # Display results
        print(f"\n📊 Batch Processing Results")
        print("=" * 35)
        print(f"📝 Total Items: {result.total_items}")
        print(f"✅ Successful: {result.successful_items}")
        print(f"❌ Failed: {result.failed_items}")
        print(f"⏭️  Skipped: {result.skipped_items}")
        print(f"📈 Success Rate: {result.success_rate:.1%}")
        print(f"🎯 Avg Confidence: {result.average_confidence:.2f}")
        print(f"⏱️  Total Time: {result.total_processing_time:.1f}s")
        
        # Component results
        if result.sentiment_results > 0:
            print(f"😊 Sentiment Results: {result.sentiment_results}")
        if result.entity_results > 0:
            print(f"👥 Entity Results: {result.entity_results}")
        if result.keyword_results > 0:
            print(f"🔑 Keyword Results: {result.keyword_results}")
        if result.category_results > 0:
            print(f"📂 Category Results: {result.category_results}")
    
    def run_stats(self, args) -> None:
        """Show processing statistics."""
        self._init_services(args.ollama_url, args.model)
        
        content_type = "article" if args.type == "articles" else "social_media_post"
        stats = self.batch_processor.get_processing_statistics(
            content_type=content_type,
            days_back=args.days
        )
        
        if 'error' in stats:
            print(f"❌ Error getting statistics: {stats['error']}")
            return
        
        print(f"📊 Processing Statistics - {args.type.title()}")
        print("=" * 40)
        print(f"📝 Total Items: {stats['total_items']:,}")
        print(f"✅ Enriched: {stats['enriched_items']:,}")
        print(f"⏳ Pending: {stats['pending_items']:,}")
        print(f"📈 Enrichment Rate: {stats['enrichment_rate']:.1f}%")
        
        print(f"\n📅 Recent Activity ({args.days} days)")
        print(f"📝 Recent Items: {stats['recent_items']:,}")
        print(f"✅ Recently Enriched: {stats['recent_enriched']:,}")
        print(f"⏳ Recent Pending: {stats['recent_pending']:,}")
    
    def main(self, argv: Optional[List[str]] = None) -> None:
        """Main CLI entry point."""
        parser = self.create_parser()
        args = parser.parse_args(argv)
        
        # Configure logging level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Route to appropriate command
        if args.command == 'test':
            self.run_test(args)
        elif args.command == 'status':
            self.run_status(args)
        elif args.command == 'enrich':
            self.run_enrich(args)
        elif args.command == 'batch':
            self.run_batch(args)
        elif args.command == 'stats':
            self.run_stats(args)
        else:
            parser.print_help()

def main():
    """Entry point for CLI script."""
    cli = EnrichmentCLI()
    try:
        cli.main()
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
