from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from supabase import create_client, Client as SupabaseClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
class DatabaseConfig:
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "https://iycdbgankpmljjeosjqw.supabase.co")
        self.anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.secret_key: str = os.getenv("SUPABASE_SECRET_KEY", "")
        self.client: Optional[SupabaseClient] = None

    def get_client(self) -> SupabaseClient:
        """Initialize and return the Supabase client."""
        if not self.client:
            if not self.url or not self.secret_key:
                raise ValueError("Supabase URL and Secret Key must be set in environment variables")
            self.client = create_client(self.url, self.secret_key)
        return self.client

# Initialize database configuration
db_config = DatabaseConfig()

# Pydantic Models for type hints and validation
class Source(BaseModel):
    id: str
    name: str
    url: str
    source_type: str = "rss"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ParsingState(BaseModel):
    id: Optional[str] = None
    source_id: str
    last_article_link: Optional[str] = None
    last_parsed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ParsingLog(BaseModel):
    id: Optional[str] = None
    source_id: str
    started_at: datetime
    finished_at: datetime
    articles_fetched: int
    status: str  # 'success', 'failure', 'partial'
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

class Article(BaseModel):
    id: Optional[str] = None
    source_id: str
    title: str
    link: str
    description: str
    content: str
    pub_date: datetime
    media_info: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    
    def update_parsing_state(self, state: ParsingState) -> ParsingState:
        """Update or create parsing state for a source."""
        state_data = state.dict(exclude_unset=True, exclude_none=True)
        state_data["updated_at"] = datetime.utcnow().isoformat()
        
        if state.id:
            response = self.client.table("parsing_state") \
                .update(state_data) \
                .eq("id", state.id) \
                .execute()
        else:
            state_data["created_at"] = datetime.utcnow().isoformat()
            response = self.client.table("parsing_state") \
                .insert(state_data) \
                .execute()
        
        return ParsingState(**response.data[0])
    
    # Article operations
    def insert_article(self, article: Article) -> Article:
        """Insert or update an article."""
        article_data = article.dict(exclude_unset=True, exclude_none=True)
        article_data["updated_at"] = datetime.utcnow().isoformat()
        
        if article.id:
            response = self.client.table("articles") \
                .update(article_data) \
                .eq("id", article.id) \
                .execute()
        else:
            article_data["created_at"] = datetime.utcnow().isoformat()
            response = self.client.table("articles") \
                .upsert(article_data, on_conflict='link') \
                .execute()
        
        return Article(**response.data[0])
    
    # Logging operations
    def create_parsing_log(self, log: ParsingLog) -> ParsingLog:
        """Create a new parsing log entry."""
        log_data = log.dict(exclude_unset=True, exclude_none=True)
        log_data["created_at"] = datetime.utcnow().isoformat()
        
        response = self.client.table("parsing_log") \
            .insert(log_data) \
            .execute()
        
        return ParsingLog(**response.data[0])
