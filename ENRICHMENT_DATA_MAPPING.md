# LLM Enrichment Data Mapping

This document explains how LLM enrichment output is comprehensively stored across all destination tables in the Tunisia Intelligence database schema.

## Overview

The **Comprehensive Enrichment Service** ensures that every piece of LLM output is properly stored in the appropriate database tables, creating a complete audit trail and enabling advanced analytics.

## LLM Output Structure

The streamlined French enricher produces the following output:

```json
{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": 0.7,
    "confidence": 0.85,
    "summary": "French summary text...",
    "keywords": ["économie", "Kaïs Saïed", "mesures", "Tunisie"],
    "category": "Économie",
    "entities": [
        {"text": "Kaïs Saïed", "type": "PERSON", "confidence": 0.98},
        {"text": "Tunisie", "type": "LOCATION", "confidence": 0.95}
    ],
    "detected_language": "ar",
    "translation_needed": true,
    "content_fr": "French translation if needed..."
}
```

## Database Storage Mapping

### 1. Primary Content Tables

#### `articles` Table
**Purpose**: Main article content and basic enrichment
```sql
UPDATE articles SET
    sentiment = 'positif',                    -- LLM sentiment label (French)
    sentiment_score = 0.7,                    -- LLM sentiment score (-1.0 to 1.0)
    keywords = '["économie", "Kaïs Saïed"]',  -- LLM keywords as JSON (French)
    summary = 'Résumé français...',           -- LLM summary (French)
    category = 'Économie',                    -- LLM category (French)
    category_id = 2,                          -- Mapped category ID
    enriched_at = NOW(),                      -- Processing timestamp
    enrichment_confidence = 0.85,             -- LLM confidence score
    content_fr = 'Translation...'             -- French translation (if needed)
WHERE id = article_id;
```

#### `social_media_posts` Table
**Purpose**: Social media post content and enrichment
```sql
UPDATE social_media_posts SET
    sentiment = 'positif',
    sentiment_score = 0.7,
    summary = 'Résumé français...',
    category_id = 2,
    enriched_at = NOW(),
    enrichment_confidence = 0.85,
    content_fr = 'Translation...'
WHERE id = post_id;
```

#### `social_media_comments` Table
**Purpose**: Comment sentiment analysis (metadata only)
```sql
UPDATE social_media_comments SET
    sentiment = 'positif',
    sentiment_score = 0.7,
    enriched_at = NOW(),
    enrichment_confidence = 0.85
WHERE id = comment_id;
```

### 2. Detailed Analysis Tables

#### `content_analysis` Table
**Purpose**: Comprehensive analysis metadata for all content types
```sql
INSERT INTO content_analysis (
    content_type,           -- 'article', 'post', 'comment'
    content_id,             -- Reference to source content
    sentiment,              -- English sentiment for analysis ('positive', 'negative', 'neutral')
    sentiment_score,        -- LLM sentiment score
    sentiment_confidence,   -- LLM confidence
    primary_category_id,    -- Mapped category ID
    language_detected,      -- Original language detected
    ai_model_version,       -- 'qwen2.5:7b'
    processing_time_ms      -- Processing duration
) VALUES (...);
```

#### `content_keywords` Table
**Purpose**: Keyword relationships and importance scoring
```sql
-- For each keyword in LLM output:
INSERT INTO content_keywords (
    content_type,           -- 'article', 'post', 'comment'
    content_id,             -- Reference to source content
    keyword_id,             -- Reference to keywords table
    importance_score,       -- Calculated from position (1.0 - 0.1*position)
    occurrence_count,       -- Always 1 for new extractions
    position_first          -- Position in keyword list (1, 2, 3...)
) VALUES (...);
```

#### `entity_mentions` Table
**Purpose**: Entity extraction and context tracking
```sql
-- For each entity in LLM output:
INSERT INTO entity_mentions (
    entity_id,              -- Reference to entities table
    content_type,           -- 'article', 'post', 'comment'
    content_id,             -- Reference to source content
    mentioned_text,         -- Exact text as found by LLM
    context_snippet,        -- Surrounding text context
    position_start,         -- Character position in content
    position_end,           -- End character position
    extraction_confidence   -- LLM entity confidence
) VALUES (...);
```

### 3. Master Reference Tables

#### `keywords` Table
**Purpose**: Master keyword registry
```sql
-- Auto-created for new keywords:
INSERT INTO keywords (
    keyword,                -- French keyword from LLM
    normalized_form,        -- Lowercase version
    language,               -- 'fr'
    frequency_count         -- Incremented on each use
) VALUES (...);
```

#### `entities` Table
**Purpose**: Master entity registry
```sql
-- Auto-created for new entities:
INSERT INTO entities (
    canonical_name,         -- Entity name from LLM
    entity_type_id,         -- Mapped type (PERSON, LOCATION, etc.)
    confidence_score,       -- Average confidence
    is_canonical           -- TRUE for new entities
) VALUES (...);
```

#### `content_categories` Table
**Purpose**: Multilingual category definitions
```sql
-- Pre-populated with French categories:
INSERT INTO content_categories (
    name_en, name_ar, name_fr
) VALUES 
    ('politics', 'سياسة', 'Politique'),
    ('economy', 'اقتصاد', 'Économie'),
    ('society', 'مجتمع', 'Société'),
    -- ... etc
```

### 4. Tracking and Monitoring Tables

