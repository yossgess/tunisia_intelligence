# AI Enrichment Module for Tunisia Intelligence

A comprehensive AI-powered content enrichment system that provides sentiment analysis, named entity recognition, keyword extraction, and category classification for Arabic, French, and English content from Tunisian sources.

## 🚀 Features

### AI Processing Capabilities
- **Sentiment Analysis**: Analyze emotional tone and sentiment in multilingual content
- **Named Entity Recognition (NER)**: Extract persons, organizations, and locations
- **Keyword Extraction**: Identify important terms and key phrases
- **Category Classification**: Classify content into predefined categories
- **Multilingual Support**: Arabic, French, English, and mixed-language content

### Integration Points
- **RSS Articles**: Automatic enrichment of scraped news articles
- **Social Media Posts**: Facebook posts and comments analysis
- **Batch Processing**: Process existing content in bulk
- **Real-time Processing**: Enrich new content as it's scraped

### Technical Features
- **Local LLM**: Uses Ollama with qwen2.5:7b model for privacy and performance
- **Database Integration**: Seamless integration with existing Supabase schema
- **Parallel Processing**: Multi-threaded processing for efficiency
- **Error Handling**: Robust error handling and retry logic
- **CLI Tools**: Command-line interface for management and testing

## 📁 Module Structure

```
ai_enrichment/
├── __init__.py                 # Main module exports
├── core/                       # Core components
│   ├── ollama_client.py       # Ollama LLM integration
│   ├── base_processor.py      # Abstract base for processors
│   └── prompt_templates.py    # LLM prompt templates
├── processors/                 # AI processing components
│   ├── sentiment_analyzer.py  # Sentiment analysis
│   ├── entity_extractor.py    # Named entity recognition
│   ├── keyword_extractor.py   # Keyword extraction
│   └── category_classifier.py # Category classification
├── models/                     # Data models
│   └── enrichment_models.py   # Pydantic models for results
├── services/                   # High-level services
│   ├── enrichment_service.py  # Main orchestration service
│   └── batch_processor.py     # Batch processing service
├── cli/                        # Command-line interface
│   └── enrichment_cli.py      # CLI implementation
└── examples/                   # Integration examples
    ├── basic_usage.py         # Basic usage examples
    ├── rss_integration.py     # RSS integration patterns
    └── facebook_integration.py # Facebook integration patterns
```

## 🛠️ Installation

### Prerequisites
1. **Ollama**: Install and run Ollama locally
   ```bash
   # Install Ollama (see https://ollama.ai)
   ollama serve
   
   # Pull the required model
   ollama pull qwen2.5:7b
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies Added
The following dependencies have been added to `requirements.txt`:
```
# AI/LLM dependencies for enrichment module
ollama>=0.3.0
langchain>=0.1.0
langchain-community>=0.0.20
tiktoken>=0.5.0

# Text processing for AI enrichment
spacy>=3.7.0
nltk>=3.8.0
```

## 🚀 Quick Start

### 1. Test the System
```bash
# Test all processors
python ai_enrich.py test

# Test specific processor
python ai_enrich.py test --processor sentiment

# Check service status
python ai_enrich.py status
```

### 2. Enrich Single Content
```bash
# Enrich Arabic text
python ai_enrich.py enrich "الحكومة التونسية تعلن عن إجراءات اقتصادية جديدة"

# Enrich with JSON output
python ai_enrich.py enrich "Le gouvernement annonce de nouvelles mesures" --output json
```

### 3. Batch Processing
```bash
# Process recent articles
python ai_enrich.py batch articles --limit 100 --days-back 7

# Process social media posts
python ai_enrich.py batch posts --limit 50 --account "TunisianGovernment"

# Get processing statistics
python ai_enrich.py stats --type articles --days 30
```

## 💻 Programming Usage

### Basic Enrichment
```python
from ai_enrichment import EnrichmentService

# Initialize service
service = EnrichmentService()

# Enrich content
result = service.enrich_content(
    content="الحكومة التونسية تعلن عن إجراءات جديدة",
    content_type="article"
)

# Access results
if result.status.value == 'success':
    print(f"Sentiment: {result.sentiment.sentiment.value}")
    print(f"Entities: {[e.text for e in result.entities]}")
    print(f"Keywords: {[k.text for k in result.keywords]}")
    print(f"Category: {result.category.primary_category}")
```

### Individual Processors
```python
from ai_enrichment.processors import SentimentAnalyzer, EntityExtractor

# Use individual processors
sentiment_analyzer = SentimentAnalyzer()
entity_extractor = EntityExtractor()

# Process content
sentiment_result = sentiment_analyzer.process("نص للتحليل")
entity_result = entity_extractor.process("نص للتحليل")
```

### Batch Processing
```python
from ai_enrichment.services.batch_processor import BatchProcessor

# Initialize batch processor
batch_processor = BatchProcessor()

# Process articles
result = batch_processor.process_articles(
    limit=100,
    days_back=7,
    force_reprocess=False
)

