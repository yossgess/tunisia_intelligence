#!/usr/bin/env python3
"""
Optimized performance test script comparing fast mode vs normal mode.
"""
import time
import logging
from rss_loader import RSSLoader
from config.database import DatabaseManager
from config.settings import get_settings

# Set up minimal logging for performance testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_performance_modes():
    """Test performance comparison between fast mode and normal mode."""
    logger.info("🚀 Starting Optimized RSS Loader Performance Test")
    logger.info("=" * 70)
    
    # Get test sources
    db = DatabaseManager()
    sources = db.get_sources()[:3]  # Test with 3 sources for speed
    
    logger.info(f"Testing with {len(sources)} sources:")
    for source in sources:
        logger.info(f"  - {source.name}")
    
    # Test configurations
    test_configs = [
        {"name": "FAST MODE", "fast_mode": True},
        {"name": "NORMAL MODE", "fast_mode": False}
    ]
    
    results = {}
    
    for config in test_configs:
        logger.info(f"\n{'='*20} {config['name']} {'='*20}")
        
        # Initialize loader with specific configuration
        loader = RSSLoader()
        loader.force_process_all = True
        loader.settings.scraping.fast_mode = config['fast_mode']
        
        start_time = time.time()
        total_articles = 0
        
        for i, source in enumerate(sources, 1):
            logger.info(f"Processing source {i}/{len(sources)}: {source.name}")
            
            source_start = time.time()
            result = loader.process_source(source)
            source_end = time.time()
            
            articles = result.get('articles_processed', 0)
            processing_time = source_end - source_start
            
            total_articles += articles
            logger.info(f"  ✅ {articles} articles in {processing_time:.2f}s")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        results[config['name']] = {
            'total_time': total_time,
            'total_articles': total_articles,
            'articles_per_second': total_articles / total_time if total_time > 0 else 0
        }
        
        logger.info(f"\n{config['name']} RESULTS:")
        logger.info(f"  Total time: {total_time:.2f} seconds")
        logger.info(f"  Total articles: {total_articles}")
        logger.info(f"  Speed: {results[config['name']]['articles_per_second']:.1f} articles/second")
    
    # Performance comparison
    logger.info("\n" + "="*70)
    logger.info("PERFORMANCE COMPARISON")
    logger.info("="*70)
    
    fast_speed = results['FAST MODE']['articles_per_second']
    normal_speed = results['NORMAL MODE']['articles_per_second']
    
    if normal_speed > 0:
        improvement = ((fast_speed - normal_speed) / normal_speed) * 100
        logger.info(f"Fast Mode Speed:    {fast_speed:.1f} articles/second")
        logger.info(f"Normal Mode Speed:  {normal_speed:.1f} articles/second")
        logger.info(f"Performance Gain:   {improvement:+.1f}%")
        
        if improvement > 50:
            logger.info("🏆 EXCELLENT: >50% improvement!")
        elif improvement > 25:
            logger.info("✅ GOOD: >25% improvement")
        elif improvement > 0:
            logger.info("⚠️  MODEST: Some improvement")
        else:
            logger.info("❌ NO IMPROVEMENT: Consider further optimization")
    
    # Recommendations
    logger.info("\n" + "-"*70)
    logger.info("OPTIMIZATION RECOMMENDATIONS")
    logger.info("-"*70)
    
    if fast_speed >= 3.0:
        logger.info("🎯 TARGET ACHIEVED: >3 articles/second")
        logger.info("✅ System is well-optimized for production use")
    elif fast_speed >= 2.0:
        logger.info("⚡ GOOD PERFORMANCE: >2 articles/second")
        logger.info("💡 Consider database connection pooling for further gains")
    else:
        logger.info("🔧 NEEDS OPTIMIZATION: <2 articles/second")
        logger.info("💡 Consider:")
        logger.info("   - Reducing content extraction complexity")
        logger.info("   - Implementing connection pooling")
        logger.info("   - Using async processing")
    
    logger.info("="*70)
    logger.info("✅ Optimized performance test completed!")

if __name__ == "__main__":
    test_performance_modes()