#### `content_enrichment_status` Table
**Purpose**: Enrichment status tracking per content item
```sql
INSERT INTO content_enrichment_status (
    content_type,           -- 'article', 'post', 'comment'
    content_id,             -- Reference to source content
    is_enriched,            -- TRUE after successful processing
    enrichment_version,     -- 'qwen2.5:7b'
    last_enriched_at,       -- Processing timestamp
    has_sentiment,          -- TRUE if sentiment extracted
    has_entities,           -- TRUE if entities extracted
    has_keywords,           -- TRUE if keywords extracted
    has_category,           -- TRUE if category assigned
    enrichment_confidence,  -- Overall LLM confidence
    processing_time_ms      -- Processing duration
) VALUES (...);
```

#### `enrichment_log` Table
**Purpose**: Batch processing statistics
```sql
INSERT INTO enrichment_log (
    content_type,           -- Type of content processed
    items_processed,        -- Total items in batch
    items_successful,       -- Successfully enriched
    items_failed,           -- Failed enrichments
    processing_duration_ms, -- Total batch time
    ai_model_version,       -- 'qwen2.5:7b'
    average_processing_time_ms, -- Per-item average
    status                  -- 'success', 'partial', 'failed'
) VALUES (...);
```

## Data Flow Process

### Step 1: Content Processing
1. **Input**: Original content (Arabic, French, or English)
2. **Language Detection**: Automatic detection
3. **Translation**: Arabic/English → French (if needed)
4. **Enrichment**: LLM analysis in French

### Step 2: Database Storage
1. **Primary Table Update**: Store main enrichment in content table
2. **Analysis Record**: Create detailed analysis record
3. **Keyword Processing**: Extract and link keywords
4. **Entity Processing**: Extract and link entities
5. **Status Tracking**: Update enrichment status

### Step 3: Reference Management
1. **Auto-create Keywords**: New keywords added to master table
2. **Auto-create Entities**: New entities added to master table
3. **Category Mapping**: French categories mapped to IDs
4. **Relationship Linking**: All relationships properly established

## Analytics Capabilities

With this comprehensive storage approach, you can perform:

### Cross-Source Sentiment Analysis
```sql
-- Compare sentiment across content types
SELECT 
    content_type,
    AVG(sentiment_score) as avg_sentiment,
    COUNT(*) as total_items
FROM content_analysis 
WHERE processing_date >= '2025-01-01'
GROUP BY content_type;
```

### Entity Tracking Across Sources
```sql
-- Track entity mentions across all content
SELECT 
    e.canonical_name,
    COUNT(em.id) as mention_count,
    AVG(em.extraction_confidence) as avg_confidence
FROM entities e
JOIN entity_mentions em ON e.id = em.entity_id
GROUP BY e.canonical_name
ORDER BY mention_count DESC;
```

### Keyword Trend Analysis
```sql
-- Track keyword frequency over time
SELECT 
    k.keyword,
    COUNT(ck.id) as usage_count,
    AVG(ck.importance_score) as avg_importance
FROM keywords k
JOIN content_keywords ck ON k.id = ck.keyword_id
GROUP BY k.keyword
ORDER BY usage_count DESC;
```

### Processing Performance Monitoring
```sql
-- Monitor enrichment performance
SELECT 
    DATE(started_at) as processing_date,
    SUM(items_processed) as total_processed,
    AVG(average_processing_time_ms) as avg_time_per_item,
    SUM(items_failed) as total_failures
FROM enrichment_log
GROUP BY DATE(started_at)
ORDER BY processing_date DESC;
```

## Quality Assurance

### Data Integrity Checks
1. **Referential Integrity**: All foreign keys properly maintained
2. **Constraint Validation**: French sentiment labels enforced
3. **Completeness Tracking**: Status table tracks what was enriched
4. **Error Logging**: Failed enrichments logged with details

### Performance Optimization
1. **Batch Processing**: Multiple items processed efficiently
2. **Duplicate Prevention**: Existing keywords/entities reused
3. **Index Optimization**: Proper indexing on lookup columns
4. **Memory Management**: Efficient data structures used

## Usage Examples

### Process Articles
```python
from comprehensive_enrichment_service import ComprehensiveEnrichmentService

service = ComprehensiveEnrichmentService(ollama_client, db_manager)

# Process single article
success = service.process_article({
    'id': 123,
    'title': 'Article title',
    'content': 'Article content...'
})

# All tables automatically updated with enrichment data
```

### Batch Processing
```python
# Process multiple articles
articles = get_articles_to_process(limit=50)
for article in articles:
    service.process_article(article)

# Comprehensive logging and tracking maintained
```

This comprehensive approach ensures that every piece of LLM output is properly stored, tracked, and available for advanced analytics across the Tunisia Intelligence system.

## State Management Benefits

### Automatic Deduplication
- **Content Hashes**: Prevent reprocessing of identical content
- **State Tracking**: Track last processed item per source
- **Batch Coordination**: Avoid overlapping batch processing

### Performance Monitoring
- **Real-time Metrics**: Track success rates per source
- **Historical Analysis**: Analyze processing trends over time
- **Resource Usage**: Monitor processing time and efficiency
- **Error Tracking**: Identify problematic sources or content types

### Operational Intelligence
- **Source Health**: Monitor which sources are being enriched successfully
- **Processing Bottlenecks**: Identify slow or failing enrichment processes
- **Capacity Planning**: Analyze processing volumes and times
- **Quality Assurance**: Track enrichment confidence and accuracy

### Automated Recovery
- **Failure Tracking**: Automatic retry logic based on failure counts
- **State Restoration**: Resume processing from last successful point
- **Error Isolation**: Isolate problematic content without stopping batch
- **Graceful Degradation**: Continue processing even with partial failures
