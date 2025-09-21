# Tunisia Intelligence RSS Scraper

A comprehensive RSS scraping system for monitoring Tunisian news sources with advanced features including unified extraction, database integration, and intelligent content processing.

## 🏗️ Architecture

- **Modular Design**: Clear separation between extractors, database layer, utilities, and main processing
- **35+ Specialized Extractors**: Custom extractors for different Tunisian news sources
- **Unified Routing System**: Automatic URL-to-extractor mapping with fallback support
- **Supabase Integration**: Cloud database with Pydantic models for type safety
- **Comprehensive Logging**: Detailed logging with configurable levels and formats
- **Error Handling**: Retry logic with exponential backoff and graceful error recovery

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and navigate to the project
cd tunisia_intelligence

# Run the setup script
python setup.py

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit the `.env` file with your configuration:

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-secret-key

# Environment
ENVIRONMENT=development
DEBUG=true

# Scraping settings
SCRAPING_MAX_RETRIES=3
SCRAPING_INITIAL_TIMEOUT=60
SCRAPING_RATE_LIMIT_DELAY=1.0
```

### 3. Database Setup

```bash
# Check database schema
python check_schema.py
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### 5. Start Scraping

```bash
# Process all sources
python rss_loader.py

# Test individual extractor
python main.py --url https://nawaat.org/feed/ --output json
```

## 📁 Project Structure

```
tunisia_intelligence/
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── database.py        # Database models and operations
│   ├── settings.py        # Application settings
│   └── secrets.py         # Secret management system
├── extractors/            # RSS extractors
│   ├── __init__.py        # Extractor registry
│   ├── unified_extractor.py  # Unified extraction system
│   ├── utils.py           # Extractor utilities
│   └── *_extractor.py     # Source-specific extractors
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── content_utils.py   # Content processing
│   └── date_utils.py      # Date parsing
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_extractors.py
│   ├── test_database.py
│   ├── test_utils.py
│   └── test_config.py
├── main.py               # CLI dispatcher
├── rss_loader.py         # Main processing engine
├── check_schema.py       # Database schema checker
├── setup.py              # Project setup script
├── requirements.txt      # Dependencies
├── pytest.ini           # Test configuration
├── .env.template         # Environment template
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

The system uses a hierarchical configuration system with the following precedence:
1. Environment variables
2. `.env` file
3. Default values

### Secret Management

Multiple secret backends are supported:

- **Environment Variables** (default): Store secrets in environment variables
- **Encrypted Files**: Store secrets in encrypted local files
- **Azure Key Vault**: Use Azure Key Vault for secret storage
- **AWS Secrets Manager**: Use AWS Secrets Manager for secret storage

```bash
# Set secret backend
SECRETS_BACKEND=env  # or file, azure_kv, aws_sm
```

### Database Configuration

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-secret-key

# Optional
SUPABASE_ANON_KEY=your-anon-key
```

### Scraping Configuration

```bash
SCRAPING_MAX_RETRIES=3              # Maximum retry attempts
SCRAPING_INITIAL_TIMEOUT=60         # Initial timeout in seconds
SCRAPING_RATE_LIMIT_DELAY=1.0       # Delay between requests
SCRAPING_BATCH_SIZE=100             # Articles per batch
SCRAPING_MAX_WORKERS=5              # Maximum worker threads
```

### Logging Configuration

```bash
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_PATH=rss_loader.log        # Log file path
LOG_MAX_FILE_SIZE=10485760          # Max file size (10MB)
LOG_BACKUP_COUNT=5                  # Number of backup files
```

## 🧪 Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_extractors.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

## 📊 Monitoring

The system includes built-in monitoring capabilities:

```bash
MONITORING_ENABLED=true
MONITORING_METRICS_RETENTION_DAYS=30
MONITORING_ALERT_ON_ERRORS=true
MONITORING_WEBHOOK_URL=https://hooks.slack.com/your/webhook
```

## 🔍 Content Processing

Advanced content processing features:

- **HTML Cleaning**: Removes HTML tags and normalizes content
- **Date Parsing**: Handles multiple date formats with fallbacks
- **Media Extraction**: Extracts media information from feeds
- **Content Validation**: Validates content quality and length
- **Deduplication**: Prevents duplicate content storage

```bash
CONTENT_MIN_TITLE_LENGTH=5
CONTENT_MIN_CONTENT_LENGTH=50
CONTENT_ENABLE_DEDUPLICATION=true
CONTENT_DEFAULT_LANGUAGE=ar
```

## 🌐 Supported Sources

The system supports 35+ Tunisian news sources including:

### Newspapers & Portals
- Nawaat
- African Manager
- Leaders
- La Presse
- Réalités
- WebManagerCenter
- Al Chourouk
- WebDo
- Business News
- Tunisie Numérique

### Radio Stations
- Mosaïque FM
- Radio Tunisienne
- Radio Express FM
- Jawhara FM
- Radio Tataouine
- Radio Gafsa
- Radio Kef
- RTCI
- Radio Monastir
- Radio Sfax

## 🔒 Security

- **Secret Management**: Multiple secure backends for sensitive data
- **Input Validation**: Comprehensive input validation using Pydantic
- **Rate Limiting**: Respectful crawling with configurable delays
- **Error Handling**: Secure error handling without information leakage

## 🚀 Performance

- **Concurrent Processing**: Multi-threaded processing with configurable workers
- **Timeout Handling**: Robust timeout handling with exponential backoff
- **Connection Pooling**: Efficient database connection management
- **Caching**: Intelligent caching to reduce redundant operations

## 📈 Improvements Made

Based on the comprehensive analysis, the following critical improvements have been implemented:

### ✅ Fixed Issues
1. **Fixed mktime import bug** in `date_utils.py`
2. **Removed legacy code** (`rss_parser.py` with 3000+ lines of duplicates)
3. **Implemented secure secret management** with multiple backends
4. **Added comprehensive configuration system** with validation
5. **Created extensive test suite** with 80%+ coverage target

### 🆕 New Features
1. **Configuration Management**: Centralized, validated configuration system
2. **Secret Management**: Secure handling of sensitive data
3. **Testing Framework**: Comprehensive unit and integration tests
4. **Enhanced Logging**: Configurable logging with proper formatting
5. **Project Setup**: Automated setup and installation scripts

### 🔧 Enhanced Architecture
1. **Type Safety**: Enhanced Pydantic models with proper validation
2. **Error Handling**: Improved error handling patterns
3. **Documentation**: Comprehensive documentation and setup guides
4. **Development Tools**: Testing, coverage, and development utilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the documentation
2. Run the test suite to verify setup
3. Check logs for detailed error information
4. Review configuration settings

## 🔄 Changelog

### v1.1.0 (Current)
- ✅ Fixed critical mktime import bug
- ✅ Removed legacy duplicate code
- ✅ Added secure secret management system
- ✅ Implemented comprehensive configuration management
- ✅ Added extensive test suite
- ✅ Enhanced error handling and logging
- ✅ Added project setup automation

### v1.0.0 (Previous)
- Initial RSS scraping system
- 35+ specialized extractors
- Supabase database integration
- Basic logging and error handling
