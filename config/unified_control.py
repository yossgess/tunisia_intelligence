"""
Unified Control Configuration for Tunisia Intelligence System

This module provides centralized configuration and control for all processing pipelines:
- RSS Extraction and Loading
- Facebook Extraction and Loading  
- AI Enrichment Processing
- Vectorization Processing

All pipeline parameters, rate limits, batch sizes, and processing controls are managed here.
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Any
from enum import Enum
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    """Pipeline execution modes."""
    DISABLED = "disabled"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    CONTINUOUS = "continuous"
    BATCH = "batch"


class ProcessingPriority(Enum):
    """Processing priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RSSControlSettings(BaseSettings):
    """RSS extraction and loading control settings."""
    
    # Pipeline Control
    enabled: bool = Field(True, env="RSS_ENABLED", description="Enable RSS pipeline")
    mode: PipelineMode = Field(PipelineMode.SCHEDULED, env="RSS_MODE", description="RSS pipeline mode")
    
    # Rate Limiting
    requests_per_minute: int = Field(30, env="RSS_REQUESTS_PER_MINUTE", description="Max requests per minute")
    requests_per_hour: int = Field(1000, env="RSS_REQUESTS_PER_HOUR", description="Max requests per hour")
    delay_between_sources: float = Field(2.0, env="RSS_DELAY_BETWEEN_SOURCES", description="Delay between sources (seconds)")
    delay_between_articles: float = Field(0.5, env="RSS_DELAY_BETWEEN_ARTICLES", description="Delay between articles (seconds)")
    
    # Batch Processing
    batch_size: int = Field(50, env="RSS_BATCH_SIZE", description="Articles per batch")
    max_articles_per_source: int = Field(100, env="RSS_MAX_ARTICLES_PER_SOURCE", description="Max articles per source per run")
    max_sources_per_run: int = Field(10, env="RSS_MAX_SOURCES_PER_RUN", description="Max sources per run")
    
    # Processing Limits
    max_retries: int = Field(3, env="RSS_MAX_RETRIES", description="Max retry attempts")
    timeout_seconds: int = Field(60, env="RSS_TIMEOUT", description="Request timeout")
    max_workers: int = Field(5, env="RSS_MAX_WORKERS", description="Max worker threads")
    
    # Content Filtering
    min_content_length: int = Field(100, env="RSS_MIN_CONTENT_LENGTH", description="Minimum content length")
    max_content_length: int = Field(50000, env="RSS_MAX_CONTENT_LENGTH", description="Maximum content length")
    skip_duplicates: bool = Field(True, env="RSS_SKIP_DUPLICATES", description="Skip duplicate articles")
    
    # Scheduling
    schedule_interval_minutes: int = Field(60, env="RSS_SCHEDULE_INTERVAL", description="Schedule interval in minutes")
    priority_sources_interval_minutes: int = Field(30, env="RSS_PRIORITY_INTERVAL", description="Priority sources interval")
    
    # Quality Control
    enable_content_validation: bool = Field(True, env="RSS_ENABLE_VALIDATION", description="Enable content validation")
    enable_language_detection: bool = Field(True, env="RSS_ENABLE_LANG_DETECTION", description="Enable language detection")
    
    @validator('requests_per_minute')
    def validate_rpm(cls, v):
        if v < 1 or v > 300:
            raise ValueError('Requests per minute must be between 1 and 300')
        return v


