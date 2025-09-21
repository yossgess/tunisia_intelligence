#!/usr/bin/env python3
"""
Enhanced AI Enrichment Pipeline Runner - Main Entry Point.

This script provides easy access to run the enhanced AI enrichment pipelines
for the Tunisia Intelligence system.

Usage Examples:
    # Run all pipelines
    python run_enhanced_enrichment.py

    # Run only comment enrichment with limit
    python run_enhanced_enrichment.py --pipeline comments --limit 100

    # Run articles and posts with force reprocess
    python run_enhanced_enrichment.py --pipeline articles --force-reprocess

    # Check pipeline status
    python run_enhanced_enrichment.py --status

    # Run with specific limits for each pipeline
    python run_enhanced_enrichment.py --pipeline all --article-limit 50 --post-limit 30 --comment-limit 200
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the enhanced pipeline runner
from ai_enrichment.runners.enhanced_pipeline_runner import src.core.main

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Enhanced AI Enrichment Pipeline Runner")
        logger.info("Tunisia Intelligence System - AI Enrichment")
        logger.info("=" * 60)
        
        # Run the main pipeline runner
        main()
        
    except Exception as e:
        logger.error(f"Failed to start pipeline runner: {e}")
        sys.exit(1)
