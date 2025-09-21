# Facebook Pipeline Tunable Parameters

This document provides a comprehensive guide to all tunable parameters in the Facebook scraping pipeline for the Tunisia Intelligence system.

## Overview

The Facebook pipeline configuration is centralized in `config/facebook_config.py` and provides fine-grained control over:
- **Scraping frequency and timing**
- **Rate limiting and API usage**
- **Batch processing and performance**
- **Data extraction scope and depth**
- **Error handling and retry logic**

## Configuration Structure

The configuration is organized into three main components:

### 1. FacebookExtractionConfig
Controls the core data extraction process

### 2. FacebookLoaderConfig  
Controls database operations and data loading

### 3. FacebookScraperConfig
Controls the CLI runner and analysis features

## Detailed Parameter Reference

### 🕒 TIMING AND FREQUENCY PARAMETERS

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `hours_back` | 168 (7 days) | How far back to look for posts | Higher = more data, more API calls |
| `min_api_delay` | 0.3 seconds | Minimum delay between API calls | Lower = faster, higher rate limit risk |
| `page_cache_duration` | 86400 (24 hours) | How long to cache page info | Higher = fewer API calls, staler data |

**Tuning Recommendations:**
- **High frequency monitoring**: `hours_back=24` (daily)
- **Weekly analysis**: `hours_back=168` (7 days)
- **Historical analysis**: `hours_back=720` (30 days)

### ⚡ RATE LIMITING PARAMETERS

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `max_api_calls_per_run` | 100 | Maximum API calls before stopping | Higher = more data, rate limit risk |
| `api_timeout` | 30 seconds | Request timeout for API calls | Higher = more resilient, slower |

**Facebook Rate Limits:**
- **App-level**: 200 calls/hour/user
- **Page-level**: Varies by page popularity
- **Conservative**: 50-100 calls/run
- **Aggressive**: 150-200 calls/run

### 📦 BATCH PROCESSING PARAMETERS

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `max_pages_per_run` | 53 | Maximum pages to process per run | Higher = more comprehensive, more API calls |
| `posts_limit_per_page` | 25 | Maximum posts to fetch per page | Higher = more posts, more API calls |

**Batch Size Recommendations:**
- **Quick updates**: `max_pages_per_run=15`, `posts_limit_per_page=10`
- **Balanced**: `max_pages_per_run=25`, `posts_limit_per_page=25`
- **Comprehensive**: `max_pages_per_run=53`, `posts_limit_per_page=50`

### 🎯 DATA EXTRACTION SCOPE

| Parameter | Default | Description | Customizable |
|-----------|---------|-------------|--------------|
| `api_version` | "v18.0" | Facebook API version | Yes |
| `post_fields` | Essential fields | Which post data to extract | Yes |
| `page_fields` | ['id', 'name'] | Which page data to extract | Yes |

**Available Post Fields:**
```python
# Current essential fields
post_fields = [
    'id',                                    # Post ID
    'message',                               # Post content
    'created_time',                          # When posted
    'permalink_url',                         # Link to post
    'reactions.summary(total_count)',        # Total reactions
    'comments{message,created_time}'         # Comments with essential fields
]

# Additional available fields
additional_fields = [
    'story',                                 # Post story
    'description',                           # Post description
    'link',                                  # External link
    'picture',                               # Post image
    'shares',                                # Share count
    'reactions.type(LIKE).summary(total_count)',  # Specific reaction types
    'comments.summary(total_count)',         # Comment count only
]
```

### 📊 REACTION ESTIMATION PARAMETERS

| Parameter | Default | Description | Tunable |
|-----------|---------|-------------|---------|
| `reaction_distribution` | See below | Estimated reaction breakdown | Yes |

**Default Reaction Distribution:**
```python
reaction_distribution = {
    'like': 0.70,   # 70% likes
    'love': 0.20,   # 20% love
    'wow': 0.00,    # 0% wow
    'haha': 0.05,   # 5% haha
    'sad': 0.03,    # 3% sad
    'angry': 0.02   # 2% angry
}
```

### 🎯 PRIORITY AND FILTERING

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `default_page_priority` | 5 | Priority for new pages | Higher = processed first |
| `max_page_priority` | 10 | Maximum priority value | - |
| `min_page_priority` | 1 | Minimum priority value | - |
| `priority_increase_for_activity` | 1 | Priority boost for active pages | Higher = more aggressive prioritization |
| `priority_decrease_for_inactivity` | 0.1 | Priority reduction for inactive pages | Higher = more aggressive deprioritization |

### 📁 FILE PATHS

| Parameter | Default | Description | Customizable |
|-----------|---------|-------------|--------------|
| `page_cache_file` | "facebook_page_cache.pkl" | Page info cache location | Yes |
| `page_priorities_file` | "facebook_page_priorities.json" | Page priorities storage | Yes |
| `log_file` | "facebook_scraper.log" | Log file location | Yes |

### 🛠️ DATABASE AND LOADING PARAMETERS

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `use_batch_inserts` | True | Use batch database operations | True = faster, False = more granular |
| `check_duplicates` | True | Check for duplicate posts | True = cleaner data, slower |
| `update_existing_posts` | True | Update existing posts vs skip | True = fresher data, more operations |
| `enable_state_tracking` | True | Track parsing state | True = avoids duplicates |
| `enable_priority_updates` | True | Update page priorities | True = adaptive prioritization |
| `log_to_database` | True | Log results to database | True = better monitoring |

