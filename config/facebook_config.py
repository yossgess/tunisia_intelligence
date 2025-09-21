"""
Facebook Pipeline Configuration
Centralized configuration for all tunable parameters in the Facebook scraping pipeline.

This file contains all configurable parameters that can be tuned for:
- Scraping frequency and timing
- Rate limiting and API usage
- Batch processing and performance
- Data extraction scope and depth
- Error handling and retry logic
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import os
from pathlib import Path


@dataclass
class FacebookExtractionConfig:
    """Configuration for Facebook data extraction parameters"""
    
    # === TIMING AND FREQUENCY PARAMETERS ===
    # How far back to look for posts (in hours)
    hours_back: int = 336  # 14 days default
    
    # Minimum delay between API calls (seconds)
    min_api_delay: float = 0.3
    
    # Cache freshness duration (seconds) - 24 hours default
    page_cache_duration: int = 86400
    
    # === RATE LIMITING PARAMETERS ===
    # Maximum API calls before stopping (conservative limit)
    max_api_calls_per_run: int = 100
    
    # Request timeout for API calls (seconds)
    api_timeout: int = 30
    
    # === BATCH PROCESSING PARAMETERS ===
    # Maximum pages to process per run
    max_pages_per_run: int = 999  # Unlimited - process all Facebook sources
    
    # Maximum posts to fetch per page per API call
    posts_limit_per_page: int = 100  # Increased limit for comprehensive data collection
    
    # === DATA EXTRACTION SCOPE ===
    # Facebook API version to use
    api_version: str = "v18.0"
    
    # Essential post fields to extract
    post_fields: List[str] = None
    
    # Essential page fields to extract
    page_fields: List[str] = None
    
    # === REACTION ESTIMATION PARAMETERS ===
    # Estimated reaction distribution percentages
    reaction_distribution: Dict[str, float] = None
    
    # === PRIORITY AND FILTERING ===
    # Default priority for new pages
    default_page_priority: int = 5
    
    # Maximum priority value
    max_page_priority: int = 10
    
    # Minimum priority value
    min_page_priority: int = 1
    
    # Priority adjustment for active pages
    priority_increase_for_activity: int = 1
    
    # Priority decrease for inactive pages
    priority_decrease_for_inactivity: float = 0.1
    
    # === FILE PATHS ===
    # Page cache file location
    page_cache_file: str = "facebook_page_cache.pkl"
    
    # Page priorities file location
    page_priorities_file: str = "facebook_page_priorities.json"
    
    # Log file location
    log_file: str = "facebook_scraper.log"
    
    # === ERROR HANDLING ===
    # Whether to skip known failed pages
    skip_failed_pages: bool = True
    
    # Maximum errors to show in output
    max_errors_to_display: int = 3
    
    def __post_init__(self):
        """Initialize default values for complex fields"""
        if self.post_fields is None:
            self.post_fields = [
                'id',                                    # Post ID
                'message',                               # Post content
                'created_time',                          # When posted
                'permalink_url',                         # Link to post
                'reactions.summary(total_count)',        # Total reactions (no breakdown)
                'comments{message,created_time}'         # Comments with essential fields
            ]
        
        if self.page_fields is None:
            self.page_fields = [
                'id',    # Page ID
                'name'   # Page name
            ]
        
        if self.reaction_distribution is None:
            # Estimated reaction distribution based on typical Facebook patterns
            self.reaction_distribution = {
                'like': 0.70,   # ~70% likes
                'love': 0.20,   # ~20% love
                'wow': 0.00,    # ~0% wow
                'haha': 0.05,   # ~5% haha
                'sad': 0.03,    # ~3% sad
                'angry': 0.02   # ~2% angry
            }


@dataclass
class FacebookLoaderConfig:
    """Configuration for Facebook data loading and database operations"""
    
    # === DATABASE BATCH PROCESSING ===
    # Whether to use batch inserts for better performance
    use_batch_inserts: bool = True
    
    # Whether to check for duplicates before inserting
    check_duplicates: bool = True
    
    # Whether to update existing posts or skip them
    update_existing_posts: bool = True
    
    # === STATE TRACKING ===
    # Whether to track parsing state to avoid duplicates
    enable_state_tracking: bool = True
    
    # Whether to update page priorities based on activity
    enable_priority_updates: bool = True
    
    # === LOGGING AND MONITORING ===
    # Whether to log parsing results to database
    log_to_database: bool = True
    
    # Log level for Facebook operations
    log_level: str = "INFO"
    
    # Whether to save page cache after each run
    save_cache_after_run: bool = True
    
    # Whether to save priorities after each run
    save_priorities_after_run: bool = True


@dataclass
class FacebookScraperConfig:
    """Configuration for the Facebook scraper runner"""
    
    # === COMMAND LINE DEFAULTS ===
    # Default hours back for CLI
    default_hours_back: int = 336  # 14 days
    
    # Default max pages for CLI
    default_max_pages: int = 999  # Unlimited - process all pages
    
    # === ANALYSIS AND REPORTING ===
    # Whether to show detailed analysis by default
    show_analysis_by_default: bool = False
    
    # Whether to enable verbose logging by default
    verbose_by_default: bool = False
    
    # === EFFICIENCY THRESHOLDS ===
    # API calls per source threshold for "perfect" efficiency
    perfect_efficiency_threshold: float = 4.0
    
    # API calls per source threshold for "excellent" efficiency
    excellent_efficiency_threshold: float = 6.0
    
    # API calls per source threshold for "moderate" efficiency
    moderate_efficiency_threshold: float = 10.0
    
    # === SCHEDULING RECOMMENDATIONS ===
    # Recommended run frequency for perfect efficiency (hours)
    perfect_efficiency_run_frequency: int = 3
    
    # Recommended run frequency for excellent efficiency (hours)
    excellent_efficiency_run_frequency: int = 5
    
    # Recommended run frequency for moderate efficiency (hours)
    moderate_efficiency_run_frequency: int = 7
    
    # === WARNING THRESHOLDS ===
    # Warn if max_pages exceeds this value
    max_pages_warning_threshold: int = 30


@dataclass
class FacebookPipelineConfig:
    """Complete Facebook pipeline configuration combining all components"""
    
    extraction: FacebookExtractionConfig
    loader: FacebookLoaderConfig
    scraper: FacebookScraperConfig
    
    def __init__(self, 
                 extraction_config: Optional[FacebookExtractionConfig] = None,
                 loader_config: Optional[FacebookLoaderConfig] = None,
                 scraper_config: Optional[FacebookScraperConfig] = None):
        """Initialize with optional custom configurations"""
        self.extraction = extraction_config or FacebookExtractionConfig()
        self.loader = loader_config or FacebookLoaderConfig()
        self.scraper = scraper_config or FacebookScraperConfig()
    
    @classmethod
    def from_environment(cls) -> 'FacebookPipelineConfig':
        """Create configuration from environment variables"""
        extraction_config = FacebookExtractionConfig(
            hours_back=int(os.getenv('FB_HOURS_BACK', 336)),
            min_api_delay=float(os.getenv('FB_MIN_API_DELAY', 0.3)),
            max_api_calls_per_run=int(os.getenv('FB_MAX_API_CALLS', 100)),
            max_pages_per_run=int(os.getenv('FB_MAX_PAGES', 999)),
            posts_limit_per_page=int(os.getenv('FB_POSTS_LIMIT', 100)),
            api_version=os.getenv('FB_API_VERSION', 'v18.0'),
            api_timeout=int(os.getenv('FB_API_TIMEOUT', 30)),
            page_cache_duration=int(os.getenv('FB_CACHE_DURATION', 86400)),
        )
        
        loader_config = FacebookLoaderConfig(
            use_batch_inserts=os.getenv('FB_USE_BATCH_INSERTS', 'true').lower() == 'true',
            check_duplicates=os.getenv('FB_CHECK_DUPLICATES', 'true').lower() == 'true',
            update_existing_posts=os.getenv('FB_UPDATE_EXISTING', 'true').lower() == 'true',
            enable_state_tracking=os.getenv('FB_STATE_TRACKING', 'true').lower() == 'true',
            enable_priority_updates=os.getenv('FB_PRIORITY_UPDATES', 'true').lower() == 'true',
            log_to_database=os.getenv('FB_LOG_TO_DB', 'true').lower() == 'true',
            log_level=os.getenv('FB_LOG_LEVEL', 'INFO'),
        )
        
        scraper_config = FacebookScraperConfig(
            default_hours_back=int(os.getenv('FB_DEFAULT_HOURS_BACK', 336)),
            default_max_pages=int(os.getenv('FB_DEFAULT_MAX_PAGES', 999)),
            show_analysis_by_default=os.getenv('FB_SHOW_ANALYSIS', 'false').lower() == 'true',
            verbose_by_default=os.getenv('FB_VERBOSE', 'false').lower() == 'true',
        )
        
        return cls(extraction_config, loader_config, scraper_config)
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for serialization"""
        return {
            'extraction': {
                'hours_back': self.extraction.hours_back,
                'min_api_delay': self.extraction.min_api_delay,
                'page_cache_duration': self.extraction.page_cache_duration,
                'max_api_calls_per_run': self.extraction.max_api_calls_per_run,
                'api_timeout': self.extraction.api_timeout,
                'max_pages_per_run': self.extraction.max_pages_per_run,
                'posts_limit_per_page': self.extraction.posts_limit_per_page,
                'api_version': self.extraction.api_version,
                'post_fields': self.extraction.post_fields,
                'page_fields': self.extraction.page_fields,
                'reaction_distribution': self.extraction.reaction_distribution,
                'default_page_priority': self.extraction.default_page_priority,
                'max_page_priority': self.extraction.max_page_priority,
                'min_page_priority': self.extraction.min_page_priority,
                'priority_increase_for_activity': self.extraction.priority_increase_for_activity,
                'priority_decrease_for_inactivity': self.extraction.priority_decrease_for_inactivity,
                'page_cache_file': self.extraction.page_cache_file,
                'page_priorities_file': self.extraction.page_priorities_file,
                'log_file': self.extraction.log_file,
                'skip_failed_pages': self.extraction.skip_failed_pages,
                'max_errors_to_display': self.extraction.max_errors_to_display,
            },
            'loader': {
                'use_batch_inserts': self.loader.use_batch_inserts,
                'check_duplicates': self.loader.check_duplicates,
                'update_existing_posts': self.loader.update_existing_posts,
                'enable_state_tracking': self.loader.enable_state_tracking,
                'enable_priority_updates': self.loader.enable_priority_updates,
                'log_to_database': self.loader.log_to_database,
                'log_level': self.loader.log_level,
                'save_cache_after_run': self.loader.save_cache_after_run,
                'save_priorities_after_run': self.loader.save_priorities_after_run,
            },
            'scraper': {
                'default_hours_back': self.scraper.default_hours_back,
                'default_max_pages': self.scraper.default_max_pages,
                'show_analysis_by_default': self.scraper.show_analysis_by_default,
                'verbose_by_default': self.scraper.verbose_by_default,
                'perfect_efficiency_threshold': self.scraper.perfect_efficiency_threshold,
                'excellent_efficiency_threshold': self.scraper.excellent_efficiency_threshold,
                'moderate_efficiency_threshold': self.scraper.moderate_efficiency_threshold,
                'perfect_efficiency_run_frequency': self.scraper.perfect_efficiency_run_frequency,
                'excellent_efficiency_run_frequency': self.scraper.excellent_efficiency_run_frequency,
                'moderate_efficiency_run_frequency': self.scraper.moderate_efficiency_run_frequency,
                'max_pages_warning_threshold': self.scraper.max_pages_warning_threshold,
            }
        }


