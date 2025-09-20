#!/usr/bin/env python3
"""
Performance test script for the optimized RSS loader.
Tests processing speed and memory efficiency improvements.
"""
import time
import logging
from rss_loader import RSSLoader
from config.database import DatabaseManager

# Set up minimal logging for performance testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_performance():
    """Test the performance of the optimized RSS loader."""
    logger.info("🚀 Starting RSS Loader Performance Test")
    logger.info("=" * 60)
    
    # Initialize components
    start_time = time.time()
    loader = RSSLoader()
    loader.force_process_all = True  # Force process for consistent testing
    
    # Get a few test sources
    db = DatabaseManager()
    sources = db.get_sources()[:5]  # Test with first 5 sources
    
    logger.info(f"Testing with {len(sources)} sources:")
    for source in sources:
        logger.info(f"  - {source.name} ({source.url})")
    
    logger.info("-" * 60)
    
    # Process sources and measure performance
    results = []
    total_articles = 0
    total_processing_time = 0
    
    for i, source in enumerate(sources, 1):
        logger.info(f"Processing source {i}/{len(sources)}: {source.name}")
        
        source_start = time.time()
        result = loader.process_source(source)
        source_end = time.time()
        
        processing_time = source_end - source_start
        articles_processed = result.get('articles_processed', 0)
        
        results.append({
            'source': source.name,
            'articles': articles_processed,
            'time': processing_time,
            'rate': articles_processed / processing_time if processing_time > 0 else 0
        })
        
        total_articles += articles_processed
        total_processing_time += processing_time
        
        logger.info(f"  ✅ {articles_processed} articles in {processing_time:.2f}s ({articles_processed/processing_time:.1f} articles/sec)")
    
    # Calculate overall performance
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info("=" * 60)
    logger.info("PERFORMANCE TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total sources processed:    {len(sources)}")
    logger.info(f"Total articles processed:   {total_articles}")
    logger.info(f"Total processing time:      {total_processing_time:.2f} seconds")
    logger.info(f"Total elapsed time:         {total_time:.2f} seconds")
    logger.info(f"Average processing speed:   {total_articles/total_processing_time:.1f} articles/second")
    logger.info(f"Average source time:        {total_processing_time/len(sources):.2f} seconds/source")
    
    # Show per-source breakdown
    logger.info("-" * 60)
    logger.info("PER-SOURCE PERFORMANCE")
    logger.info("-" * 60)
    for result in results:
        logger.info(f"{result['source']:<25} {result['articles']:>3} articles  {result['time']:>6.2f}s  {result['rate']:>6.1f} art/sec")
    
    # Performance benchmarks
    logger.info("-" * 60)
    logger.info("PERFORMANCE BENCHMARKS")
    logger.info("-" * 60)
    
    if total_articles/total_processing_time >= 5.0:
        logger.info("🏆 EXCELLENT: >5 articles/second - Highly optimized!")
    elif total_articles/total_processing_time >= 3.0:
        logger.info("✅ GOOD: >3 articles/second - Well optimized")
    elif total_articles/total_processing_time >= 1.0:
        logger.info("⚠️  FAIR: >1 article/second - Could be improved")
    else:
        logger.info("❌ SLOW: <1 article/second - Needs optimization")
    
    logger.info("=" * 60)
    logger.info("✅ Performance test completed!")

if __name__ == "__main__":
    test_performance()