class FacebookControlSettings(BaseSettings):
    """Facebook extraction and loading control settings."""
    
    # Pipeline Control
    enabled: bool = Field(True, env="FACEBOOK_ENABLED", description="Enable Facebook pipeline")
    mode: PipelineMode = Field(PipelineMode.SCHEDULED, env="FACEBOOK_MODE", description="Facebook pipeline mode")
    
    # API Rate Limiting (Facebook specific)
    api_calls_per_hour: int = Field(200, env="FACEBOOK_API_CALLS_PER_HOUR", description="Max API calls per hour")
    api_calls_per_day: int = Field(2000, env="FACEBOOK_API_CALLS_PER_DAY", description="Max API calls per day")
    delay_between_pages: float = Field(1.0, env="FACEBOOK_DELAY_BETWEEN_PAGES", description="Delay between pages (seconds)")
    delay_between_batches: float = Field(30.0, env="FACEBOOK_DELAY_BETWEEN_BATCHES", description="Delay between batches (seconds)")
    
    # Batch Processing
    pages_per_batch: int = Field(10, env="FACEBOOK_PAGES_PER_BATCH", description="Pages per batch")
    max_posts_per_page: int = Field(50, env="FACEBOOK_MAX_POSTS_PER_PAGE", description="Max posts per page per run")
    max_comments_per_post: int = Field(20, env="FACEBOOK_MAX_COMMENTS_PER_POST", description="Max comments per post")
    
    # Processing Limits
    max_retries: int = Field(3, env="FACEBOOK_MAX_RETRIES", description="Max retry attempts")
    timeout_seconds: int = Field(30, env="FACEBOOK_TIMEOUT", description="Request timeout")
    api_version: str = Field("v18.0", env="FACEBOOK_API_VERSION", description="Facebook API version")
    
    # Content Filtering
    min_engagement_threshold: int = Field(5, env="FACEBOOK_MIN_ENGAGEMENT", description="Minimum engagement for posts")
    skip_low_quality_posts: bool = Field(True, env="FACEBOOK_SKIP_LOW_QUALITY", description="Skip low quality posts")
    process_comments: bool = Field(True, env="FACEBOOK_PROCESS_COMMENTS", description="Process post comments")
    
    # Scheduling
    schedule_interval_minutes: int = Field(120, env="FACEBOOK_SCHEDULE_INTERVAL", description="Schedule interval in minutes")
    priority_pages_interval_minutes: int = Field(60, env="FACEBOOK_PRIORITY_INTERVAL", description="Priority pages interval")
    
    # Data Collection
    collect_reactions: bool = Field(True, env="FACEBOOK_COLLECT_REACTIONS", description="Collect post reactions")
    collect_shares: bool = Field(True, env="FACEBOOK_COLLECT_SHARES", description="Collect share counts")
    hours_back: int = Field(168, env="FACEBOOK_HOURS_BACK", description="Hours back to fetch posts (default: 7 days)")
    collect_page_info: bool = Field(True, env="FACEBOOK_COLLECT_PAGE_INFO", description="Collect page information")
    
    @validator('api_calls_per_hour')
    def validate_api_calls(cls, v):
        if v < 10 or v > 1000:
            raise ValueError('API calls per hour must be between 10 and 1000')
        return v


