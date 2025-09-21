# Tunisia Intelligence Database Schema Reference

This file contains the exact database table structure as implemented in production.
Use this as the authoritative reference for all development work.

**Last Updated:** 2025-09-21  
**Source:** Production Database Schema

## Table Structure Overview

| Table Name | Purpose | Primary Data Source |
|------------|---------|-------------------|
| articles | Main news articles from RSS feeds | RSS Loader Module |
| content_analysis | AI-powered content analysis results | Automated AI Processing |
| content_categories | Hierarchical content categorization | Predefined SQL |
| content_embeddings | Vector embeddings for semantic search | Vectorization Module |
| content_enrichment_status | AI enrichment processing status | AI Enrichment Module |
| content_keywords | Keyword extraction and TF-IDF scoring | Automated AI Processing |
| enrichment_log | AI processing performance logs | AI Enrichment Module |
| enrichment_state | Batch processing state management | AI Enrichment Module |
| entities | Master entity registry | Automated AI Processing |
| entity_mentions | Cross-source entity tracking | Automated AI Processing |
| entity_types | Entity classification system | Predefined SQL |
| governorates | Tunisian geographic entities | Predefined SQL |
| keywords | Master keyword taxonomy | Automated AI Processing |
| parsing_log | RSS/Facebook scraping logs | RSS/Facebook Loader Modules |
| parsing_state | Scraping state management | RSS/Facebook Loader Modules |
| social_media_comments | Facebook post comments | Facebook Loader Module |
| social_media_post_reactions | Facebook post reaction counts | Facebook Loader Module |
| social_media_posts | Facebook posts content | Facebook Loader Module |
| sources | RSS feeds and Facebook pages registry | Predefined SQL |

---

## Detailed Table Schemas

### articles
**Purpose:** Main news articles from RSS feeds  
**Primary Source:** RSS Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | RSS loader module | Primary key |
| source_id | INTEGER | RSS loader module | Reference to sources table |
| title | TEXT | RSS loader module | Article title |
| description | TEXT | RSS loader module | Article description/summary |
| content | TEXT | RSS loader module | Full article content |
| link | TEXT | RSS loader module | Article URL |
| pub_date | TIMESTAMP | RSS loader module | Publication date |
| created_at | TIMESTAMP | RSS loader module | Record creation time |
| updated_at | TIMESTAMP | RSS loader module | Record update time |
| media_url | TEXT | RSS loader module | Associated media URL |
| content_hash | TEXT | RSS loader module | Content deduplication hash |
| guid | TEXT | RSS loader module | RSS GUID identifier |
| sentiment | TEXT | AI enrichment module | Sentiment label (positive/negative/neutral) |
| sentiment_score | FLOAT | AI enrichment module | Sentiment confidence score |
| keywords | TEXT | AI enrichment module | Extracted keywords |
| summary | TEXT | AI enrichment module | AI-generated summary |
| category | TEXT | AI enrichment module | Content category |
| category_id | INTEGER | RSS loader module | Reference to content_categories |
| enriched_at | TIMESTAMP | AI enrichment module | AI processing timestamp |
| enrichment_confidence | FLOAT | AI enrichment module | AI processing confidence |
| content_fr | TEXT | AI enrichment module | French translation |

### content_analysis
**Purpose:** AI-powered content analysis results  
**Primary Source:** Automated AI Processing

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Automated | Primary key |
| content_type | TEXT | Automated | Type of content (article/post/comment) |
| content_id | INTEGER | Automated | Reference to content record |
| sentiment | TEXT | Automated | Sentiment analysis result |
| sentiment_score | FLOAT | Automated | Sentiment confidence score |
| sentiment_confidence | FLOAT | Automated | Sentiment analysis confidence |
| primary_category_id | INTEGER | Automated | Primary category assignment |
| secondary_category_ids | INTEGER[] | Automated | Secondary categories |
| category_confidence | FLOAT | Automated | Category assignment confidence |
| language_detected | TEXT | Automated | Detected content language |
| processing_date | TIMESTAMP | Automated | Analysis processing date |
| ai_model_version | TEXT | Automated | AI model version used |
| processing_time_ms | INTEGER | Automated | Processing time in milliseconds |
| created_at | TIMESTAMP | Automated | Record creation time |

