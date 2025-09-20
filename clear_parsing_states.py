#!/usr/bin/env python3
"""
Clear all parsing states and logs from the database.

This script will completely reset the parsing state, forcing the RSS loader
to process all articles as if running for the first time.
"""
import logging
from config.database import DatabaseManager
from config.settings import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_all_parsing_data():
    """Clear all parsing states and logs from the database."""
    try:
        # Initialize database connection
        db = DatabaseManager()
        settings = get_settings()
        
        logger.info("🗑️  Starting database cleanup...")
        
        # Clear parsing states
        logger.info("Clearing parsing states...")
        response = db.client.table("parsing_state").delete().neq("id", "").execute()
        states_deleted = len(response.data) if response.data else 0
        logger.info(f"✅ Deleted {states_deleted} parsing states")
        
        # Clear parsing logs
        logger.info("Clearing parsing logs...")
        response = db.client.table("parsing_log").delete().neq("id", "").execute()
        logs_deleted = len(response.data) if response.data else 0
        logger.info(f"✅ Deleted {logs_deleted} parsing logs")
        
        logger.info("🎯 Database cleanup completed successfully!")
        logger.info("💡 Next RSS loader run will process all articles from scratch")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise

def main():
    """Main function with confirmation prompt."""
    print("🚨 WARNING: This will delete ALL parsing states and logs!")
    print("This means the next RSS loader run will process ALL articles from scratch.")
    print("This could result in duplicate articles if you haven't cleared the articles table.")
    print()
    
    confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    
    if confirm.lower() == 'yes':
        clear_all_parsing_data()
    else:
        print("❌ Operation cancelled")

if __name__ == "__main__":
    main()