### 📈 ANALYSIS AND REPORTING PARAMETERS

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `perfect_efficiency_threshold` | 4.0 | API calls/source for "perfect" rating | Lower = stricter efficiency requirements |
| `excellent_efficiency_threshold` | 6.0 | API calls/source for "excellent" rating | - |
| `moderate_efficiency_threshold` | 10.0 | API calls/source for "moderate" rating | - |
| `max_errors_to_display` | 3 | Maximum errors shown in output | Higher = more verbose error reporting |

## Usage Examples

### Basic Configuration

```python
from config.facebook_config import get_facebook_config, update_facebook_config

# Get current configuration
config = get_facebook_config()

# Update specific parameters
update_facebook_config(extraction={
    'hours_back': 48,  # Look back 2 days
    'max_pages_per_run': 20,  # Process 20 pages max
    'min_api_delay': 0.5  # More conservative rate limiting
})
```

### Environment Variables

Set these environment variables to configure the pipeline:

```bash
# Timing and frequency
export FB_HOURS_BACK=168
export FB_MIN_API_DELAY=0.3

# Rate limiting
export FB_MAX_API_CALLS=100
export FB_API_TIMEOUT=30

# Batch processing
export FB_MAX_PAGES=53
export FB_POSTS_LIMIT=25

# API configuration
export FB_API_VERSION=v18.0

# Feature toggles
export FB_USE_BATCH_INSERTS=true
export FB_CHECK_DUPLICATES=true
export FB_STATE_TRACKING=true
export FB_PRIORITY_UPDATES=true
export FB_LOG_TO_DB=true

# CLI defaults
export FB_DEFAULT_HOURS_BACK=168
export FB_DEFAULT_MAX_PAGES=20
export FB_SHOW_ANALYSIS=false
export FB_VERBOSE=false
```

### Predefined Performance Modes

```python
from config.facebook_config import set_performance_mode

# Conservative mode - safe for frequent runs
set_performance_mode('conservative')
# - min_api_delay: 0.5s
# - max_api_calls_per_run: 50
# - max_pages_per_run: 15
# - posts_limit_per_page: 20

# Balanced mode - good for regular monitoring
set_performance_mode('balanced')
# - min_api_delay: 0.3s
# - max_api_calls_per_run: 100
# - max_pages_per_run: 25
# - posts_limit_per_page: 25

# Aggressive mode - maximum data extraction
set_performance_mode('aggressive')
# - min_api_delay: 0.1s
# - max_api_calls_per_run: 200
# - max_pages_per_run: 53
# - posts_limit_per_page: 50
```

### Convenience Functions

```python
from config.facebook_config import (
    set_scraping_frequency,
    set_rate_limiting,
    set_batch_size
)

# Set scraping frequency
set_scraping_frequency(hours_back=72)  # 3 days

# Set rate limiting
set_rate_limiting(min_delay=0.2, max_calls=150)

# Set batch size
set_batch_size(max_pages=30, posts_per_page=40)
```

## Scheduling Recommendations

Based on efficiency thresholds:

### Perfect Efficiency (≤4.0 calls/source)
- **Run every 2-3 hours**
- **Daily API usage**: ~320-480 calls
- **Sustainable for continuous monitoring**

### Excellent Efficiency (≤6.0 calls/source)
- **Run every 4-6 hours**
- **Daily API usage**: ~240-360 calls
- **Good for regular monitoring**

### Moderate Efficiency (≤10.0 calls/source)
- **Run every 6-8 hours**
- **Daily API usage**: ~180-240 calls
- **Acceptable for periodic monitoring**

## Monitoring and Optimization

### Key Metrics to Monitor

1. **API Calls per Source**: Target ≤4.0 for optimal efficiency
2. **Posts Found per Run**: Indicates content availability
3. **Error Rate**: Should be <5% for healthy operation
4. **Processing Time**: Should be <60 seconds for most runs
5. **Cache Hit Rate**: Higher = fewer API calls

### Optimization Strategies

1. **Increase Cache Duration**: Reduce API calls for page info
2. **Adjust Hours Back**: Balance data freshness vs API usage
3. **Optimize Page Priorities**: Focus on most active pages
4. **Use Batch Operations**: Improve database performance
5. **Enable State Tracking**: Avoid processing duplicates

### Troubleshooting Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Rate limit errors | Too aggressive settings | Increase `min_api_delay`, reduce `max_api_calls_per_run` |
| No posts found | `hours_back` too small | Increase `hours_back` parameter |
| Slow performance | Large batch sizes | Reduce `max_pages_per_run` or `posts_limit_per_page` |
| Duplicate posts | State tracking disabled | Enable `enable_state_tracking` |
| High API usage | Inefficient extraction | Check `post_fields`, enable caching |

## Integration with Unified Control System

The Facebook configuration integrates with the unified control system:

```python
# In unified_pipeline_controller.py
from config.facebook_config import get_facebook_config

config = get_facebook_config()
facebook_hours_back = config.extraction.hours_back
facebook_max_pages = config.extraction.max_pages_per_run
```

This ensures consistent configuration across all pipeline components and enables centralized tuning of the entire Tunisia Intelligence system.