### content_categories
**Purpose:** Hierarchical content categorization system  
**Primary Source:** Predefined SQL

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Predefined SQL | Primary key |
| name_en | TEXT | Predefined SQL | Category name in English |
| name_ar | TEXT | Predefined SQL | Category name in Arabic |
| name_fr | TEXT | Predefined SQL | Category name in French |
| parent_id | INTEGER | Predefined SQL | Parent category for hierarchy |
| description | TEXT | Predefined SQL | Category description |
| created_at | TIMESTAMP | Predefined SQL | Record creation time |

### content_embeddings
**Purpose:** Vector embeddings for semantic search and similarity analysis  
**Primary Source:** Vectorization Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Vectorization module | Primary key |
| content_type | TEXT | Vectorization module | Type of content (article/post/comment) |
| content_id | INTEGER | Vectorization module | Reference to content record |
| embedding_model | TEXT | Vectorization module | Model used for embedding |
| embedding_version | TEXT | Vectorization module | Model version |
| content_length | INTEGER | Vectorization module | Original content length |
| embedding_quality_score | FLOAT | Vectorization module | Embedding quality assessment |
| created_at | TIMESTAMP | Vectorization module | Record creation time |
| updated_at | TIMESTAMP | Vectorization module | Record update time |
| language | TEXT | Vectorization module | Content language |
| content_hash | TEXT | Vectorization module | Content hash for deduplication |
| content_embedding | VECTOR | Vectorization module | Main content vector embedding |
| title_embedding | VECTOR | Vectorization module | Title-specific embedding |
| entity_embedding | VECTOR | Vectorization module | Entity-focused embedding |

### content_enrichment_status
**Purpose:** AI enrichment processing status and tracking  
**Primary Source:** AI Enrichment Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | AI enrichment module | Primary key |
| content_type | TEXT | AI enrichment module | Type of content |
| content_id | INTEGER | AI enrichment module | Reference to content record |
| content_hash | TEXT | AI enrichment module | Content hash |
| is_enriched | BOOLEAN | AI enrichment module | Enrichment completion status |
| enrichment_version | TEXT | AI enrichment module | Enrichment version |
| last_enriched_at | TIMESTAMP | AI enrichment module | Last enrichment timestamp |
| enrichment_attempts | INTEGER | AI enrichment module | Number of attempts |
| last_attempt_at | TIMESTAMP | AI enrichment module | Last attempt timestamp |
| last_error_message | TEXT | AI enrichment module | Last error message |
| has_sentiment | BOOLEAN | AI enrichment module | Sentiment analysis completed |
| has_entities | BOOLEAN | AI enrichment module | Entity extraction completed |
| has_keywords | BOOLEAN | AI enrichment module | Keyword extraction completed |
| has_category | BOOLEAN | AI enrichment module | Category classification completed |
| has_embedding | BOOLEAN | AI enrichment module | Vector embedding completed |
| enrichment_confidence | FLOAT | AI enrichment module | Overall enrichment confidence |
| processing_time_ms | INTEGER | AI enrichment module | Processing time |
| created_at | TIMESTAMP | AI enrichment module | Record creation time |
| updated_at | TIMESTAMP | AI enrichment module | Record update time |

### content_keywords
**Purpose:** Keyword extraction with TF-IDF scoring  
**Primary Source:** Automated AI Processing

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Automated | Primary key |
| content_type | TEXT | Automated | Type of content |
| content_id | INTEGER | Automated | Reference to content record |
| keyword_id | INTEGER | Automated | Reference to keywords table |
| importance_score | FLOAT | Automated | Keyword importance score |
| tf_score | FLOAT | Automated | Term frequency score |
| tf_idf_score | FLOAT | Automated | TF-IDF score |
| position_first | INTEGER | Automated | First occurrence position |
| occurrence_count | INTEGER | Automated | Total occurrences |
| created_at | TIMESTAMP | Automated | Record creation time |

### enrichment_log
**Purpose:** AI processing performance and batch operation logs  
**Primary Source:** AI Enrichment Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | AI enrichment module | Primary key |
| content_type | TEXT | AI enrichment module | Type of content processed |
| source_id | INTEGER | AI enrichment module | Source identifier |
| started_at | TIMESTAMP | AI enrichment module | Processing start time |
| finished_at | TIMESTAMP | AI enrichment module | Processing end time |
| processing_duration_ms | INTEGER | AI enrichment module | Total processing time |
| items_processed | INTEGER | AI enrichment module | Total items processed |
| items_successful | INTEGER | AI enrichment module | Successfully processed items |
| items_failed | INTEGER | AI enrichment module | Failed items |
| items_skipped | INTEGER | AI enrichment module | Skipped items |
| ai_model_used | TEXT | AI enrichment module | AI model identifier |
| ai_model_version | TEXT | AI enrichment module | AI model version |
| average_processing_time_ms | INTEGER | AI enrichment module | Average processing time per item |
| average_confidence_score | FLOAT | AI enrichment module | Average confidence score |
| batch_size | INTEGER | AI enrichment module | Batch size used |
| processing_mode | TEXT | AI enrichment module | Processing mode |
| status | TEXT | AI enrichment module | Overall batch status |
| error_message | TEXT | AI enrichment module | Error message if failed |
| error_count | INTEGER | AI enrichment module | Number of errors |
| memory_usage_mb | FLOAT | AI enrichment module | Memory usage |
| cpu_usage_percent | FLOAT | AI enrichment module | CPU usage |

