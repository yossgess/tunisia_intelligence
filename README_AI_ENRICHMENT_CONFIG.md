# AI Enrichment Configuration System

## Overview

The Tunisia Intelligence system now includes a comprehensive AI enrichment configuration system that provides full control over AI processing parameters, prompts, and behavior through both configuration files and the web dashboard.

## Key Features

### ✅ **Tunable Parameters by Content Type**
- **Articles**: Full enrichment with sentiment, keywords, entities, categories, and summaries
- **Posts**: Social media optimized processing with hashtag and mention handling
- **Comments**: Lightweight sentiment analysis or enhanced processing with bilingual support

### ✅ **Editable Prompts System**
- Content type specific prompts (articles, posts, comments)
- Processing mode specific prompts (full enrichment, sentiment only, etc.)
- Real-time prompt editing through web dashboard
- Prompt validation and template variable support

### ✅ **Dashboard Integration**
- Real-time configuration management
- Live parameter tuning
- Prompt editing interface
- Configuration testing and validation

### ✅ **Advanced Rate Limiting**
- Global and content-type specific rate limits
- Adaptive delay based on response times
- Burst protection and cooldown periods

### ✅ **Quality Control**
- Content validation and filtering
- Response validation and quality scoring
- Graceful degradation and fallback processing
- Comprehensive error handling

## Architecture

```
config/
├── ai_enrichment_config.py     # Main configuration system
├── ai_enrichment_prompts.py    # Prompt management system
└── unified_control.py          # Legacy integration wrapper

ai_enrichment/services/
├── configurable_enrichment_service.py  # New configurable service
├── enrichment_service.py               # Legacy service
└── enhanced_enrichment_service.py      # Enhanced processing

web_dashboard/
├── ai_config_manager.py        # Dashboard API endpoints
└── app.py                      # Updated with AI config integration

configurable_batch_enrichment.py  # New batch processing script
```

## Configuration Structure

### Content Type Settings

Each content type (articles, posts, comments) has its own configuration section:

```python
# Article Configuration
articles:
  enabled: true
  processing_mode: "full"  # full, sentiment_only, keywords_only, etc.
  batch_size: 10
  max_items_per_run: 100
  min_confidence_threshold: 0.7
  enable_sentiment: true
  enable_keywords: true
  enable_entities: true
  enable_categories: true
  enable_summary: true
  enable_translation: true
  max_keywords: 10
  max_entities: 15
  summary_max_length: 500
```

### Model Settings

```python
model:
  provider: "ollama"
  model_name: "qwen2.5:7b"
  temperature: 0.3
  max_tokens: 1024
  ollama_url: "http://localhost:11434"
  enable_fallback: true
  fallback_models: ["llama2:7b", "mistral:7b"]
```

### Rate Limiting

```python
rate_limiting:
  requests_per_minute: 20
  articles_per_minute: 5
  posts_per_minute: 8
  comments_per_minute: 15
  base_delay_seconds: 3.0
  adaptive_delay: true
  enable_burst_protection: true
```

## Prompt System

### Prompt Types

- **FULL_ENRICHMENT**: Complete analysis with all features
- **SENTIMENT_ONLY**: Sentiment analysis only
- **KEYWORDS_ONLY**: Keyword extraction only
- **ENTITIES_ONLY**: Named entity recognition only
- **TRANSLATION**: Content translation
- **ENHANCED_COMMENT**: Enhanced comment processing with bilingual output

### Template Variables

Prompts support template variables for dynamic content:

```python
prompt_vars = {
    'content': content,
    'max_keywords': settings.max_keywords,
    'max_entities': settings.max_entities,
    'summary_max_length': settings.summary_max_length
}
```

### Example Prompt

```python
"""Analyze the following French article content and provide comprehensive AI enrichment in JSON format.

Article Content: {content}

Requirements:
1. Sentiment Analysis: Determine overall sentiment (positive/negative/neutral) with confidence score
2. Keyword Extraction: Extract top {max_keywords} most important keywords with importance scores
3. Named Entity Recognition: Identify persons, organizations, locations with Tunisian context priority
4. Category Classification: Classify into primary and secondary categories
5. Summary Generation: Create concise Arabic summary (max {summary_max_length} characters)

Focus on Tunisian political, social, and economic context.
Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.85,
  "keywords": [...],
  "entities": [...],
  "category": {...},
  "summary": "Arabic summary text",
  "confidence": 0.89
}}"""
```

