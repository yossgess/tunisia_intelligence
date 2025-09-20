#!/usr/bin/env python3
"""
Check current parsing states in the database.
"""
import logging
from config.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_parsing_states():
    """Check all parsing states in the database."""
    try:
        db = DatabaseManager()
        
        # Get all sources
        sources = db.get_sources()
        logger.info(f"Found {len(sources)} sources in database")
        
        # Check parsing state for each source
        for source in sources[:5]:  # Check first 5 sources
            logger.info(f"\n📰 SOURCE: {source.name}")
            logger.info(f"   URL: {source.url}")
            logger.info(f"   ID: {source.id}")
            
            # Get parsing state
            state = db.get_parsing_state(source.id)
            if state:
                logger.info(f"   ✅ HAS PARSING STATE:")
                logger.info(f"      Last article: {state.last_article_link}")
                logger.info(f"      Last parsed: {state.last_parsed_at}")
                logger.info(f"      Articles count: {state.articles_count}")
            else:
                logger.info(f"   ❌ NO PARSING STATE")
        
        # Check total parsing states
        response = db.client.table("parsing_state").select("*").execute()
        total_states = len(response.data) if response.data else 0
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Total sources: {len(sources)}")
        logger.info(f"   Total parsing states: {total_states}")
        
        if total_states > 0:
            logger.info(f"   🚨 ISSUE: Parsing states still exist!")
            logger.info(f"   💡 Run: python clear_parsing_states.py")
        else:
            logger.info(f"   ✅ No parsing states found (good for fresh start)")
            
    except Exception as e:
        logger.error(f"Error checking parsing states: {e}")
        raise

if __name__ == "__main__":
    check_parsing_states()