### enrichment_state
**Purpose:** Batch processing state management  
**Primary Source:** AI Enrichment Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | AI enrichment module | Primary key |
| content_type | TEXT | AI enrichment module | Type of content |
| source_id | INTEGER | AI enrichment module | Source identifier |
| last_enriched_content_id | INTEGER | AI enrichment module | Last processed content ID |
| last_enriched_at | TIMESTAMP | AI enrichment module | Last processing timestamp |
| last_enriched_content_hash | TEXT | AI enrichment module | Last processed content hash |
| enrichment_enabled | BOOLEAN | AI enrichment module | Enrichment enabled flag |
| auto_enrich_new_content | BOOLEAN | AI enrichment module | Auto-enrichment flag |
| total_items_processed | INTEGER | AI enrichment module | Total processed items |
| successful_enrichments | INTEGER | AI enrichment module | Successful enrichments |
| failed_enrichments | INTEGER | AI enrichment module | Failed enrichments |
| last_batch_size | INTEGER | AI enrichment module | Last batch size |
| created_at | TIMESTAMP | AI enrichment module | Record creation time |
| updated_at | TIMESTAMP | AI enrichment module | Record update time |

### entities
**Purpose:** Master entity registry with canonical names  
**Primary Source:** Automated AI Processing

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Automated | Primary key |
| canonical_name | TEXT | AI enrichment module | Canonical entity name |
| entity_type_id | INTEGER | Automated | Reference to entity_types |
| governorate_id | INTEGER | Automated | Reference to governorates |
| aliases | TEXT[] | AI enrichment module | Entity aliases |
| confidence_score | FLOAT | AI enrichment module | Entity confidence score |
| is_canonical | BOOLEAN | AI enrichment module | Canonical entity flag |
| canonical_entity_id | INTEGER | Automated | Reference to canonical entity |
| external_ids | JSONB | Automated | External system identifiers |
| metadata | JSONB | Automated | Additional metadata |
| created_at | TIMESTAMP | Automated | Record creation time |
| updated_at | TIMESTAMP | Automated | Record update time |

### entity_mentions
**Purpose:** Cross-source entity tracking and mentions  
**Primary Source:** Automated AI Processing

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Automated | Primary key |
| entity_id | INTEGER | Automated | Reference to entities table |
| content_type | TEXT | Automated | Type of content |
| content_id | INTEGER | Automated | Reference to content record |
| mentioned_text | TEXT | Automated | Actual mentioned text |
| context_snippet | TEXT | Automated | Surrounding context |
| position_start | INTEGER | Automated | Start position in content |
| position_end | INTEGER | Automated | End position in content |
| entity_sentiment | TEXT | Automated | Entity-specific sentiment |
| entity_sentiment_score | FLOAT | Automated | Entity sentiment score |
| extraction_confidence | FLOAT | Automated | Extraction confidence |
| created_at | TIMESTAMP | Automated | Record creation time |

### entity_types
**Purpose:** Entity classification system  
**Primary Source:** Predefined SQL

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Predefined SQL | Primary key |
| name | TEXT | Predefined SQL | Entity type name |
| description | TEXT | Predefined SQL | Entity type description |
| created_at | TIMESTAMP | Predefined SQL | Record creation time |

### governorates
**Purpose:** Tunisian geographic entities  
**Primary Source:** Predefined SQL

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Predefined SQL | Primary key |
| name_ar | TEXT | Predefined SQL | Name in Arabic |
| name_en | TEXT | Predefined SQL | Name in English |
| name_fr | TEXT | Predefined SQL | Name in French |
| code | TEXT | Predefined SQL | Governorate code |
| population | INTEGER | Predefined SQL | Population count |
| area_km2 | FLOAT | Predefined SQL | Area in square kilometers |
| created_at | TIMESTAMP | Predefined SQL | Record creation time |