# Default configuration instance
DEFAULT_FACEBOOK_CONFIG = FacebookPipelineConfig()

# Environment-based configuration instance
FACEBOOK_CONFIG = FacebookPipelineConfig.from_environment()


def get_facebook_config() -> FacebookPipelineConfig:
    """Get the current Facebook pipeline configuration"""
    return FACEBOOK_CONFIG


def update_facebook_config(**kwargs) -> FacebookPipelineConfig:
    """Update Facebook configuration with new values"""
    global FACEBOOK_CONFIG
    
    # Update extraction config
    if 'extraction' in kwargs:
        for key, value in kwargs['extraction'].items():
            if hasattr(FACEBOOK_CONFIG.extraction, key):
                setattr(FACEBOOK_CONFIG.extraction, key, value)
    
    # Update loader config
    if 'loader' in kwargs:
        for key, value in kwargs['loader'].items():
            if hasattr(FACEBOOK_CONFIG.loader, key):
                setattr(FACEBOOK_CONFIG.loader, key, value)
    
    # Update scraper config
    if 'scraper' in kwargs:
        for key, value in kwargs['scraper'].items():
            if hasattr(FACEBOOK_CONFIG.scraper, key):
                setattr(FACEBOOK_CONFIG.scraper, key, value)
    
    return FACEBOOK_CONFIG


