"""
AI Enrichment Configuration for Tunisia Intelligence System

This module provides comprehensive configuration management for AI enrichment processing,
including tunable parameters for each content type (articles, posts, comments) and
integration with the web dashboard for real-time parameter adjustment.
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import os
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Content types for AI enrichment."""
    ARTICLE = "article"
    POST = "post"
    COMMENT = "comment"


class ProcessingMode(str, Enum):
    """AI processing modes."""
    FULL = "full"  # All AI features enabled
    SENTIMENT_ONLY = "sentiment_only"  # Only sentiment analysis
    KEYWORDS_ONLY = "keywords_only"  # Only keyword extraction
    ENTITIES_ONLY = "entities_only"  # Only entity recognition
    CUSTOM = "custom"  # Custom feature selection


class ModelProvider(str, Enum):
    """AI model providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class ArticleEnrichmentSettings(BaseSettings):
    """Configuration settings for article enrichment."""
    
    # Processing Control
    enabled: bool = Field(True, env="AI_ARTICLES_ENABLED", description="Enable article enrichment")
    processing_mode: ProcessingMode = Field(ProcessingMode.FULL, env="AI_ARTICLES_MODE", description="Article processing mode")
    
    # Batch Processing
    batch_size: int = Field(10, env="AI_ARTICLES_BATCH_SIZE", description="Articles per batch")
    max_items_per_run: int = Field(100, env="AI_ARTICLES_MAX_PER_RUN", description="Max articles per run")
    processing_priority: int = Field(1, env="AI_ARTICLES_PRIORITY", description="Processing priority (1-10)")
    
    # Feature Toggles
    enable_sentiment: bool = Field(True, env="AI_ARTICLES_SENTIMENT", description="Enable sentiment analysis")
    enable_keywords: bool = Field(True, env="AI_ARTICLES_KEYWORDS", description="Enable keyword extraction")
    enable_entities: bool = Field(True, env="AI_ARTICLES_ENTITIES", description="Enable entity recognition")
    enable_categories: bool = Field(True, env="AI_ARTICLES_CATEGORIES", description="Enable category classification")
    enable_summary: bool = Field(True, env="AI_ARTICLES_SUMMARY", description="Enable summary generation")
    enable_translation: bool = Field(True, env="AI_ARTICLES_TRANSLATION", description="Enable translation")
    
    # Quality Control
    min_content_length: int = Field(100, env="AI_ARTICLES_MIN_LENGTH", description="Minimum content length")
    max_content_length: int = Field(50000, env="AI_ARTICLES_MAX_LENGTH", description="Maximum content length")
    min_confidence_threshold: float = Field(0.7, env="AI_ARTICLES_MIN_CONFIDENCE", description="Minimum confidence threshold")
    
    # Processing Limits
    max_processing_time_seconds: int = Field(60, env="AI_ARTICLES_MAX_TIME", description="Max processing time per article")
    max_retries: int = Field(3, env="AI_ARTICLES_MAX_RETRIES", description="Max retry attempts")
    retry_delay_seconds: float = Field(5.0, env="AI_ARTICLES_RETRY_DELAY", description="Delay between retries")
    
    # Output Configuration
    max_keywords: int = Field(10, env="AI_ARTICLES_MAX_KEYWORDS", description="Maximum keywords to extract")
    max_entities: int = Field(15, env="AI_ARTICLES_MAX_ENTITIES", description="Maximum entities to extract")
    summary_max_length: int = Field(500, env="AI_ARTICLES_SUMMARY_LENGTH", description="Maximum summary length")
    
    # Language Configuration
    source_languages: List[str] = Field(["ar", "fr", "en"], env="AI_ARTICLES_SOURCE_LANGS", description="Supported source languages")
    target_language: str = Field("fr", env="AI_ARTICLES_TARGET_LANG", description="Target language for processing")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Article batch size must be between 1 and 100')
        return v
    
    @validator('min_confidence_threshold')
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v


class PostEnrichmentSettings(BaseSettings):
    """Configuration settings for social media post enrichment."""
    
    # Processing Control
    enabled: bool = Field(True, env="AI_POSTS_ENABLED", description="Enable post enrichment")
    processing_mode: ProcessingMode = Field(ProcessingMode.FULL, env="AI_POSTS_MODE", description="Post processing mode")
    
    # Batch Processing
    batch_size: int = Field(15, env="AI_POSTS_BATCH_SIZE", description="Posts per batch")
    max_items_per_run: int = Field(200, env="AI_POSTS_MAX_PER_RUN", description="Max posts per run")
    processing_priority: int = Field(2, env="AI_POSTS_PRIORITY", description="Processing priority (1-10)")
    
    # Feature Toggles
    enable_sentiment: bool = Field(True, env="AI_POSTS_SENTIMENT", description="Enable sentiment analysis")
    enable_keywords: bool = Field(True, env="AI_POSTS_KEYWORDS", description="Enable keyword extraction")
    enable_entities: bool = Field(True, env="AI_POSTS_ENTITIES", description="Enable entity recognition")
    enable_categories: bool = Field(True, env="AI_POSTS_CATEGORIES", description="Enable category classification")
    enable_summary: bool = Field(True, env="AI_POSTS_SUMMARY", description="Enable summary generation")
    enable_translation: bool = Field(True, env="AI_POSTS_TRANSLATION", description="Enable translation")
    
    # Quality Control
    min_content_length: int = Field(20, env="AI_POSTS_MIN_LENGTH", description="Minimum content length")
    max_content_length: int = Field(10000, env="AI_POSTS_MAX_LENGTH", description="Maximum content length")
    min_confidence_threshold: float = Field(0.6, env="AI_POSTS_MIN_CONFIDENCE", description="Minimum confidence threshold")
    
    # Processing Limits
    max_processing_time_seconds: int = Field(45, env="AI_POSTS_MAX_TIME", description="Max processing time per post")
    max_retries: int = Field(3, env="AI_POSTS_MAX_RETRIES", description="Max retry attempts")
    retry_delay_seconds: float = Field(3.0, env="AI_POSTS_RETRY_DELAY", description="Delay between retries")
    
    # Output Configuration
    max_keywords: int = Field(8, env="AI_POSTS_MAX_KEYWORDS", description="Maximum keywords to extract")
    max_entities: int = Field(10, env="AI_POSTS_MAX_ENTITIES", description="Maximum entities to extract")
    summary_max_length: int = Field(300, env="AI_POSTS_SUMMARY_LENGTH", description="Maximum summary length")
    
    # Social Media Specific
    min_engagement_threshold: int = Field(0, env="AI_POSTS_MIN_ENGAGEMENT", description="Minimum engagement for processing")
    process_hashtags: bool = Field(True, env="AI_POSTS_HASHTAGS", description="Process hashtags as keywords")
    process_mentions: bool = Field(True, env="AI_POSTS_MENTIONS", description="Process mentions as entities")
    
    # Language Configuration
    source_languages: List[str] = Field(["ar", "fr", "en"], env="AI_POSTS_SOURCE_LANGS", description="Supported source languages")
    target_language: str = Field("fr", env="AI_POSTS_TARGET_LANG", description="Target language for processing")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Post batch size must be between 1 and 50')
        return v


class CommentEnrichmentSettings(BaseSettings):
    """Configuration settings for comment enrichment."""
    
    # Processing Control
    enabled: bool = Field(True, env="AI_COMMENTS_ENABLED", description="Enable comment enrichment")
    processing_mode: ProcessingMode = Field(ProcessingMode.SENTIMENT_ONLY, env="AI_COMMENTS_MODE", description="Comment processing mode")
    
    # Batch Processing
    batch_size: int = Field(25, env="AI_COMMENTS_BATCH_SIZE", description="Comments per batch")
    max_items_per_run: int = Field(500, env="AI_COMMENTS_MAX_PER_RUN", description="Max comments per run")
    processing_priority: int = Field(3, env="AI_COMMENTS_PRIORITY", description="Processing priority (1-10)")
    
    # Feature Toggles
    enable_sentiment: bool = Field(True, env="AI_COMMENTS_SENTIMENT", description="Enable sentiment analysis")
    enable_keywords: bool = Field(False, env="AI_COMMENTS_KEYWORDS", description="Enable keyword extraction")
    enable_entities: bool = Field(False, env="AI_COMMENTS_ENTITIES", description="Enable entity recognition")
    enable_categories: bool = Field(False, env="AI_COMMENTS_CATEGORIES", description="Enable category classification")
    enable_summary: bool = Field(False, env="AI_COMMENTS_SUMMARY", description="Enable summary generation")
    enable_translation: bool = Field(True, env="AI_COMMENTS_TRANSLATION", description="Enable translation")
    
    # Enhanced Processing (when enabled)
    enable_enhanced_processing: bool = Field(False, env="AI_COMMENTS_ENHANCED", description="Enable enhanced comment processing")
    enhanced_keywords: bool = Field(True, env="AI_COMMENTS_ENHANCED_KEYWORDS", description="Enhanced keyword extraction")
    enhanced_entities: bool = Field(True, env="AI_COMMENTS_ENHANCED_ENTITIES", description="Enhanced entity recognition")
    bilingual_output: bool = Field(True, env="AI_COMMENTS_BILINGUAL", description="Bilingual keyword/entity output")
    
    # Quality Control
    min_content_length: int = Field(10, env="AI_COMMENTS_MIN_LENGTH", description="Minimum content length")
    max_content_length: int = Field(2000, env="AI_COMMENTS_MAX_LENGTH", description="Maximum content length")
    min_confidence_threshold: float = Field(0.5, env="AI_COMMENTS_MIN_CONFIDENCE", description="Minimum confidence threshold")
    
    # Processing Limits
    max_processing_time_seconds: int = Field(30, env="AI_COMMENTS_MAX_TIME", description="Max processing time per comment")
    max_retries: int = Field(2, env="AI_COMMENTS_MAX_RETRIES", description="Max retry attempts")
    retry_delay_seconds: float = Field(2.0, env="AI_COMMENTS_RETRY_DELAY", description="Delay between retries")
    
    # Output Configuration
    max_keywords: int = Field(5, env="AI_COMMENTS_MAX_KEYWORDS", description="Maximum keywords to extract")
    max_entities: int = Field(5, env="AI_COMMENTS_MAX_ENTITIES", description="Maximum entities to extract")
    
    # Comment Specific
    min_relevance_score: float = Field(0.3, env="AI_COMMENTS_MIN_RELEVANCE", description="Minimum relevance score")
    filter_spam: bool = Field(True, env="AI_COMMENTS_FILTER_SPAM", description="Filter spam comments")
    filter_offensive: bool = Field(True, env="AI_COMMENTS_FILTER_OFFENSIVE", description="Filter offensive comments")
    
    # Language Configuration
    source_languages: List[str] = Field(["ar", "fr", "en"], env="AI_COMMENTS_SOURCE_LANGS", description="Supported source languages")
    target_language: str = Field("fr", env="AI_COMMENTS_TARGET_LANG", description="Target language for processing")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Comment batch size must be between 1 and 100')
        return v


class ModelSettings(BaseSettings):
    """AI model configuration settings."""
    
    # Primary Model Configuration
    provider: ModelProvider = Field(ModelProvider.OLLAMA, env="AI_MODEL_PROVIDER", description="AI model provider")
    model_name: str = Field("qwen2.5:7b", env="AI_MODEL_NAME", description="Primary AI model name")
    model_version: str = Field("1.0", env="AI_MODEL_VERSION", description="Model version")
    
    # Ollama Configuration
    ollama_url: str = Field("http://localhost:11434", env="OLLAMA_URL", description="Ollama server URL")
    ollama_timeout: int = Field(120, env="OLLAMA_TIMEOUT", description="Ollama request timeout")
    
    # Model Parameters
    temperature: float = Field(0.3, env="AI_MODEL_TEMPERATURE", description="Model temperature")
    max_tokens: int = Field(1024, env="AI_MODEL_MAX_TOKENS", description="Maximum tokens per request")
    top_p: float = Field(0.9, env="AI_MODEL_TOP_P", description="Top-p sampling parameter")
    frequency_penalty: float = Field(0.0, env="AI_MODEL_FREQ_PENALTY", description="Frequency penalty")
    presence_penalty: float = Field(0.0, env="AI_MODEL_PRESENCE_PENALTY", description="Presence penalty")
    
    # Fallback Models
    enable_fallback: bool = Field(True, env="AI_ENABLE_FALLBACK", description="Enable fallback models")
    fallback_models: List[str] = Field(["llama2:7b", "mistral:7b"], env="AI_FALLBACK_MODELS", description="Fallback model list")
    
    # Performance Settings
    max_concurrent_requests: int = Field(3, env="AI_MAX_CONCURRENT", description="Max concurrent model requests")
    request_queue_size: int = Field(100, env="AI_REQUEST_QUEUE_SIZE", description="Request queue size")
    enable_caching: bool = Field(True, env="AI_ENABLE_CACHING", description="Enable response caching")
    cache_ttl_minutes: int = Field(60, env="AI_CACHE_TTL", description="Cache TTL in minutes")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0.0 or v > 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v


class RateLimitingSettings(BaseSettings):
    """Rate limiting configuration for AI processing."""
    
    # Global Rate Limits
    requests_per_minute: int = Field(20, env="AI_REQUESTS_PER_MINUTE", description="Global requests per minute")
    requests_per_hour: int = Field(1000, env="AI_REQUESTS_PER_HOUR", description="Global requests per hour")
    requests_per_day: int = Field(10000, env="AI_REQUESTS_PER_DAY", description="Global requests per day")
    
    # Content Type Specific Limits
    articles_per_minute: int = Field(5, env="AI_ARTICLES_PER_MINUTE", description="Articles per minute")
    posts_per_minute: int = Field(8, env="AI_POSTS_PER_MINUTE", description="Posts per minute")
    comments_per_minute: int = Field(15, env="AI_COMMENTS_PER_MINUTE", description="Comments per minute")
    
    # Delay Configuration
    base_delay_seconds: float = Field(3.0, env="AI_BASE_DELAY", description="Base delay between requests")
    adaptive_delay: bool = Field(True, env="AI_ADAPTIVE_DELAY", description="Enable adaptive delay based on response time")
    max_delay_seconds: float = Field(30.0, env="AI_MAX_DELAY", description="Maximum delay between requests")
    
    # Burst Control
    enable_burst_protection: bool = Field(True, env="AI_BURST_PROTECTION", description="Enable burst protection")
    burst_threshold: int = Field(10, env="AI_BURST_THRESHOLD", description="Burst threshold")
    burst_cooldown_seconds: int = Field(60, env="AI_BURST_COOLDOWN", description="Burst cooldown period")
    
    @validator('requests_per_minute')
    def validate_rpm(cls, v):
        if v < 1 or v > 300:
            raise ValueError('Requests per minute must be between 1 and 300')
        return v


class QualityControlSettings(BaseSettings):
    """Quality control and validation settings."""
    
    # Content Validation
    enable_content_validation: bool = Field(True, env="AI_CONTENT_VALIDATION", description="Enable content validation")
    enable_language_detection: bool = Field(True, env="AI_LANGUAGE_DETECTION", description="Enable language detection")
    enable_content_filtering: bool = Field(True, env="AI_CONTENT_FILTERING", description="Enable content filtering")
    
    # Response Validation
    enable_response_validation: bool = Field(True, env="AI_RESPONSE_VALIDATION", description="Enable AI response validation")
    require_valid_json: bool = Field(True, env="AI_REQUIRE_VALID_JSON", description="Require valid JSON responses")
    validate_sentiment_values: bool = Field(True, env="AI_VALIDATE_SENTIMENT", description="Validate sentiment values")
    validate_confidence_scores: bool = Field(True, env="AI_VALIDATE_CONFIDENCE", description="Validate confidence scores")
    
    # Quality Thresholds
    min_response_quality_score: float = Field(0.5, env="AI_MIN_QUALITY_SCORE", description="Minimum response quality score")
    max_processing_failures: int = Field(5, env="AI_MAX_FAILURES", description="Max consecutive processing failures")
    
    # Error Handling
    enable_graceful_degradation: bool = Field(True, env="AI_GRACEFUL_DEGRADATION", description="Enable graceful degradation")
    fallback_to_simple_processing: bool = Field(True, env="AI_FALLBACK_SIMPLE", description="Fallback to simple processing")
    log_failed_requests: bool = Field(True, env="AI_LOG_FAILURES", description="Log failed requests")
    
    # Monitoring
    track_processing_quality: bool = Field(True, env="AI_TRACK_QUALITY", description="Track processing quality")
    quality_reporting_interval_minutes: int = Field(30, env="AI_QUALITY_REPORT_INTERVAL", description="Quality reporting interval")


class AIEnrichmentConfig(BaseSettings):
    """Main AI enrichment configuration."""
    
    # Global Settings
    enabled: bool = Field(True, env="AI_ENRICHMENT_ENABLED", description="Master enable switch for AI enrichment")
    debug_mode: bool = Field(False, env="AI_DEBUG_MODE", description="Enable debug mode")
    
    # Content Type Settings
    articles: ArticleEnrichmentSettings = ArticleEnrichmentSettings()
    posts: PostEnrichmentSettings = PostEnrichmentSettings()
    comments: CommentEnrichmentSettings = CommentEnrichmentSettings()
    
    # Model and Processing Settings
    model: ModelSettings = ModelSettings()
    rate_limiting: RateLimitingSettings = RateLimitingSettings()
    quality_control: QualityControlSettings = QualityControlSettings()
    
    # Configuration Metadata
    config_version: str = "1.0.0"
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def is_content_type_enabled(self, content_type: ContentType) -> bool:
        """Check if a specific content type is enabled for processing."""
        if not self.enabled:
            return False
        
        if content_type == ContentType.ARTICLE:
            return self.articles.enabled
        elif content_type == ContentType.POST:
            return self.posts.enabled
        elif content_type == ContentType.COMMENT:
            return self.comments.enabled
        
        return False
    
    def get_content_type_settings(self, content_type: ContentType) -> Union[ArticleEnrichmentSettings, PostEnrichmentSettings, CommentEnrichmentSettings]:
        """Get settings for a specific content type."""
        if content_type == ContentType.ARTICLE:
            return self.articles
        elif content_type == ContentType.POST:
            return self.posts
        elif content_type == ContentType.COMMENT:
            return self.comments
        
        raise ValueError(f"Unknown content type: {content_type}")
    
    def get_processing_order(self) -> List[ContentType]:
        """Get the processing order based on priority."""
        enabled_types = []
        
        if self.articles.enabled:
            enabled_types.append((ContentType.ARTICLE, self.articles.processing_priority))
        if self.posts.enabled:
            enabled_types.append((ContentType.POST, self.posts.processing_priority))
        if self.comments.enabled:
            enabled_types.append((ContentType.COMMENT, self.comments.processing_priority))
        
        # Sort by priority (lower number = higher priority)
        enabled_types.sort(key=lambda x: x[1])
        
        return [content_type for content_type, _ in enabled_types]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), BaseSettings):
                    # Handle nested settings objects
                    nested_settings = getattr(self, key)
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if hasattr(nested_settings, nested_key):
                                setattr(nested_settings, nested_key, nested_value)
                else:
                    setattr(self, key, value)
        
        self.last_updated = datetime.now()
    
    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file."""
        import json
        config_dict = self.to_dict()
        
        # Convert datetime objects to strings
        if config_dict.get('last_updated'):
            config_dict['last_updated'] = config_dict['last_updated'].isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, file_path: str) -> None:
        """Load configuration from file."""
        import json
        
        if not os.path.exists(file_path):
            logger.warning(f"Configuration file not found: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # Convert datetime strings back to datetime objects
        if config_dict.get('last_updated'):
            config_dict['last_updated'] = datetime.fromisoformat(config_dict['last_updated'])
        
        self.update_from_dict(config_dict)


# Global configuration instance
_ai_enrichment_config: Optional[AIEnrichmentConfig] = None


def get_ai_enrichment_config() -> AIEnrichmentConfig:
    """Get the global AI enrichment configuration instance."""
    global _ai_enrichment_config
    if _ai_enrichment_config is None:
        _ai_enrichment_config = AIEnrichmentConfig()
    return _ai_enrichment_config


def reload_ai_enrichment_config() -> AIEnrichmentConfig:
    """Reload AI enrichment configuration from environment variables."""
    global _ai_enrichment_config
    _ai_enrichment_config = AIEnrichmentConfig()
    return _ai_enrichment_config


# Convenience functions for content type settings
def get_article_settings() -> ArticleEnrichmentSettings:
    """Get article enrichment settings."""
    return get_ai_enrichment_config().articles


def get_post_settings() -> PostEnrichmentSettings:
    """Get post enrichment settings."""
    return get_ai_enrichment_config().posts


def get_comment_settings() -> CommentEnrichmentSettings:
    """Get comment enrichment settings."""
    return get_ai_enrichment_config().comments


def get_model_settings() -> ModelSettings:
    """Get model settings."""
    return get_ai_enrichment_config().model


def get_rate_limiting_settings() -> RateLimitingSettings:
    """Get rate limiting settings."""
    return get_ai_enrichment_config().rate_limiting


def get_quality_control_settings() -> QualityControlSettings:
    """Get quality control settings."""
    return get_ai_enrichment_config().quality_control
