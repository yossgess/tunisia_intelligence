from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from supabase import create_client, Client as SupabaseClient
import os
from dotenv import load_dotenv
import logging
import sys

# Import our secret management system
from .secrets import get_secret

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Database Configuration
class DatabaseConfig:
    def __init__(self):
        # Use secret management system for sensitive data
        self.url: str = get_secret("SUPABASE_URL", "https://iycdbgankpmljjeosjqw.supabase.co")
        self.anon_key: str = get_secret("SUPABASE_ANON_KEY", "")
        self.secret_key: str = get_secret("SUPABASE_SECRET_KEY", "")
        self.client: Optional[SupabaseClient] = None

    def get_client(self) -> SupabaseClient:
        """Initialize and return the Supabase client."""
        if not self.client:
            if not self.url or not self.secret_key:
                raise ValueError("Supabase URL and Secret Key must be set in environment variables or secret store")
            self.client = create_client(self.url, self.secret_key)
            logger.info("Supabase client initialized successfully")
        return self.client

# Initialize database configuration
db_config = DatabaseConfig()

# Pydantic Models for type hints and validation
class Source(BaseModel):
    id: Union[str, int]  # Handle both string and integer IDs
    name: str
    url: str
    source_type: str = "rss"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Enable ORM mode for Pydantic v2
        
    def __hash__(self):
        return hash(str(self.id))  # Ensure hashable for dict/set operations