class AIEnrichmentControlSettings(BaseSettings):
    """AI enrichment processing control settings - Legacy wrapper for new AI config system."""
    
    # Pipeline Control
    enabled: bool = Field(True, env="AI_ENRICHMENT_ENABLED", description="Enable AI enrichment pipeline")
    mode: PipelineMode = Field(PipelineMode.BATCH, env="AI_ENRICHMENT_MODE", description="AI enrichment mode")
    
    # Model Configuration (maintained for backward compatibility)
    ollama_url: str = Field("http://localhost:11434", env="OLLAMA_URL", description="Ollama server URL")
    model_name: str = Field("qwen2.5:7b", env="AI_MODEL_NAME", description="AI model name")
    model_temperature: float = Field(0.1, env="AI_MODEL_TEMPERATURE", description="Model temperature")
    max_tokens: int = Field(1024, env="AI_MAX_TOKENS", description="Max tokens per request")
    
    # Processing Limits (maintained for backward compatibility)
    batch_size: int = Field(10, env="AI_BATCH_SIZE", description="Items per batch")
    max_items_per_run: int = Field(100, env="AI_MAX_ITEMS_PER_RUN", description="Max items per run")
    max_concurrent_requests: int = Field(3, env="AI_MAX_CONCURRENT", description="Max concurrent AI requests")
    
    # Rate Limiting
    requests_per_minute: int = Field(20, env="AI_REQUESTS_PER_MINUTE", description="Max AI requests per minute")
    delay_between_requests: float = Field(3.0, env="AI_DELAY_BETWEEN_REQUESTS", description="Delay between requests")
    
    # Processing Configuration
    process_articles: bool = Field(True, env="AI_PROCESS_ARTICLES", description="Process articles")
    process_posts: bool = Field(True, env="AI_PROCESS_POSTS", description="Process social media posts")
    process_comments: bool = Field(True, env="AI_PROCESS_COMMENTS", description="Process comments")
    
    # Feature Toggles
    enable_sentiment_analysis: bool = Field(True, env="AI_ENABLE_SENTIMENT", description="Enable sentiment analysis")
    enable_keyword_extraction: bool = Field(True, env="AI_ENABLE_KEYWORDS", description="Enable keyword extraction")
    enable_entity_recognition: bool = Field(True, env="AI_ENABLE_NER", description="Enable named entity recognition")
    enable_category_detection: bool = Field(True, env="AI_ENABLE_CATEGORIES", description="Enable category detection")
    enable_translation: bool = Field(True, env="AI_ENABLE_TRANSLATION", description="Enable translation")
    
    # Quality Control
    min_confidence_threshold: float = Field(0.7, env="AI_MIN_CONFIDENCE", description="Minimum confidence threshold")
    max_processing_time_seconds: int = Field(60, env="AI_MAX_PROCESSING_TIME", description="Max processing time per item")
    enable_fallback_processing: bool = Field(True, env="AI_ENABLE_FALLBACK", description="Enable fallback processing")
    
    # Retry Configuration
    max_retries: int = Field(3, env="AI_MAX_RETRIES", description="Max retry attempts")
    retry_delay_seconds: float = Field(5.0, env="AI_RETRY_DELAY", description="Delay between retries")
    
    # Language Configuration
    source_languages: List[str] = Field(["ar", "fr", "en"], env="AI_SOURCE_LANGUAGES", description="Source languages")
    target_language: str = Field("fr", env="AI_TARGET_LANGUAGE", description="Target language for translation")
    
    # New Configuration Integration
    use_advanced_config: bool = Field(True, env="AI_USE_ADVANCED_CONFIG", description="Use advanced AI configuration system")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Batch size must be between 1 and 100')
        return v
    
    def get_advanced_config(self):
        """Get the advanced AI enrichment configuration."""
        try:
            from config.ai_enrichment_config import get_ai_enrichment_config
            return get_ai_enrichment_config()
        except ImportError:
            logger.warning("Advanced AI configuration not available, using legacy settings")
            return None


class VectorizationControlSettings(BaseSettings):
    """Vectorization processing control settings."""
    
    # Pipeline Control
    enabled: bool = Field(True, env="VECTORIZATION_ENABLED", description="Enable vectorization pipeline")
    mode: PipelineMode = Field(PipelineMode.BATCH, env="VECTORIZATION_MODE", description="Vectorization mode")
    
    # Model Configuration
    model_name: str = Field("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
                           env="VECTOR_MODEL_NAME", description="Sentence transformer model")
    embedding_dimensions: int = Field(384, env="VECTOR_DIMENSIONS", description="Embedding dimensions")
    device: str = Field("cpu", env="VECTOR_DEVICE", description="Processing device (cpu/cuda)")
    
    # Processing Limits
    batch_size: int = Field(32, env="VECTOR_BATCH_SIZE", description="Vectors per batch")
    max_items_per_run: int = Field(1000, env="VECTOR_MAX_ITEMS_PER_RUN", description="Max items per run")
    max_workers: int = Field(4, env="VECTOR_MAX_WORKERS", description="Max worker processes")
    
    # Performance Configuration
    cache_vectors: bool = Field(True, env="VECTOR_CACHE", description="Cache computed vectors")
    use_gpu_if_available: bool = Field(True, env="VECTOR_USE_GPU", description="Use GPU if available")
    memory_limit_gb: float = Field(4.0, env="VECTOR_MEMORY_LIMIT", description="Memory limit in GB")
    
    # Content Processing
    vectorize_articles: bool = Field(True, env="VECTOR_PROCESS_ARTICLES", description="Vectorize articles")
    vectorize_posts: bool = Field(True, env="VECTOR_PROCESS_POSTS", description="Vectorize social media posts")
    vectorize_comments: bool = Field(False, env="VECTOR_PROCESS_COMMENTS", description="Vectorize comments")
    
    # Text Preprocessing
    max_text_length: int = Field(2000, env="VECTOR_MAX_TEXT_LENGTH", description="Max text length for vectorization")
    min_text_length: int = Field(50, env="VECTOR_MIN_TEXT_LENGTH", description="Min text length for vectorization")
    use_french_text_only: bool = Field(True, env="VECTOR_FRENCH_ONLY", description="Use French translations only")
    
    # Quality Control
    similarity_threshold: float = Field(0.8, env="VECTOR_SIMILARITY_THRESHOLD", description="Similarity threshold for duplicates")
    enable_duplicate_detection: bool = Field(True, env="VECTOR_ENABLE_DUPLICATE_DETECTION", description="Enable duplicate detection")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 128:
            raise ValueError('Vector batch size must be between 1 and 128')
        return v


