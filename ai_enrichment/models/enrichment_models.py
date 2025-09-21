"""
Pydantic models for AI enrichment results.

This module defines data models for representing AI processing results
and integrating with the existing database schema.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class ProcessingStatus(str, Enum):
    """Status of AI processing operations."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    PENDING = "pending"

class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"

class KeywordType(str, Enum):
    """Keyword types."""
    SINGLE_WORD = "single_word"
    PHRASE = "phrase"
    CONCEPT = "concept"

class LanguageCode(str, Enum):
    """Supported language codes."""
    ARABIC = "ar"
    FRENCH = "fr"
    ENGLISH = "en"
    MIXED = "mixed"
    AUTO = "auto"
    UNKNOWN = "unknown"

class ProcessingMetadata(BaseModel):
    """Metadata for processing operations."""
    processor: str
    model: str
    processing_time: Optional[float] = None
    content_length: Optional[int] = None
    language_detected: Optional[LanguageCode] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True

class SentimentResult(BaseModel):
    """Result model for sentiment analysis."""
    sentiment: SentimentLabel
    sentiment_score: int = Field(..., ge=-1, le=1)  # -1: negative, 0: neutral, 1: positive
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    emotions: List[str] = Field(default_factory=list)
    language_detected: Optional[LanguageCode] = None
    
    # Database integration fields
    sentiment_id: Optional[int] = None  # Links to sentiments table
    
    class Config:
        use_enum_values = True
    
    @validator('sentiment_score')
    def validate_sentiment_score(cls, v, values):
        """Validate sentiment score matches sentiment label."""
        sentiment = values.get('sentiment')
        if sentiment == SentimentLabel.POSITIVE and v != 1:
            return 1
        elif sentiment == SentimentLabel.NEGATIVE and v != -1:
            return -1
        elif sentiment == SentimentLabel.NEUTRAL and v != 0:
            return 0
        return v

class EntityResult(BaseModel):
    """Result model for named entity recognition."""
    text: str
    type: EntityType
    confidence: float = Field(..., ge=0.0, le=1.0)
    canonical_name: Optional[str] = None
    context: Optional[str] = None
    is_tunisian: bool = False
    
    # Database integration fields
    entity_id: Optional[int] = None  # Links to entities table
    mention_id: Optional[int] = None  # Links to entity_mentions table
    
    class Config:
        use_enum_values = True

class KeywordResult(BaseModel):
    """Result model for keyword extraction."""
    text: str
    type: KeywordType = KeywordType.SINGLE_WORD
    importance: float = Field(..., ge=0.0, le=1.0)
    frequency: int = Field(default=1, ge=1)
    category: str = "other"
    is_phrase: bool = False
    language: Optional[LanguageCode] = None
    
    # Database integration fields
    keyword_id: Optional[int] = None  # Links to keywords table
    
    class Config:
        use_enum_values = True

class CategoryResult(BaseModel):
    """Result model for category classification."""
    primary_category: str
    secondary_categories: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    subcategories: List[str] = Field(default_factory=list)
    category_path: Optional[str] = None
    
    # Database integration fields
    category_id: Optional[int] = None  # Links to categories table
    secondary_category_ids: List[int] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True

class EnrichmentResult(BaseModel):
    """Complete AI enrichment result for a piece of content."""
    content_id: Optional[int] = None  # ID of the source content (article, post, etc.)
    content_type: str  # 'article', 'social_media_post', 'comment', 'report'
    
    # AI processing results
    sentiment: Optional[SentimentResult] = None
    entities: List[EntityResult] = Field(default_factory=list)
    keywords: List[KeywordResult] = Field(default_factory=list)
    category: Optional[CategoryResult] = None
    
    # Processing metadata
    status: ProcessingStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[ProcessingMetadata] = None
    
    # Summary fields
    summary: Optional[str] = None
    language_detected: Optional[LanguageCode] = None
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    @validator('confidence')
    def calculate_overall_confidence(cls, v, values):
        """Calculate overall confidence from individual components."""
        confidences = []
        
        if values.get('sentiment'):
            confidences.append(values['sentiment'].confidence)
        
        if values.get('category'):
            confidences.append(values['category'].confidence)
        
        entities = values.get('entities', [])
        if entities:
            entity_confidences = [e.confidence for e in entities]
            confidences.append(sum(entity_confidences) / len(entity_confidences))
        
        keywords = values.get('keywords', [])
        if keywords:
            keyword_confidences = [k.importance for k in keywords]
            confidences.append(sum(keyword_confidences) / len(keyword_confidences))
        
        if confidences:
            return sum(confidences) / len(confidences)
        
        return v