class ParsingState(BaseModel):
    source_id: int
    last_parsed_at: Optional[datetime] = None
    last_article_link: Optional[str] = None
    last_article_guid: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ParsingLog(BaseModel):
    id: Optional[int] = None
    source_id: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    articles_fetched: int = 0
    status: str = 'success'  # 'success', 'failure', 'partial'
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class Article(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    link: str  # Keep as 'link' to match database schema
    pub_date: Optional[datetime] = None
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_id: Optional[int] = None
    guid: Optional[str] = None  # Add guid field from schema
    # Content hash for deduplication
    content_hash: Optional[str] = None
    # AI enrichment fields (these are in separate tables in the new schema)
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    keywords: Optional[str] = None
    summary: Optional[str] = None
    category_id: Optional[int] = None
    # Vector embedding for semantic search
    embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True

# Database Operations
class DatabaseManager:
    def __init__(self):
        self.client = db_config.get_client()
    
    # Source operations
    def get_sources(self) -> List[Source]:
        """Fetch all RSS sources from the database."""
        response = self.client.table("sources") \
            .select("*") \
            .eq("source_type", "rss") \
            .execute()
        return [Source(**item) for item in response.data]
    
    # Parsing state operations
    def get_parsing_state(self, source_id: str) -> Optional[ParsingState]:
        """Get the parsing state for a source."""
        response = self.client.table("parsing_state") \
            .select("*") \
            .eq("source_id", source_id) \
            .execute()
        return ParsingState(**response.data[0]) if response.data else None
    
    def update_parsing_state(self, state: ParsingState) -> Optional[ParsingState]:
        """Update or create parsing state for a source."""
        try:
            state_data = state.dict(exclude_unset=True, exclude_none=True)
            
            # Convert datetime objects to ISO format strings
            for field in ['last_parsed_at']:
                if field in state_data and state_data[field] is not None:
                    if hasattr(state_data[field], 'isoformat'):
                        state_data[field] = state_data[field].isoformat()
            
            # Remove fields that might not exist in the database
            state_data.pop('updated_at', None)
            
            # Check if a record exists for this source_id
            existing = self.client.table("parsing_state") \
                .select("*") \
                .eq("source_id", state.source_id) \
                .execute()
            
            if existing.data:
                # Update existing record
                response = self.client.table("parsing_state") \
                    .update(state_data) \
                    .eq("source_id", state.source_id) \
                    .execute()
            else:
                # Insert new record
                response = self.client.table("parsing_state") \
                    .insert(state_data) \
                    .execute()
            
            return ParsingState(**response.data[0]) if response.data else None
            
        except Exception as e:
            logger.error(f"Error updating parsing state: {e}", exc_info=True)
            return None
    
    # Article operations
    def insert_article(self, article: Article) -> Optional[Article]:
        """Insert or update an article."""
        try:
            article_data = article.dict(exclude_unset=True, exclude_none=True)
            
            # Handle media_info -> media_url conversion if needed
            if 'media_info' in article_data:
                if article_data['media_info'] and 'url' in article_data['media_info']:
                    article_data['media_url'] = article_data['media_info']['url']
                del article_data['media_info']
            
            # Convert datetime objects to ISO format strings
            for field in ['pub_date', 'created_at']:
                if field in article_data and article_data[field] is not None:
                    if hasattr(article_data[field], 'isoformat'):
                        article_data[field] = article_data[field].isoformat()
            
            # Remove fields that don't exist in the database
            article_data.pop('updated_at', None)
            
            # Ensure required fields are present
            if 'title' not in article_data or 'link' not in article_data:
                raise ValueError("Article must have title and link")
            
            # Keep 'link' as is - no mapping needed
            # The database table uses 'link' column, not 'url'
            
            # Check if article already exists by link
            existing = self.client.table("articles") \
                .select("id") \
                .eq("link", article_data['link']) \
                .limit(1) \
                .execute()
            
            if existing.data:
                # Article exists, update it
                response = self.client.table("articles") \
                    .update(article_data) \
                    .eq("link", article_data['link']) \
                    .execute()
            else:
                # Article doesn't exist, insert it
                response = self.client.table("articles") \
                    .insert(article_data) \
                    .execute()
            
            return Article(**response.data[0]) if response.data else None
            
        except Exception as e:
            # Streamlined error logging for performance
            logger.error(f"Error inserting article: {e}")
            # Only log full details in debug mode
            logger.debug(f"Article data that failed: {article_data}")
            logger.debug(f"Exception type: {type(e).__name__}")
            return None
    
    # Logging operations
    def create_parsing_log(self, log: ParsingLog) -> Optional[ParsingLog]:
        """Create a new parsing log entry."""
        try:
            log_data = log.dict(exclude_unset=True, exclude_none=True)
            
            # Convert datetime objects to ISO format strings
            for field in ['started_at', 'finished_at']:
                if field in log_data and log_data[field] is not None:
                    if hasattr(log_data[field], 'isoformat'):
                        log_data[field] = log_data[field].isoformat()
            
            # Ensure required fields have default values
            if 'status' not in log_data:
                log_data['status'] = 'success'
            if 'articles_fetched' not in log_data:
                log_data['articles_fetched'] = 0
            
            # Insert the log entry - use plural table name to match schema
            response = self.client.table("parsing_log") \
                .insert(log_data) \
                .execute()
            
            return ParsingLog(**response.data[0]) if response.data else None
            
        except Exception as e:
            logger.error(f"Error creating parsing log: {e}")
            return None
    
    # Facebook/Social Media operations
    def get_facebook_sources(self) -> List[Source]:
        """Fetch all Facebook sources from the database."""
        response = self.client.table("sources") \
            .select("*") \
            .eq("source_type", "facebook") \
            .eq("is_active", True) \
            .execute()
        return [Source(**item) for item in response.data]
    
    def insert_social_media_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a social media post."""
        try:
            # Convert datetime objects to ISO format strings
            for field in ['publish_date', 'created_at', 'updated_at']:
                if field in post_data and post_data[field] is not None:
                    if hasattr(post_data[field], 'isoformat'):
                        post_data[field] = post_data[field].isoformat()
            
            response = self.client.table("social_media_posts") \
                .upsert(post_data, on_conflict='post_id') \
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error inserting social media post: {e}")
            return None
    
    def insert_social_media_reactions(self, reactions_data: List[Dict[str, Any]]) -> bool:
        """Insert social media post reactions."""
        try:
            if not reactions_data:
                return True
                
            response = self.client.table("social_media_post_reactions") \
                .upsert(reactions_data, on_conflict='post_id,reaction_type') \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error inserting social media reactions: {e}")
            return False
    
    def insert_social_media_comments(self, comments_data: List[Dict[str, Any]]) -> bool:
        """Insert social media comments."""
        try:
            if not comments_data:
                return True
            
            # Convert datetime objects to ISO format strings
            for comment in comments_data:
                for field in ['created_time', 'created_at', 'updated_at']:
                    if field in comment and comment[field] is not None:
                        if hasattr(comment[field], 'isoformat'):
                            comment[field] = comment[field].isoformat()
            
            response = self.client.table("social_media_comments") \
                .upsert(comments_data, on_conflict='comment_id') \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error inserting social media comments: {e}")
            return False