### keywords
**Purpose:** Master keyword taxonomy  
**Primary Source:** Automated AI Processing

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Automated | Primary key |
| keyword | TEXT | AI enrichment module | Keyword text |
| normalized_form | TEXT | AI enrichment module | Normalized keyword form |
| category_id | INTEGER | Automated | Reference to content_categories |
| language | TEXT | Automated | Keyword language |
| parent_id | INTEGER | Automated | Parent keyword for hierarchy |
| frequency_count | INTEGER | Automated | Usage frequency |
| idf_score | FLOAT | Automated | Inverse document frequency |
| is_stopword | BOOLEAN | Automated | Stopword flag |
| created_at | TIMESTAMP | Automated | Record creation time |

### parsing_log
**Purpose:** RSS and Facebook scraping operation logs  
**Primary Source:** RSS Loader Module, Facebook Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | RSS/Facebook loader modules | Primary key |
| source_id | INTEGER | RSS/Facebook loader modules | Reference to sources table |
| source_type | TEXT | RSS/Facebook loader modules | Type of source (rss/facebook) |
| processing_type | TEXT | RSS/Facebook loader modules | Processing type |
| started_at | TIMESTAMP | RSS/Facebook loader modules | Processing start time |
| finished_at | TIMESTAMP | RSS/Facebook loader modules | Processing end time |
| articles_fetched | INTEGER | RSS/Facebook loader modules | Number of articles fetched |
| posts_fetched | INTEGER | RSS/Facebook loader modules | Number of posts fetched |
| comments_fetched | INTEGER | RSS/Facebook loader modules | Number of comments fetched |
| status | TEXT | RSS/Facebook loader modules | Processing status |
| error_message | TEXT | RSS/Facebook loader modules | Error message if failed |
| facebook_page_id | TEXT | RSS/Facebook loader modules | Facebook page identifier |

### parsing_state
**Purpose:** RSS and Facebook scraping state management  
**Primary Source:** RSS Loader Module, Facebook Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | RSS/Facebook loader modules | Primary key |
| source_id | INTEGER | RSS/Facebook loader modules | Reference to sources table |
| source_type | TEXT | RSS/Facebook loader modules | Type of source |
| last_parsed_at | TIMESTAMP | RSS/Facebook loader modules | Last parsing timestamp |
| last_article_link | TEXT | RSS/Facebook loader modules | Last processed article link |
| last_article_guid | TEXT | RSS/Facebook loader modules | Last processed article GUID |
| last_post_id | TEXT | RSS/Facebook loader modules | Last processed post ID |
| last_comment_id | TEXT | RSS/Facebook loader modules | Last processed comment ID |
| facebook_page_id | TEXT | RSS/Facebook loader modules | Facebook page identifier |
| last_processed_timestamp | TIMESTAMP | RSS/Facebook loader modules | Last processing timestamp |
| updated_at | TIMESTAMP | RSS/Facebook loader modules | Record update time |

### social_media_comments
**Purpose:** Facebook post comments  
**Primary Source:** Facebook Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Facebook loader module | Primary key |
| post_id | INTEGER | Facebook loader module | Reference to social_media_posts |
| platform_comment_id | TEXT | Facebook loader module | Facebook comment ID |
| content | TEXT | Facebook loader module | Comment content |
| comment_date | TIMESTAMP | Facebook loader module | Comment date |
| relevance | FLOAT | Facebook loader module | Comment relevance score |
| author_name | TEXT | Facebook loader module | Comment author name |
| content_hash | TEXT | Facebook loader module | Content deduplication hash |
| created_at | TIMESTAMP | Facebook loader module | Record creation time |
| sentiment | TEXT | AI enrichment module | Comment sentiment |
| sentiment_score | FLOAT | AI enrichment module | Sentiment confidence score |
| enriched_at | TIMESTAMP | AI enrichment module | AI processing timestamp |
| enrichment_confidence | FLOAT | AI enrichment module | AI processing confidence |
| keywords | TEXT | AI enrichment module | Extracted keywords (JSON array) |
| entities | TEXT | AI enrichment module | Named entities (JSON array) |
| content_fr | TEXT | AI enrichment module | French translation of comment |
| keywords_fr | TEXT | AI enrichment module | Keywords translated to French (JSON array) |
| entities_fr | TEXT | AI enrichment module | Entities translated to French (JSON array) |
| language_detected | TEXT | AI enrichment module | Detected language of content |
| processing_time_ms | INTEGER | AI enrichment module | AI processing time in milliseconds |
| content_length | INTEGER | AI enrichment module | Original content length in characters |
| ai_model_version | TEXT | AI enrichment module | AI model version used for enrichment |

