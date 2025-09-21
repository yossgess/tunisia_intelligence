{{ ... }}
## 2. Social Media Comments (Enhanced Enrichment)

### Required LLM Output Format:

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

### Field Specifications:

#### **sentiment** (Required)
- **Type:** String
- **Values:** `"positive"`, `"negative"`, `"neutral"`
- **Database:** `social_media_comments.sentiment`

#### **sentiment_score** (Required)
- **Type:** Float
- **Range:** 0.0 to 1.0
- **Database:** `social_media_comments.sentiment_score`

#### **keywords** (Required)
- **Type:** Array of objects
- **Max Items:** 5 (top keywords for comments)
- **Database:** `social_media_comments.keywords` (stored as JSON string)
- **Object Structure:** Same as articles/posts

#### **entities** (Required)
- **Type:** Array of objects
- **Database:** `social_media_comments.entities` (stored as JSON string)
- **Object Structure:** Same as articles/posts

#### **content_fr** (Required)
- **Type:** String
- **Database:** `social_media_comments.content_fr`
- **Description:** French translation of comment content

#### **keywords_fr** (Required)
- **Type:** Array of objects
- **Database:** `social_media_comments.keywords_fr` (stored as JSON string)
- **Object Structure:**
  - `text` (string): Keyword in French
  - `importance` (float): Same as original
  - `category` (string): Same as original
  - `original_text` (string): Original Arabic/mixed text

#### **entities_fr** (Required)
- **Type:** Array of objects
- **Database:** `social_media_comments.entities_fr` (stored as JSON string)
- **Object Structure:**
  - `text` (string): Entity name in French
  - `type` (string): Same as original
  - `canonical_name` (string): Standardized name
  - `confidence` (float): Same as original
  - `original_text` (string): Original Arabic text
  - `is_tunisian` (boolean): Same as original

#### **confidence** (Required)
- **Type:** Float
- **Range:** 0.0 to 1.0
- **Database:** `social_media_comments.enrichment_confidence`

#### **language_detected** (Required)
- **Type:** String
- **Values:** `"ar"`, `"fr"`, `"en"`, `"mixed"`
- **Database:** `social_media_comments.language_detected`

#### **processing_metadata** (Required)
- **Type:** Object
- **Database:** Multiple fields in `social_media_comments`
- **Object Structure:**
  - `model_version` (string): → `ai_model_version`
  - `processing_time_ms` (integer): → `processing_time_ms`
  - `content_length` (integer): → `content_length`
{{ ... }}
