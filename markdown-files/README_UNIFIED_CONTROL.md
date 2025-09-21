# Tunisia Intelligence Unified Control System

A comprehensive unified control system that manages all processing pipelines in the Tunisia Intelligence system with centralized configuration, monitoring, and orchestration.

## 🎛️ Overview

The Unified Control System provides:

- **Centralized Configuration**: Single configuration file for all pipeline parameters
- **Pipeline Orchestration**: Coordinated execution of RSS, Facebook, AI enrichment, and vectorization pipelines
- **Rate Limiting**: Intelligent rate limiting across all modules to respect API limits
- **Resource Management**: Memory and CPU monitoring with automatic throttling
- **Comprehensive Monitoring**: Real-time metrics, alerts, and health checks
- **CLI Interface**: Command-line tools for management and monitoring
- **Scheduling**: Automated scheduling with dependency management

## 🏗️ Architecture

```
Tunisia Intelligence Unified Control System
├── Configuration Layer
│   ├── config/unified_control.py      # Centralized configuration
│   └── .env                          # Environment variables
├── Control Layer
│   ├── unified_pipeline_controller.py # Main orchestration engine
│   └── unified_control_cli.py         # Command-line interface
├── Monitoring Layer
│   └── monitoring/unified_monitoring.py # Metrics and alerting
└── Pipeline Modules
    ├── RSS Extraction & Loading
    ├── Facebook Extraction & Loading
    ├── AI Enrichment Processing
    └── Vectorization Processing
```

## 🚀 Quick Start

### 1. Setup Configuration

Copy the example configuration file:
```bash
cp .env.unified_control_example .env
```

Edit `.env` with your specific settings:
- Database credentials (Supabase)
- Facebook API tokens
- Ollama server URL
- Processing limits and rate limits

### 2. Start the Unified Controller

**Option A: Start all pipelines automatically**
```bash
python unified_control_cli.py start
```

**Option B: Interactive mode**
```bash
python unified_control_cli.py interactive
```

**Option C: Background mode**
```bash
python unified_control_cli.py start --background
```

### 3. Monitor Status

```bash
# Show current status
python unified_control_cli.py status

# Show metrics
python unified_control_cli.py metrics

# Follow logs
python unified_control_cli.py logs --follow
```

## 🎯 Pipeline Control

### Individual Pipeline Execution

Run specific pipelines manually:

```bash
# RSS extraction only
python unified_control_cli.py run rss

# Facebook extraction only
python unified_control_cli.py run facebook

# AI enrichment only
python unified_control_cli.py run ai_enrichment

# Vectorization only
python unified_control_cli.py run vectorization
```

### Pipeline Modes

Each pipeline can operate in different modes:

- **`disabled`**: Pipeline is turned off
- **`manual`**: Run only when explicitly triggered
- **`scheduled`**: Run on predefined schedule
- **`continuous`**: Run continuously with minimal delays
- **`batch`**: Process in large batches periodically

Set modes via environment variables:
```bash
RSS_MODE=scheduled
FACEBOOK_MODE=scheduled
AI_ENRICHMENT_MODE=batch
VECTORIZATION_MODE=batch
```

## ⚙️ Configuration Management

### View Configuration

```bash
# Show all configuration
python unified_control_cli.py config show

# Show specific section
python unified_control_cli.py config show rss
python unified_control_cli.py config show ai_enrichment
```

### Update Configuration

```bash
# Set individual parameters
python unified_control_cli.py config set rss.batch_size 25
python unified_control_cli.py config set ai_enrichment.model_name qwen2.5:14b
python unified_control_cli.py config set facebook.api_calls_per_hour 150

# Reload configuration
python unified_control_cli.py config reload
```

## 📊 Monitoring & Alerting

### Real-time Monitoring

The system provides comprehensive monitoring:

- **System Resources**: CPU, memory, disk usage
- **Pipeline Metrics**: Processing rates, error rates, success rates
- **Database Performance**: Query times, connection counts
- **API Usage**: Rate limit tracking, quota monitoring

### Health Checks

Automated health checks monitor:

- System resource thresholds
- Pipeline error rates
- Database connectivity
- API availability
- Processing delays

### Alerts

Automatic alerts for:

- **Critical**: System failures, resource exhaustion
- **Error**: Pipeline failures, database errors
- **Warning**: High resource usage, elevated error rates
- **Info**: Normal operational events

## 🔧 Pipeline-Specific Configuration

### RSS Pipeline

Key parameters:
```bash
RSS_REQUESTS_PER_MINUTE=30        # Rate limiting
RSS_BATCH_SIZE=50                 # Articles per batch
RSS_MAX_SOURCES_PER_RUN=10        # Sources per execution
RSS_DELAY_BETWEEN_SOURCES=2.0     # Delay between sources
RSS_SCHEDULE_INTERVAL=60          # Minutes between runs
```

### Facebook Pipeline

Key parameters:
```bash
FACEBOOK_API_CALLS_PER_HOUR=200   # API rate limiting
FACEBOOK_PAGES_PER_BATCH=10       # Pages per batch
FACEBOOK_MAX_POSTS_PER_PAGE=50    # Posts per page
FACEBOOK_DELAY_BETWEEN_PAGES=5.0  # Delay between pages
FACEBOOK_SCHEDULE_INTERVAL=120    # Minutes between runs
```