class MonitoringControlSettings(BaseSettings):
    """Monitoring and alerting control settings."""
    
    # Monitoring Control
    enabled: bool = Field(True, env="MONITORING_ENABLED", description="Enable monitoring")
    detailed_logging: bool = Field(True, env="MONITORING_DETAILED_LOGGING", description="Enable detailed logging")
    
    # Performance Monitoring
    track_processing_times: bool = Field(True, env="MONITORING_TRACK_TIMES", description="Track processing times")
    track_memory_usage: bool = Field(True, env="MONITORING_TRACK_MEMORY", description="Track memory usage")
    track_api_usage: bool = Field(True, env="MONITORING_TRACK_API", description="Track API usage")
    
    # Alerting
    enable_alerts: bool = Field(True, env="MONITORING_ENABLE_ALERTS", description="Enable alerts")
    alert_on_failures: bool = Field(True, env="MONITORING_ALERT_FAILURES", description="Alert on failures")
    alert_on_slow_processing: bool = Field(True, env="MONITORING_ALERT_SLOW", description="Alert on slow processing")
    
    # Thresholds
    failure_rate_threshold: float = Field(0.1, env="MONITORING_FAILURE_THRESHOLD", description="Failure rate threshold")
    slow_processing_threshold_seconds: int = Field(300, env="MONITORING_SLOW_THRESHOLD", description="Slow processing threshold")
    memory_usage_threshold_gb: float = Field(8.0, env="MONITORING_MEMORY_THRESHOLD", description="Memory usage threshold")
    
    # Retention
    metrics_retention_days: int = Field(30, env="MONITORING_METRICS_RETENTION", description="Metrics retention days")
    logs_retention_days: int = Field(7, env="MONITORING_LOGS_RETENTION", description="Logs retention days")


class SchedulingControlSettings(BaseSettings):
    """Scheduling and coordination control settings."""
    
    # Global Scheduling
    enabled: bool = Field(True, env="SCHEDULING_ENABLED", description="Enable scheduling")
    coordination_mode: str = Field("sequential", env="SCHEDULING_MODE", description="Coordination mode (sequential/parallel)")
    
    # Pipeline Coordination
    rss_first: bool = Field(True, env="SCHEDULING_RSS_FIRST", description="Run RSS pipeline first")
    facebook_after_rss: bool = Field(True, env="SCHEDULING_FACEBOOK_AFTER_RSS", description="Run Facebook after RSS")
    ai_enrichment_after_content: bool = Field(True, env="SCHEDULING_AI_AFTER_CONTENT", description="Run AI enrichment after content collection")
    vectorization_after_enrichment: bool = Field(True, env="SCHEDULING_VECTOR_AFTER_AI", description="Run vectorization after enrichment")
    
    # Timing Configuration
    pipeline_delay_minutes: int = Field(5, env="SCHEDULING_PIPELINE_DELAY", description="Delay between pipelines")
    full_cycle_interval_hours: int = Field(4, env="SCHEDULING_FULL_CYCLE_INTERVAL", description="Full cycle interval")
    priority_cycle_interval_hours: int = Field(1, env="SCHEDULING_PRIORITY_CYCLE_INTERVAL", description="Priority cycle interval")
    
    # Resource Management
    max_concurrent_pipelines: int = Field(2, env="SCHEDULING_MAX_CONCURRENT", description="Max concurrent pipelines")
    resource_check_interval_minutes: int = Field(10, env="SCHEDULING_RESOURCE_CHECK", description="Resource check interval")