## Usage

### Command Line Usage

```bash
# Process all content types with default settings
python configurable_batch_enrichment.py

# Process only articles with custom limit
python configurable_batch_enrichment.py --content-type articles --limit 50

# Force reprocessing of already enriched content
python configurable_batch_enrichment.py --force-reprocess

# Show service status
python configurable_batch_enrichment.py --status
```

### Programmatic Usage

```python
from ai_enrichment.services.configurable_enrichment_service import ConfigurableEnrichmentService
from config.ai_enrichment_config import ContentType

# Initialize service
service = ConfigurableEnrichmentService()

# Process single item
result = service.enrich_content(
    content_id=123,
    content_type=ContentType.ARTICLE,
    content="Article content here",
    force_reprocess=False
)

print(f"Success: {result.success}")
print(f"Confidence: {result.confidence}")
print(f"Processing time: {result.processing_time_ms}ms")
```

### Batch Processing

```python
from configurable_batch_enrichment import ConfigurableBatchEnrichment

# Initialize batch processor
processor = ConfigurableBatchEnrichment()

# Process articles
article_stats = processor.process_articles(limit=100)
print(f"Processed: {article_stats.successful_items}/{article_stats.total_items}")

# Process posts
post_stats = processor.process_posts(limit=200)

# Process comments
comment_stats = processor.process_comments(limit=500)
```

## Dashboard Integration

### API Endpoints

The web dashboard provides comprehensive API endpoints for configuration management:

#### Configuration Management
- `GET /api/ai-config/status` - Get current AI configuration status
- `GET /api/ai-config/config` - Get full configuration
- `POST /api/ai-config/config` - Update configuration
- `GET /api/ai-config/config/content-type/{type}` - Get content type specific config
- `POST /api/ai-config/config/content-type/{type}` - Update content type config

#### Prompt Management
- `GET /api/ai-config/prompts` - Get all prompts
- `GET /api/ai-config/prompts/{content_type}/{prompt_type}` - Get specific prompt
- `POST /api/ai-config/prompts/{content_type}/{prompt_type}` - Update specific prompt
- `POST /api/ai-config/prompts/validate` - Validate prompt
- `POST /api/ai-config/prompts/reset` - Reset prompts to defaults

#### System Operations
- `POST /api/ai-config/reload` - Reload configuration and prompts
- `POST /api/ai-config/test` - Test configuration with sample content
- `GET /api/ai-config/options` - Get available configuration options

### Dashboard Features

1. **Real-time Configuration Editing**
   - Adjust batch sizes, rate limits, and processing parameters
   - Enable/disable content types and features
   - Update model settings and thresholds

2. **Prompt Management Interface**
   - Edit prompts for each content type and processing mode
   - Validate prompts before saving
   - Reset to default prompts
   - Export/import prompt configurations

3. **Live Testing**
   - Test configuration changes with sample content
   - Validate AI model connectivity
   - Monitor processing performance

4. **Status Monitoring**
   - View current configuration status
   - Monitor processing statistics
   - Track success rates and confidence scores

## Environment Variables

The system supports environment variable configuration for all parameters:

```bash
# Global Settings
AI_ENRICHMENT_ENABLED=true
AI_DEBUG_MODE=false

# Model Settings
AI_MODEL_PROVIDER=ollama
AI_MODEL_NAME=qwen2.5:7b
AI_MODEL_TEMPERATURE=0.3
OLLAMA_URL=http://localhost:11434

# Article Settings
AI_ARTICLES_ENABLED=true
AI_ARTICLES_BATCH_SIZE=10
AI_ARTICLES_MAX_PER_RUN=100
AI_ARTICLES_MIN_CONFIDENCE=0.7

# Post Settings
AI_POSTS_ENABLED=true
AI_POSTS_BATCH_SIZE=15
AI_POSTS_MAX_PER_RUN=200

# Comment Settings
AI_COMMENTS_ENABLED=true
AI_COMMENTS_BATCH_SIZE=25
AI_COMMENTS_MAX_PER_RUN=500
AI_COMMENTS_MODE=sentiment_only

# Rate Limiting
AI_REQUESTS_PER_MINUTE=20
AI_ARTICLES_PER_MINUTE=5
AI_POSTS_PER_MINUTE=8
AI_COMMENTS_PER_MINUTE=15
```

