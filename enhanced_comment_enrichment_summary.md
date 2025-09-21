# Enhanced Comment Enrichment for Tunisia Intelligence

## Overview

This document outlines the enhanced AI enrichment capabilities for social media comments, extending beyond basic sentiment analysis to include keyword extraction, named entity recognition, and French translations.

## Database Schema Changes

### New Columns Added to `social_media_comments`:

| Column | Type | Purpose |
|--------|------|---------|
| `keywords` | TEXT | Extracted keywords in original language (JSON) |
| `entities` | TEXT | Named entities extracted from comment (JSON) |
| `content_fr` | TEXT | French translation of comment content |
| `keywords_fr` | TEXT | Keywords translated to French (JSON) |
| `entities_fr` | TEXT | Entity names translated to French (JSON) |
| `language_detected` | TEXT | Detected language ('ar', 'fr', 'en', 'mixed') |
| `processing_time_ms` | INTEGER | AI processing time in milliseconds |
| `content_length` | INTEGER | Original content length in characters |
| `ai_model_version` | TEXT | AI model version used (default: 'qwen2.5:7b') |

### Performance Optimizations:

- **Indexes created** for language_detected, enriched_at, sentiment
- **Partial index** for enriched comments only
- **Constraints** for data validation (sentiment values, score ranges, language codes)

## Enhanced LLM Output Format

### Required JSON Structure for Comments:

```json
{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.72,
  "keywords": [
    {
      "text": "ممتاز",
      "importance": 0.85,
      "category": "opinion",
      "normalized_form": "excellent"
    },
    {
      "text": "الحكومة",
      "importance": 0.75,
      "category": "politics",
      "normalized_form": "government"
    }
  ],
  "entities": [
    {
      "text": "تونس",
      "type": "LOCATION",
      "canonical_name": "Tunisia",
      "confidence": 0.95,
      "context": "في تونس",
      "is_tunisian": true
    }
  ],
  "content_fr": "Excellent travail du gouvernement en Tunisie",
  "keywords_fr": [
    {
      "text": "excellent",
      "importance": 0.85,
      "category": "opinion",
      "original_text": "ممتاز"
    },
    {
      "text": "gouvernement",
      "importance": 0.75,
      "category": "politics",
      "original_text": "الحكومة"
    }
  ],
  "entities_fr": [
    {
      "text": "Tunisie",
      "type": "LOCATION",
      "canonical_name": "Tunisia",
      "confidence": 0.95,
      "original_text": "تونس",
      "is_tunisian": true
    }
  ],
  "language_detected": "ar",
  "confidence": 0.85,
  "processing_metadata": {
    "model_version": "qwen2.5:7b",
    "processing_time_ms": 1200,
    "content_length": 45
  }
}
```

## Key Features

### 1. **Bilingual Analysis**
- Original Arabic/mixed content analysis
- French translations for all text elements
- Keyword and entity translation with original text preservation

### 2. **Comprehensive Extraction**
- **Keywords**: Top 5 most important terms with importance scores
- **Entities**: Person, Organization, Location with Tunisian context awareness
- **Sentiment**: Enhanced with confidence scoring

### 3. **Cross-Language Linking**
- French translations maintain links to original Arabic text
- Consistent importance and confidence scores across languages
- Canonical entity names for standardization

### 4. **Performance Tracking**
- Processing time monitoring
- Content length analysis
- Model version tracking for quality assurance

## Implementation Steps

### 1. **Database Migration**
```sql
-- Run the SQL script
\i add_comments_enrichment_columns.sql
```

### 2. **Update AI Enrichment Service**
- Modify comment processing to use enhanced format
- Add French translation step
- Implement keyword and entity extraction for comments

### 3. **Update Processing Pipeline**
- Extend comment enrichment beyond sentiment-only
- Add bilingual processing capabilities
- Integrate with existing entity and keyword systems

## Benefits

### 1. **Enhanced Analytics**
- Deeper understanding of public sentiment in comments
- Entity tracking across all content types (articles, posts, comments)
- Keyword trend analysis from grassroots comments

### 2. **Cross-Source Intelligence**
- Official sentiment (government sources)
- Media sentiment (news articles)
- **People sentiment (social media comments)** ← Enhanced
- Entity mentions across all three sources

### 3. **Multilingual Insights**
- Arabic sentiment analysis with French accessibility
- Consistent entity recognition across languages
- Keyword trends in both Arabic and French

### 4. **Research Capabilities**
- Comment-level entity analysis
- Keyword frequency analysis in public discourse
- Sentiment correlation between posts and comments

## Performance Targets

- **Processing Time**: < 1.5 seconds per comment (enhanced from < 1 second)
- **Keyword Extraction**: Top 5 keywords per comment
- **Entity Recognition**: All persons, organizations, locations
- **Translation Quality**: Maintain semantic meaning in French
- **Overall Confidence**: > 0.7 average for enhanced processing

## Integration with Existing Systems

### 1. **Entity System**
- Comments now contribute to `entities` and `entity_mentions` tables
- Cross-source entity tracking includes comment mentions
- Enhanced entity frequency analysis

### 2. **Keyword System**
- Comments populate `keywords` and `content_keywords` tables
- Keyword trend analysis includes public discourse
- TF-IDF scoring across all content types

### 3. **Vector Database**
- Comment embeddings can be generated from French translations
- Semantic similarity search across articles, posts, and comments
- Enhanced content clustering capabilities

## Quality Assurance

### 1. **Data Validation**
- Database constraints ensure data integrity
- JSON validation for keyword and entity structures
- Language code validation

### 2. **Performance Monitoring**
- Processing time tracking per comment
- Success rate monitoring
- Error logging and retry mechanisms

### 3. **Content Quality**
- Confidence scoring for all extractions
- Original text preservation for verification
- Tunisian context prioritization

---

**This enhanced comment enrichment transforms social media comments from simple sentiment indicators into rich, analyzable content that contributes meaningfully to the Tunisia Intelligence cross-source analysis capabilities.**