class UnifiedControlSettings(BaseSettings):
    """Main unified control settings for all pipelines."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT", description="Environment")
    debug: bool = Field(False, env="DEBUG", description="Debug mode")
    
    # Global Controls
    master_enabled: bool = Field(True, env="MASTER_ENABLED", description="Master enable switch")
    maintenance_mode: bool = Field(False, env="MAINTENANCE_MODE", description="Maintenance mode")
    
    # Pipeline Settings
    rss: RSSControlSettings = RSSControlSettings()
    facebook: FacebookControlSettings = FacebookControlSettings()
    ai_enrichment: AIEnrichmentControlSettings = AIEnrichmentControlSettings()
    vectorization: VectorizationControlSettings = VectorizationControlSettings()
    monitoring: MonitoringControlSettings = MonitoringControlSettings()
    scheduling: SchedulingControlSettings = SchedulingControlSettings()
    
    # Application Metadata
    app_name: str = "Tunisia Intelligence Unified Control"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def is_pipeline_enabled(self, pipeline_name: str) -> bool:
        """Check if a specific pipeline is enabled."""
        if not self.master_enabled or self.maintenance_mode:
            return False
        
        pipeline_settings = getattr(self, pipeline_name, None)
        if pipeline_settings and hasattr(pipeline_settings, 'enabled'):
            return pipeline_settings.enabled
        return False
    
    def get_pipeline_mode(self, pipeline_name: str) -> PipelineMode:
        """Get the mode for a specific pipeline."""
        pipeline_settings = getattr(self, pipeline_name, None)
        if pipeline_settings and hasattr(pipeline_settings, 'mode'):
            return pipeline_settings.mode
        return PipelineMode.DISABLED
    
    def get_processing_order(self) -> List[str]:
        """Get the processing order based on scheduling configuration."""
        order = []
        
        if self.scheduling.rss_first and self.is_pipeline_enabled('rss'):
            order.append('rss')
        
        if self.scheduling.facebook_after_rss and self.is_pipeline_enabled('facebook'):
            order.append('facebook')
        elif self.is_pipeline_enabled('facebook') and 'facebook' not in order:
            order.append('facebook')
        
        if self.scheduling.ai_enrichment_after_content and self.is_pipeline_enabled('ai_enrichment'):
            order.append('ai_enrichment')
        
        if self.scheduling.vectorization_after_enrichment and self.is_pipeline_enabled('vectorization'):
            order.append('vectorization')
        
        return order
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()


# Global settings instance
_unified_settings: Optional[UnifiedControlSettings] = None


def get_unified_control() -> UnifiedControlSettings:
    """Get the global unified control settings instance."""
    global _unified_settings
    if _unified_settings is None:
        _unified_settings = UnifiedControlSettings()
    return _unified_settings


def reload_unified_control() -> UnifiedControlSettings:
    """Reload unified control settings from environment variables."""
    global _unified_settings
    _unified_settings = UnifiedControlSettings()
    return _unified_settings


# Convenience functions for pipeline settings
def get_rss_control() -> RSSControlSettings:
    """Get RSS control settings."""
    return get_unified_control().rss


def get_facebook_control() -> FacebookControlSettings:
    """Get Facebook control settings."""
    return get_unified_control().facebook


def get_ai_enrichment_control() -> AIEnrichmentControlSettings:
    """Get AI enrichment control settings."""
    return get_unified_control().ai_enrichment


def get_vectorization_control() -> VectorizationControlSettings:
    """Get vectorization control settings."""
    return get_unified_control().vectorization


def get_monitoring_control() -> MonitoringControlSettings:
    """Get monitoring control settings."""
    return get_unified_control().monitoring


def get_scheduling_control() -> SchedulingControlSettings:
    """Get scheduling control settings."""
    return get_unified_control().scheduling