### social_media_post_reactions
**Purpose:** Facebook post reaction counts  
**Primary Source:** Facebook Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Facebook loader module | Primary key |
| post_id | INTEGER | Facebook loader module | Reference to social_media_posts |
| reaction_type | TEXT | Facebook loader module | Type of reaction (like, love, etc.) |
| count | INTEGER | Facebook loader module | Reaction count |

### social_media_posts
**Purpose:** Facebook posts content  
**Primary Source:** Facebook Loader Module

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Facebook loader module | Primary key |
| source_id | INTEGER | Facebook loader module | Reference to sources table |
| social_media | TEXT | Facebook loader module | Social media platform |
| account | TEXT | Facebook loader module | Account name |
| platform_post_id | TEXT | Facebook loader module | Facebook post ID |
| content | TEXT | Facebook loader module | Post content |
| url | TEXT | Facebook loader module | Post URL |
| publish_date | TIMESTAMP | Facebook loader module | Publication date |
| created_at | TIMESTAMP | Facebook loader module | Record creation time |
| updated_at | TIMESTAMP | Facebook loader module | Record update time |
| content_hash | TEXT | Facebook loader module | Content deduplication hash |
| sentiment | TEXT | AI enrichment module | Post sentiment |
| sentiment_score | FLOAT | AI enrichment module | Sentiment confidence score |
| summary | TEXT | AI enrichment module | AI-generated summary |
| category_id | INTEGER | Facebook loader module | Reference to content_categories |
| enriched_at | TIMESTAMP | AI enrichment module | AI processing timestamp |
| enrichment_confidence | FLOAT | AI enrichment module | AI processing confidence |
| content_fr | TEXT | AI enrichment module | French translation |
| keywords | TEXT | AI enrichment module | Extracted keywords |

### sources
**Purpose:** RSS feeds and Facebook pages registry  
**Primary Source:** Predefined SQL

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| id | INTEGER | Predefined SQL | Primary key |
| name | TEXT | Predefined SQL | Source name |
| url | TEXT | Predefined SQL | Source URL |
| source_type | TEXT | Predefined SQL | Type (rss/facebook) |
| language | TEXT | Predefined SQL | Source language |
| country | TEXT | Predefined SQL | Source country |
| category | TEXT | Predefined SQL | Source category |
| is_active | BOOLEAN | Predefined SQL | Active status |
| rss_url | TEXT | Predefined SQL | RSS feed URL |
| page_name | TEXT | Predefined SQL | Facebook page name |
| page_id | TEXT | Predefined SQL | Facebook page ID |
| username | TEXT | Predefined SQL | Username |
| about | TEXT | Predefined SQL | Source description |
| priority | INTEGER | Predefined SQL | Processing priority |
| fetch_frequency_minutes | INTEGER | Predefined SQL | Fetch frequency |
| last_successful_fetch | TIMESTAMP | Predefined SQL | Last successful fetch |
| consecutive_failures | INTEGER | Predefined SQL | Consecutive failure count |
| created_at | TIMESTAMP | Predefined SQL | Record creation time |
| updated_at | TIMESTAMP | Predefined SQL | Record update time |

---

## Development Guidelines

### Table Naming Convention
- Use exact table names as specified above
- Primary content table is `articles` (not `news_articles`)
- All table names are lowercase with underscores

### Key Relationships
- `articles.source_id` → `sources.id`
- `content_embeddings.content_id` → `articles.id` (when content_type = 'article')
- `content_analysis.content_id` → `articles.id` (when content_type = 'article')
- `entity_mentions.content_id` → `articles.id` (when content_type = 'article')

### AI Enrichment Pipeline
1. Content ingested via RSS/Facebook loaders
2. `content_enrichment_status` tracks processing state
3. AI modules populate analysis tables
4. Vector embeddings generated in `content_embeddings`
5. Performance logged in `enrichment_log`

### Cross-Source Analytics
- Articles (official/media sources)
- Social media posts (Facebook pages)
- Social media comments (public sentiment)
- All linked via entity mentions and semantic embeddings

---

**Note:** This schema supports the complete Tunisia Intelligence analysis pipeline including sentiment analysis, entity tracking, semantic similarity, and cross-source correlation analysis.
