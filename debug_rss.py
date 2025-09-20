#!/usr/bin/env python3
"""
Debug script to test RSS processing with detailed logging.
"""
import logging
import sys
from rss_loader import RSSLoader
from config.database import DatabaseManager

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Enable debug for specific loggers
logging.getLogger('rss_loader').setLevel(logging.DEBUG)
logging.getLogger('extractors').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

def test_single_source():
    """Test processing a single source with detailed debugging."""
    try:
        # Initialize components
        db = DatabaseManager()
        loader = RSSLoader()
        loader.force_process_all = True  # Force process all articles
        
        # Get first source for testing
        sources = db.get_sources()
        if not sources:
            logger.error("No sources found in database")
            return
        
        test_source = sources[0]  # Test with first source
        logger.info(f"🧪 Testing with source: {test_source.name} ({test_source.url})")
        
        # Process just this one source
        result = loader.process_source(test_source)
        
        # Show detailed results
        logger.info("🎯 DETAILED RESULTS:")
        for key, value in result.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("🚀 Starting RSS debug test...")
    test_single_source()
    logger.info("✅ Debug test completed")