### AI Enrichment Pipeline

Key parameters:
```bash
AI_BATCH_SIZE=10                  # Items per batch
AI_MAX_CONCURRENT=3               # Concurrent requests
AI_REQUESTS_PER_MINUTE=20         # Rate limiting
AI_MODEL_NAME=qwen2.5:7b          # Ollama model
AI_ENABLE_SENTIMENT=true          # Feature toggles
AI_ENABLE_KEYWORDS=true
AI_ENABLE_NER=true
```

### Vectorization Pipeline

Key parameters:
```bash
VECTOR_BATCH_SIZE=32              # Vectors per batch
VECTOR_MAX_ITEMS_PER_RUN=1000     # Items per execution
VECTOR_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
VECTOR_FRENCH_ONLY=true           # Process French text only
```

## 📈 Performance Optimization

### Rate Limiting Strategy

The system implements intelligent rate limiting:

- **RSS**: 30 requests/minute, 1000 requests/hour
- **Facebook**: 200 API calls/hour, 2000 calls/day
- **AI Enrichment**: 20 requests/minute to Ollama
- **Vectorization**: Batch processing for optimal throughput

### Resource Management

Automatic resource management:

- **Memory Monitoring**: Alert at 80%, critical at 90%
- **CPU Throttling**: Reduce batch sizes under high load
- **Disk Space**: Monitor and alert on low space
- **Connection Pooling**: Efficient database connections

### Processing Optimization

- **Sequential Processing**: Ensures data dependencies
- **Batch Processing**: Optimizes throughput for AI and vectorization
- **Parallel Workers**: Configurable worker threads per pipeline
- **Caching**: Vector caching and content deduplication

## 🔄 Scheduling & Coordination

### Pipeline Dependencies

Default execution order:
1. **RSS Extraction** → Collect news articles
2. **Facebook Extraction** → Collect social media content
3. **AI Enrichment** → Process all content
4. **Vectorization** → Generate embeddings

### Scheduling Options

```bash
# Full cycle every 4 hours
SCHEDULING_FULL_CYCLE_INTERVAL=4

# Priority content every hour
SCHEDULING_PRIORITY_CYCLE_INTERVAL=1

# Delay between pipelines (minutes)
SCHEDULING_PIPELINE_DELAY=5
```

### Coordination Modes

- **Sequential**: Run pipelines one after another (recommended)
- **Parallel**: Run compatible pipelines simultaneously (future)

## 🚨 Troubleshooting

### Common Issues

**Controller won't start:**
```bash
# Check configuration
python unified_control_cli.py config show

# Check logs
python unified_control_cli.py logs

# Verify database connection
python -c "from config.database import DatabaseManager; db = DatabaseManager(); print('DB OK')"
```

**High error rates:**
```bash
# Check pipeline status
python unified_control_cli.py status

# View recent errors
python unified_control_cli.py logs --lines 100

# Reduce batch sizes
python unified_control_cli.py config set rss.batch_size 10
python unified_control_cli.py config set ai_enrichment.batch_size 5
```

**Resource exhaustion:**
```bash
# Check system metrics
python unified_control_cli.py metrics

# Reduce concurrent workers
python unified_control_cli.py config set rss.max_workers 2
python unified_control_cli.py config set ai_enrichment.max_concurrent 1
```

### Debug Mode

Enable debug mode for detailed logging:
```bash
DEBUG=true python unified_control_cli.py start
```

### Log Files

Logs are stored in:
- `logs/unified_controller.log` - Main controller log
- `logs/controller_YYYYMMDD.log` - Daily logs
- `monitoring/metrics.db` - Metrics database

## 📋 Interactive Commands

In interactive mode, available commands:

```
status    - Show system status
start     - Start controller
stop      - Stop controller
pause     - Pause controller
resume    - Resume controller
config    - Show configuration
metrics   - Show metrics
logs      - Show recent logs
run <pipeline> - Run single pipeline
help      - Show help
exit      - Exit interactive mode
```

## 🔐 Security Considerations

- Store sensitive credentials in `.env` file
- Use environment variables for production
- Implement proper access controls for CLI
- Monitor API usage to prevent quota exhaustion
- Regular security updates for dependencies

## 📊 Performance Benchmarks

Based on current system performance:

- **RSS Processing**: ~2-3 articles/second
- **Facebook Processing**: ~1-2 API calls per page
- **AI Enrichment**: ~28 seconds per item (full analysis)
- **Vectorization**: ~66 articles/second (sentence-transformers)

## 🔮 Future Enhancements

- Web-based dashboard interface
- Advanced scheduling with cron-like syntax
- Multi-node distributed processing
- Advanced analytics and reporting
- Integration with external monitoring systems
- Automated scaling based on load

## 📞 Support

For issues or questions:

1. Check the logs: `python unified_control_cli.py logs`
2. Review configuration: `python unified_control_cli.py config show`
3. Check system status: `python unified_control_cli.py status`
4. Review this documentation
5. Check individual pipeline documentation

---

**Tunisia Intelligence Unified Control System** - Centralized control for comprehensive news intelligence processing.