# Convenience functions for common configuration updates
def set_scraping_frequency(hours_back: int):
    """Set how far back to look for posts"""
    update_facebook_config(extraction={'hours_back': hours_back})


def set_rate_limiting(min_delay: float, max_calls: int):
    """Set rate limiting parameters"""
    update_facebook_config(extraction={
        'min_api_delay': min_delay,
        'max_api_calls_per_run': max_calls
    })


def set_batch_size(max_pages: int, posts_per_page: int):
    """Set batch processing parameters"""
    update_facebook_config(extraction={
        'max_pages_per_run': max_pages,
        'posts_limit_per_page': posts_per_page
    })


def set_performance_mode(mode: str):
    """Set predefined performance modes"""
    if mode == 'conservative':
        update_facebook_config(extraction={
            'min_api_delay': 0.5,
            'max_api_calls_per_run': 50,
            'max_pages_per_run': 15,
            'posts_limit_per_page': 20
        })
    elif mode == 'balanced':
        update_facebook_config(extraction={
            'min_api_delay': 0.3,
            'max_api_calls_per_run': 100,
            'max_pages_per_run': 25,
            'posts_limit_per_page': 25
        })
    elif mode == 'aggressive':
        update_facebook_config(extraction={
            'min_api_delay': 0.1,
            'max_api_calls_per_run': 200,
            'max_pages_per_run': 53,
            'posts_limit_per_page': 50
        })
