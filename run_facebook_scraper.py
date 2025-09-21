"""
Ultra-Minimal Facebook Scraper Runner

Maximum efficiency version that achieves 3-4 API calls per source:
- Gets posts + reactions + comments in single API call per source
- Uses estimated reaction breakdowns to avoid multiple API calls
- Perfect for high-frequency monitoring without rate limit concerns

Ideal for Tunisia Intelligence continuous monitoring.
"""

import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from facebook_loader import UltraMinimalFacebookLoader
from config.secrets import SecretManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('facebook_scraper.log')
    ]
)
logger = logging.getLogger(__name__)


def run_ultra_minimal_facebook_scraper(hours_back: int = 168, max_pages: int = 20) -> dict:
    """
    Run the ultra-minimal Facebook scraper
    
    Args:
        hours_back: Number of hours to look back for posts
        max_pages: Maximum pages to process (can be higher due to efficiency)
        
    Returns:
        Dictionary with results and efficiency metrics
    """
    try:
        logger.info(f"Starting ultra-minimal Facebook scraper (hours_back={hours_back}, max_pages={max_pages})")
        
        # Check if Facebook token is configured
        secret_manager = SecretManager(backend="file")
        app_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
        if not app_token:
            error_msg = "Facebook app token not configured. Please run setup_facebook_token.py first."
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        # Initialize ultra-minimal loader
        loader = UltraMinimalFacebookLoader()
        loader.max_pages_per_run = max_pages
        
        # Get Facebook sources count
        sources = loader.load_facebook_sources_prioritized()
        if not sources:
            warning_msg = "No active Facebook sources found in database"
            logger.warning(warning_msg)
            return {"status": "no_sources", "message": warning_msg}
        
        logger.info(f"Found {len(sources)} Facebook sources, will process top {max_pages} by priority")
        
        # Run the ultra-minimal extraction and loading
        result = loader.extract_and_load_posts_ultra_minimal(hours_back=hours_back)
        
        # Enhanced logging with efficiency metrics
        if result.get("status") == "completed":
            api_calls = result.get('api_calls_made', 0)
            sources_processed = result.get('sources_processed', 0)
            posts_loaded = result.get('total_posts_loaded', 0)
            efficiency = result.get('efficiency', 0)
            
            logger.info(f"Ultra-minimal Facebook scraping completed successfully:")
            logger.info(f"  - Sources available: {result.get('total_sources_available', 0)}")
            logger.info(f"  - Sources processed: {sources_processed}")
            logger.info(f"  - Posts loaded: {posts_loaded}")
            logger.info(f"  - API calls made: {api_calls}")
            logger.info(f"  - Efficiency: {efficiency:.1f} calls/source")
            logger.info(f"  - Ultra-efficient: Single call gets all data per source")
            
            if result.get('errors'):
                logger.warning(f"  - Errors encountered: {len(result['errors'])}")
        else:
            logger.error(f"Ultra-minimal Facebook scraping failed: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in ultra-minimal Facebook scraper: {e}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}


def show_ultra_minimal_analysis(result: dict):
    """Show analysis based on ultra-minimal extraction results"""
    print("\n" + "🚀 ULTRA-MINIMAL EXTRACTION ANALYSIS" + "=" * 35)
    
    api_calls = result.get('api_calls_made', 0)
    posts_found = result.get('total_posts_loaded', 0)
    sources_processed = result.get('sources_processed', 0)
    efficiency = result.get('efficiency', 0)
    
    print(f"⚡ MAXIMUM EFFICIENCY ACHIEVED:")
    print(f"   - API calls per source: {efficiency:.1f}")
    print(f"   - Total API usage: {api_calls} calls")
    print(f"   - Intelligence extracted: {posts_found} posts")
    print(f"   - Comments extracted: {result.get('total_comments_loaded', 0)}")
    
    if efficiency <= 4.0:
        print("🏆 PERFECT EFFICIENCY:")
        print("   - Ultra-minimal extraction working perfectly")
        print("   - Can safely run every 2-3 hours")
        print("   - Sustainable for continuous monitoring")
        print("   - Single API call gets posts + reactions + comments")
    elif efficiency <= 6.0:
        print("✅ EXCELLENT EFFICIENCY:")
        print("   - Very good performance")
        print("   - Can run every 4-6 hours safely")
    else:
        print("⚠️  MODERATE EFFICIENCY:")
        print("   - Still good but could be optimized further")
        print("   - Run every 6-8 hours to be safe")
    
    if posts_found == 0:
        print(f"\n📊 NO POSTS FOUND:")
        print(f"   - Government pages may not post frequently")
        print(f"   - Try increasing hours_back parameter")
        print(f"   - Current time window: {result.get('hours_back', 24)} hours")
    else:
        print(f"\n📈 INTELLIGENCE CAPTURED:")
        print(f"   - {posts_found} government posts")
        print(f"   - {result.get('total_reactions_loaded', 0)} reaction records")
        print(f"   - {result.get('total_comments_loaded', 0)} citizen comments")
        print(f"   - Perfect for sentiment analysis")
    
    print(f"\n💡 ULTRA-MINIMAL FEATURES:")
    print(f"   - Single API call per source gets everything")
    print(f"   - Estimated reaction breakdowns (no extra calls)")
    print(f"   - Comments included in main call")
    print(f"   - Perfect for Tunisia Intelligence monitoring")
    
    # Scheduling recommendations
    if efficiency <= 4.0:
        print(f"\n⏰ RECOMMENDED SCHEDULE:")
        print(f"   - Every 3 hours: {sources_processed} pages = ~{api_calls * 8} calls/day")
        print(f"   - Every 2 hours: {sources_processed} pages = ~{api_calls * 12} calls/day")
        print(f"   - Well within Facebook's rate limits!")


def main():
    """Main function with enhanced command line interface"""
    parser = argparse.ArgumentParser(description="Ultra-Minimal Tunisia Intelligence Facebook Scraper")
    
    parser.add_argument(
        "--hours-back",
        type=int,
        default=168,
        help="Number of hours to look back for posts (default: 168 - 7 days)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum pages to process per run (default: 20, can handle more due to efficiency)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--show-analysis",
        action="store_true",
        help="Show detailed efficiency analysis after run"
    )
    
    args = parser.parse_args()
    
    # Ultra-minimal can handle more pages
    if args.max_pages > 30:
        print("⚠️  Warning: max_pages > 30 may still hit rate limits")
        print("   Ultra-minimal recommended: 15-25 for optimal safety")
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the ultra-minimal scraper
    result = run_ultra_minimal_facebook_scraper(
        hours_back=args.hours_back,
        max_pages=args.max_pages
    )
    
    # Print results
    print("\n" + "=" * 70)
    print("ULTRA-MINIMAL FACEBOOK SCRAPER RESULTS")
    print("=" * 70)
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result.get('status') == 'completed':
        api_calls = result.get('api_calls_made', 0)
        sources_processed = result.get('sources_processed', 0)
        efficiency = result.get('efficiency', 0)
        
        print(f"Sources available: {result.get('total_sources_available', 0)}")
        print(f"Sources processed: {sources_processed}")
        print(f"Posts loaded: {result.get('total_posts_loaded', 0)}")
        print(f"Reactions loaded: {result.get('total_reactions_loaded', 0)}")
        print(f"Comments loaded: {result.get('total_comments_loaded', 0)}")
        print(f"API calls made: {api_calls}")
        print(f"Efficiency: {efficiency:.1f} calls/source")
        
        # Efficiency rating
        if efficiency <= 4.0:
            print("Efficiency Rating: 🏆 PERFECT")
        elif efficiency <= 6.0:
            print("Efficiency Rating: ✅ EXCELLENT")
        elif efficiency <= 10.0:
            print("Efficiency Rating: ⚠️  MODERATE")
        else:
            print("Efficiency Rating: ❌ NEEDS OPTIMIZATION")
        
        if result.get('optimization_notes'):
            print("\nOptimization Notes:")
            for note in result['optimization_notes']:
                print(f"  • {note}")
        
        if result.get('errors'):
            print(f"\nErrors: {len(result['errors'])}")
            # Show only first 3 errors to avoid spam
            for error in result['errors'][:3]:
                print(f"  - {error}")
            if len(result['errors']) > 3:
                print(f"  ... and {len(result['errors']) - 3} more errors")
    
    elif result.get('message'):
        print(f"Message: {result['message']}")
    
    print("=" * 70)
    
    # Show analysis if requested
    if args.show_analysis:
        show_ultra_minimal_analysis(result)
    
    # Exit with appropriate code
    if result.get('status') in ['completed', 'no_sources']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