## Performance Optimization

### Recommended Settings

#### Production Environment
```python
# High throughput, balanced quality
articles:
  batch_size: 20
  max_items_per_run: 500
  processing_mode: "full"
  
posts:
  batch_size: 30
  max_items_per_run: 1000
  processing_mode: "full"
  
comments:
  batch_size: 50
  max_items_per_run: 2000
  processing_mode: "sentiment_only"

rate_limiting:
  requests_per_minute: 30
  base_delay_seconds: 2.0
```

#### Development Environment
```python
# Lower throughput, detailed logging
articles:
  batch_size: 5
  max_items_per_run: 50
  
rate_limiting:
  requests_per_minute: 10
  base_delay_seconds: 5.0
```

### Performance Metrics

Based on testing with qwen2.5:7b model:

- **Articles**: ~28 seconds per item (full enrichment)
- **Posts**: ~20 seconds per item (full enrichment)
- **Comments**: ~15 seconds per item (sentiment only)
- **Comments Enhanced**: ~40 seconds per item (full bilingual processing)

## Quality Control

### Content Validation
- Minimum/maximum content length checks
- Language detection and filtering
- Content quality scoring

### Response Validation
- JSON format validation
- Sentiment value validation
- Confidence score validation
- Required field presence checks

### Error Handling
- Graceful degradation on failures
- Fallback to simpler processing modes
- Comprehensive error logging
- Retry mechanisms with exponential backoff

## Migration from Legacy System

### Backward Compatibility

The new system maintains backward compatibility with existing enrichment services:

```python
# Legacy unified control settings still work
from config.unified_control import get_ai_enrichment_control
legacy_settings = get_ai_enrichment_control()

# New advanced configuration available
if legacy_settings.use_advanced_config:
    advanced_config = legacy_settings.get_advanced_config()
```

### Migration Steps

1. **Update Environment Variables**: Add new AI enrichment environment variables
2. **Test Configuration**: Use dashboard to validate new settings
3. **Gradual Migration**: Process content types one at a time
4. **Monitor Performance**: Track success rates and processing times
5. **Optimize Settings**: Adjust parameters based on performance data

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   ```bash
   # Check environment variables
   python -c "from config.ai_enrichment_config import get_ai_enrichment_config; print(get_ai_enrichment_config().to_dict())"
   ```

2. **Prompts Not Working**
   ```bash
   # Validate prompts
   python -c "from config.ai_enrichment_prompts import get_ai_enrichment_prompts; prompts = get_ai_enrichment_prompts(); print(prompts.validate_prompt('test prompt'))"
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check rate limiting status
   python configurable_batch_enrichment.py --status
   ```

4. **Model Connectivity**
   ```bash
   # Test Ollama connection
   curl http://localhost:11434/api/tags
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
# Environment variable
AI_DEBUG_MODE=true

# Or programmatically
config = get_ai_enrichment_config()
config.debug_mode = True
```

## Future Enhancements

### Planned Features

1. **Multi-Model Support**: Support for OpenAI, Anthropic, and other providers
2. **Advanced Scheduling**: Time-based processing schedules
3. **Performance Analytics**: Detailed performance tracking and optimization
4. **A/B Testing**: Compare different prompt and parameter configurations
5. **Auto-tuning**: Automatic parameter optimization based on performance data

### Integration Roadmap

1. **Vector Database Integration**: Enhanced semantic search capabilities
2. **Real-time Processing**: WebSocket-based real-time enrichment
3. **Multi-language Support**: Extended language support beyond Arabic and French
4. **Custom Models**: Support for fine-tuned models specific to Tunisian context

## Support

For issues, questions, or feature requests related to the AI enrichment configuration system:

1. Check the logs in `configurable_enrichment.log`
2. Use the dashboard testing interface
3. Validate configuration with the API endpoints
4. Review the comprehensive error messages and suggestions

The system is designed to be self-documenting and provides detailed error messages and suggestions for resolving configuration issues.
