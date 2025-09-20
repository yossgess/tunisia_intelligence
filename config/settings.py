"""
Configuration management system for Tunisia Intelligence RSS scraper.

This module provides centralized configuration management with environment variable support,
validation, and proper secret handling.
"""
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="", env="SUPABASE_URL", description="Supabase database URL")
    secret_key: str = Field(default="", env="SUPABASE_SECRET_KEY", description="Supabase secret key")
    anon_key: Optional[str] = Field(None, env="SUPABASE_ANON_KEY", description="Supabase anonymous key")
    
    @validator('url')
    def validate_url(cls, v):
        if v and not v.startswith('https://'):
            raise ValueError('Database URL must be a valid HTTPS URL')
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if v and len(v) < 50:
            raise ValueError('Secret key must be at least 50 characters long')
        return v
    
    class Config:
        env_prefix = "DB_"


class ScrapingSettings(BaseSettings):
    """RSS scraping configuration settings."""
    
    max_retries: int = Field(3, env="SCRAPING_MAX_RETRIES", description="Maximum retry attempts")
    initial_timeout: int = Field(60, env="SCRAPING_INITIAL_TIMEOUT", description="Initial timeout in seconds")
    rate_limit_delay: float = Field(1.0, env="SCRAPING_RATE_LIMIT_DELAY", description="Delay between requests in seconds")
    batch_size: int = Field(100, env="SCRAPING_BATCH_SIZE", description="Number of articles to process in batch")
    max_workers: int = Field(5, env="SCRAPING_MAX_WORKERS", description="Maximum number of worker threads")
    user_agent: str = Field(
        "Tunisia Intelligence RSS Scraper 1.0", 
        env="SCRAPING_USER_AGENT", 
        description="User agent string for HTTP requests"
    )
    fast_mode: bool = Field(
        True, 
        env="SCRAPING_FAST_MODE", 
        description="Enable optimized processing mode"
    )
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Max retries must be between 0 and 10')
        return v
    
    @validator('initial_timeout')
    def validate_initial_timeout(cls, v):
        if v < 10 or v > 300:
            raise ValueError('Initial timeout must be between 10 and 300 seconds')
        return v
    
    @validator('rate_limit_delay')
    def validate_rate_limit_delay(cls, v):
        if v < 0.1 or v > 10.0:
            raise ValueError('Rate limit delay must be between 0.1 and 10.0 seconds')
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    file_path: str = Field("rss_loader.log", env="LOG_FILE_PATH", description="Log file path")
    max_file_size: int = Field(10485760, env="LOG_MAX_FILE_SIZE", description="Max log file size in bytes (10MB)")
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT", description="Number of backup log files")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()


class MonitoringSettings(BaseSettings):
    """Monitoring and alerting configuration settings."""
    
    enabled: bool = Field(True, env="MONITORING_ENABLED", description="Enable monitoring")
    metrics_retention_days: int = Field(30, env="MONITORING_METRICS_RETENTION_DAYS", description="Days to retain metrics")
    alert_on_errors: bool = Field(True, env="MONITORING_ALERT_ON_ERRORS", description="Send alerts on errors")
    alert_error_threshold: int = Field(5, env="MONITORING_ALERT_ERROR_THRESHOLD", description="Error count threshold for alerts")
    
    # Webhook settings for alerts
    webhook_url: Optional[str] = Field(None, env="MONITORING_WEBHOOK_URL", description="Webhook URL for alerts")
    
    @validator('metrics_retention_days')
    def validate_retention_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Metrics retention days must be between 1 and 365')
        return v


class ContentSettings(BaseSettings):
    """Content processing configuration settings."""
    
    min_title_length: int = Field(5, env="CONTENT_MIN_TITLE_LENGTH", description="Minimum title length")
    min_content_length: int = Field(50, env="CONTENT_MIN_CONTENT_LENGTH", description="Minimum content length")
    max_content_length: int = Field(50000, env="CONTENT_MAX_CONTENT_LENGTH", description="Maximum content length")
    enable_deduplication: bool = Field(True, env="CONTENT_ENABLE_DEDUPLICATION", description="Enable content deduplication")
    enable_sentiment_analysis: bool = Field(False, env="CONTENT_ENABLE_SENTIMENT_ANALYSIS", description="Enable sentiment analysis")
    
    # Language settings
    default_language: str = Field("ar", env="CONTENT_DEFAULT_LANGUAGE", description="Default content language")
    supported_languages: List[str] = Field(["ar", "fr", "en"], env="CONTENT_SUPPORTED_LANGUAGES", description="Supported languages")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT", description="Application environment")
    debug: bool = Field(False, env="DEBUG", description="Enable debug mode")
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    scraping: ScrapingSettings = ScrapingSettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    content: ContentSettings = ContentSettings()
    
    # Application metadata
    app_name: str = "Tunisia Intelligence RSS Scraper"
    app_version: str = "1.0.0"
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {", ".join(valid_envs)}')
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields to prevent conflicts
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Perform additional validation after initialization."""
        if self.environment == "production" and self.debug:
            logger.warning("Debug mode is enabled in production environment")
        
        # Validate that required directories exist
        log_dir = Path(self.logging.file_path).parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created log directory: {log_dir}")
    
    def get_database_url(self) -> str:
        """Get the database URL with proper formatting."""
        return self.database.url
    
    def get_database_key(self) -> str:
        """Get the database secret key."""
        return self.database.secret_key
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def to_dict(self) -> Dict:
        """Convert settings to dictionary (excluding sensitive data)."""
        data = self.dict()
        # Remove sensitive information
        if 'database' in data:
            data['database'].pop('secret_key', None)
            data['database'].pop('anon_key', None)
        return data


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global _settings
    _settings = Settings()
    return _settings


# Convenience functions for common settings
def get_database_config() -> DatabaseSettings:
    """Get database configuration."""
    return get_settings().database


def get_scraping_config() -> ScrapingSettings:
    """Get scraping configuration."""
    return get_settings().scraping


def get_logging_config() -> LoggingSettings:
    """Get logging configuration."""
    return get_settings().logging


def get_monitoring_config() -> MonitoringSettings:
    """Get monitoring configuration."""
    return get_settings().monitoring


def get_content_config() -> ContentSettings:
    """Get content processing configuration."""
    return get_settings().content