class ProcessingResult(BaseModel):
    """Generic result model for individual processing tasks."""
    task_name: str
    status: ProcessingStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    confidence: Optional[float] = None
    
    class Config:
        use_enum_values = True

class BatchProcessingResult(BaseModel):
    """Result model for batch processing operations."""
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    skipped_items: int
    
    # Processing statistics
    success_rate: float = Field(..., ge=0.0, le=1.0)
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    average_processing_time: Optional[float] = None
    
    # Results breakdown
    sentiment_results: int = 0
    entity_results: int = 0
    keyword_results: int = 0
    category_results: int = 0
    
    # Timestamps
    started_at: datetime
    completed_at: datetime
    total_processing_time: float
    
    # Error summary
    error_summary: Dict[str, int] = Field(default_factory=dict)
    
    @validator('success_rate')
    def calculate_success_rate(cls, v, values):
        """Calculate success rate from processed items."""
        total = values.get('total_items', 0)
        successful = values.get('successful_items', 0)
        return successful / total if total > 0 else 0.0

# Database integration models extending existing models
class EnrichedArticle(BaseModel):
    """Extended article model with AI enrichment."""
    # Original article fields (from existing Article model)
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    link: str
    pub_date: Optional[datetime] = None
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None
    content: Optional[str] = None
    source_id: Optional[int] = None
    
    # AI enrichment fields (matching news_articles table schema)
    sentiment: Optional[str] = None  # Populated from sentiment analysis
    sentiment_score: Optional[float] = None  # New field in optimized schema
    keywords: Optional[str] = None  # JSON string of keywords
    summary: Optional[str] = None
    category_id: Optional[int] = None  # Links to categories table
    content_hash: Optional[str] = None  # Content deduplication hash
    embedding: Optional[str] = None  # Vector embedding for similarity search
    
    # Enrichment metadata
    enrichment_status: Optional[ProcessingStatus] = None
    enriched_at: Optional[datetime] = None
    enrichment_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True

class EnrichedSocialMediaPost(BaseModel):
    """Extended social media post model with AI enrichment."""
    # Original post fields
    id: Optional[int] = None
    social_media: str
    account: str
    content: Optional[str] = None
    publish_date: Optional[datetime] = None
    category_id: Optional[int] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # AI enrichment fields
    summary: Optional[str] = None
    sentiment_id: Optional[int] = None
    sentiment_score: Optional[float] = None
    
    # Enrichment metadata
    enrichment_status: Optional[ProcessingStatus] = None
    enriched_at: Optional[datetime] = None
    enrichment_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True

class EnrichedComment(BaseModel):
    """Extended comment model with AI enrichment."""
    # Original comment fields
    id: Optional[int] = None
    post_id: int
    comment_date: Optional[datetime] = None
    content: str
    relevance: bool = False
    
    # AI enrichment fields
    sentiment_id: Optional[int] = None
    sentiment_score: Optional[float] = None
    
    # Enrichment metadata
    enrichment_status: Optional[ProcessingStatus] = None
    enriched_at: Optional[datetime] = None
    enrichment_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True

# Utility models for API responses
class EnrichmentRequest(BaseModel):
    """Request model for AI enrichment API."""
    content: str
    content_type: str = "article"  # 'article', 'social_media_post', 'comment'
    content_id: Optional[int] = None
    
    # Processing options
    enable_sentiment: bool = True
    enable_entities: bool = True
    enable_keywords: bool = True
    enable_categories: bool = True
    enable_summary: bool = False
    
    # Language hint
    language: Optional[LanguageCode] = LanguageCode.AUTO
    
    class Config:
        use_enum_values = True

class EnrichmentResponse(BaseModel):
    """Response model for AI enrichment API."""
    request_id: Optional[str] = None
    status: ProcessingStatus
    result: Optional[EnrichmentResult] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    
    class Config:
        use_enum_values = True