print(f"Processed: {result.successful_items}/{result.total_items}")
print(f"Success rate: {result.success_rate:.1%}")
```

## 🔗 Integration Examples

### RSS Integration
```python
from ai_enrichment.examples.rss_integration import EnrichedRSSLoader

# Create enriched RSS loader
loader = EnrichedRSSLoader(config={
    'enrich_on_insert': True,
    'min_content_length': 100
})

# Insert and enrich article
article = Article(title="...", content="...", link="...")
enriched_article = loader.insert_article_with_enrichment(article)
```

### Facebook Integration
```python
from ai_enrichment.examples.facebook_integration import EnrichedFacebookLoader

# Create enriched Facebook loader
loader = EnrichedFacebookLoader(config={
    'enrich_posts': True,
    'enrich_comments': True,
    'enrich_high_engagement_only': True
})

# Insert and enrich post
post_data = {'content': '...', 'account': '...'}
enriched_post = loader.insert_post_with_enrichment(post_data)
```

## 📊 Database Integration

The AI enrichment module integrates seamlessly with your existing database schema:

### Articles Table Updates
- `sentiment`: Populated with sentiment labels (positive/negative/neutral)
- `keywords`: JSON string of extracted keywords
- `summary`: AI-generated summaries (optional)
- `category`: Primary category classification

### Social Media Posts Updates
- `sentiment_score`: Numerical sentiment score
- `summary`: AI-generated summaries

### New Entity Mentions
- Creates records in `entity_mentions` table
- Links to `entities` table for extracted entities
- Includes confidence scores and context

## ⚙️ Configuration

### Service Configuration
```python
config = {
    'parallel_processing': True,
    'max_workers': 4,
    'save_to_database': True,
    'timeout': 300
}

service = EnrichmentService(config=config)
```

### Processor Configuration
```python
sentiment_config = {
    'temperature': 0.1,
    'confidence_threshold': 0.6,
    'max_tokens': 512
}

sentiment_analyzer = SentimentAnalyzer(config=sentiment_config)
```

### Ollama Configuration
```python
from ai_enrichment.core.ollama_client import OllamaConfig

ollama_config = OllamaConfig(
    base_url="http://localhost:11434",
    model="qwen2.5:7b",
    timeout=120,
    temperature=0.1
)
```

## 🎯 Supported Categories

The system classifies content into the following categories:
- **Politics** (سياسة / Politique)
- **Economy** (اقتصاد / Économie)
- **Society** (مجتمع / Société)
- **Culture** (ثقافة / Culture)
- **Sports** (رياضة / Sport)
- **Education** (تعليم / Éducation)
- **Health** (صحة / Santé)
- **Technology** (تكنولوجيا / Technologie)
- **Environment** (بيئة / Environnement)
- **Security** (أمن / Sécurité)
- **International** (دولي / International)
- **Regional** (جهوي / Régional)

## 🔍 Monitoring and Statistics

### Service Status
```bash
python ai_enrich.py status
```

### Processing Statistics
```bash
python ai_enrich.py stats --type articles --days 30
```

### Performance Monitoring
```python
# Get service status
status = service.get_service_status()
print(f"Ollama available: {status['ollama_available']}")

# Test processors
test_results = service.test_processors("test content")
for processor, result in test_results.items():
    print(f"{processor}: {result['status']}")
```

## 🚨 Error Handling

The system includes comprehensive error handling:
- **Graceful Degradation**: Continues processing even if some components fail
- **Retry Logic**: Automatic retries for failed operations
- **Logging**: Detailed logging for debugging and monitoring
- **Fallback Options**: Skip enrichment if AI processing fails

## 🔧 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if not running
   ollama serve
   ```

2. **Model Not Found**
   ```bash
   # Pull the required model
   ollama pull qwen2.5:7b
   
   # List available models
   ollama list
   ```

3. **Database Connection Issues**
   - Check your `.env` file for correct Supabase credentials
   - Verify database connectivity with existing tools

4. **Low Processing Performance**
   - Adjust `max_workers` in configuration
   - Increase `batch_size` for batch processing
   - Consider using a more powerful machine for Ollama

### Debug Mode
```bash
# Enable verbose logging
python ai_enrich.py test --verbose

# Check individual processor logs
python ai_enrich.py test --processor sentiment --verbose
```

## 📈 Performance Considerations

- **Parallel Processing**: Enabled by default for better throughput
- **Batch Sizes**: Configurable batch sizes for optimal memory usage
- **Model Optimization**: Uses qwen2.5:7b for balance of accuracy and speed
- **Database Efficiency**: Bulk operations and connection pooling
- **Caching**: Results cached to avoid reprocessing

## 🤝 Contributing

To extend the AI enrichment module:

1. **Add New Processors**: Inherit from `BaseProcessor`
2. **Extend Prompts**: Add templates in `prompt_templates.py`
3. **Add Languages**: Extend language support in processors
4. **Custom Categories**: Modify category definitions in `CategoryClassifier`

## 📝 License

This module is part of the Tunisia Intelligence system and follows the same licensing terms.

---

**🎯 Ready to enrich your content with AI!** Start with `python ai_enrich.py test` to verify everything is working correctly.
