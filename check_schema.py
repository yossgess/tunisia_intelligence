import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_and_fix_schema():
    """Check and fix the database schema if needed."""
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase URL or secret key in environment variables")
            return
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Check if articles table exists and has required columns
        try:
            # This will raise an exception if the table doesn't exist
            response = supabase.table('articles').select('*').limit(1).execute()
            logger.info("Articles table exists")
            
            # Check for required columns
            if response.data and len(response.data) > 0:
                first_row = response.data[0]
                required_columns = ['id', 'title', 'url', 'source_id', 'created_at']
                missing_columns = [col for col in required_columns if col not in first_row]
                
                if missing_columns:
                    logger.warning(f"Articles table is missing required columns: {', '.join(missing_columns)}")
                    logger.info("You'll need to manually add these columns to your Supabase database")
                else:
                    logger.info("Articles table has all required columns")
            
        except Exception as e:
            logger.error(f"Error checking articles table: {e}")
            logger.info("You'll need to create the articles table in your Supabase database")
        
        # Check parsing_log table
        try:
            response = supabase.table('parsing_log').select('*').limit(1).execute()
            logger.info("Parsing log table exists")
        except Exception as e:
            logger.error(f"Error checking parsing_log table: {e}")
            logger.info("You'll need to create the parsing_log table in your Supabase database")
        
    except Exception as e:
        logger.error(f"Error checking database schema: {e}")

if __name__ == "__main__":
    check_and_fix_schema()
