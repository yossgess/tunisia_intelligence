# Tunisia Intelligence Web Dashboard

A comprehensive web-based dashboard and control panel for managing all Tunisia Intelligence processing pipelines with real-time monitoring, interactive controls, and data visualization.

## 🌟 Features

### Real-Time Monitoring
- **Live System Metrics**: CPU, memory, disk usage with real-time updates
- **Pipeline Status**: Current status and performance of all processing pipelines
- **Health Monitoring**: System health checks with automated alerts
- **Resource Tracking**: Memory usage, processing rates, and error monitoring

### Interactive Controls
- **Pipeline Management**: Start, stop, pause, and resume individual pipelines
- **Controller Operations**: Full control over the unified pipeline controller
- **Real-Time Execution**: Execute pipelines manually with live feedback
- **Configuration Management**: View and modify system configuration

### Data Visualization
- **Interactive Charts**: System resources and pipeline performance charts
- **Performance Metrics**: Processing rates, success rates, and error analytics
- **Historical Data**: Trend analysis and performance over time
- **Alert Dashboard**: Active alerts with severity levels and timestamps

### User Interface
- **Modern Design**: Bootstrap 5 with custom styling and animations
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Real-Time Updates**: WebSocket-based live updates without page refresh
- **Intuitive Controls**: Easy-to-use interface with clear visual indicators

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Tunisia Intelligence unified control system
- Database connectivity (Supabase)
- All pipeline dependencies installed

### Installation

1. **Install dashboard dependencies:**
   ```bash
   cd web_dashboard
   pip install -r requirements.txt
   ```

2. **Or use the automatic installer:**
   ```bash
   python start_dashboard.py --install-deps
   ```

### Starting the Dashboard

**Basic startup:**
```bash
python start_dashboard.py
```

**Custom configuration:**
```bash
# Custom port
python start_dashboard.py --port 8080

# Allow external connections
python start_dashboard.py --host 0.0.0.0

# Debug mode
python start_dashboard.py --debug

# Skip system checks
python start_dashboard.py --skip-checks
```

**Direct Flask startup:**
```bash
cd web_dashboard
python app.py
```

### Accessing the Dashboard

Once started, open your web browser and navigate to:
- **Local access**: http://localhost:5000
- **Custom port**: http://localhost:8080 (if using --port 8080)
- **External access**: http://your-ip:5000 (if using --host 0.0.0.0)

## 🎛️ Dashboard Interface

### Main Dashboard
- **System Status Cards**: Overview of system health, active pipelines, alerts, and current cycle
- **Controller Management**: Start, stop, pause, resume controls for the main controller
- **Pipeline Cards**: Individual pipeline status with run buttons and performance metrics
- **Real-Time Charts**: System resources and pipeline performance visualization

### Monitoring Section
- **Active Alerts**: Current system alerts with severity levels and timestamps
- **System Logs**: Real-time log viewer with syntax highlighting
- **Performance Metrics**: Detailed performance statistics and trends

### Interactive Features
- **Real-Time Updates**: Automatic updates every 5-10 seconds via WebSocket
- **Manual Refresh**: Ctrl+R to refresh all data, Ctrl+L to refresh logs
- **Pipeline Execution**: Click "Run" buttons to execute individual pipelines
- **Alert Management**: View and manage system alerts

## 🔧 Architecture

### Backend (Flask + SocketIO)
```
web_dashboard/
├── app.py                 # Main Flask application
├── start_dashboard.py     # Startup script with checks
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Main dashboard template
└── static/
    ├── css/
    │   └── dashboard.css  # Custom styles
    └── js/
        └── dashboard.js   # Dashboard JavaScript
```

### Key Components

1. **Flask Application** (`app.py`)
   - RESTful API endpoints for system control
   - WebSocket integration for real-time updates
   - Integration with unified control system
   - Dashboard data aggregation and formatting

2. **Frontend Interface** (`dashboard.html`)
   - Bootstrap 5 responsive design
   - Real-time WebSocket updates
   - Interactive charts with Plotly.js
   - Modern UI with animations and transitions

3. **JavaScript Controller** (`dashboard.js`)
   - WebSocket connection management
   - Real-time data updates
   - User interaction handling
   - Chart rendering and updates

4. **Startup Script** (`start_dashboard.py`)
   - Dependency checking and installation
   - System requirements validation
   - Configuration options
   - Error handling and logging

## 📡 API Endpoints

### System Status
- `GET /api/status` - Get comprehensive system status
- `GET /api/config` - Get system configuration
- `POST /api/config/update` - Update configuration parameters

### Pipeline Control
- `POST /api/pipeline/{name}/execute` - Execute specific pipeline
- `POST /api/controller/start` - Start the controller
- `POST /api/controller/stop` - Stop the controller
- `POST /api/controller/pause` - Pause the controller
- `POST /api/controller/resume` - Resume the controller

### Monitoring
- `GET /api/logs` - Get recent system logs
- `GET /api/metrics/chart/{type}` - Get chart data for visualization

### WebSocket Events
- `connect` - Client connection established
- `disconnect` - Client disconnection
- `status` - Real-time status updates
- `request_update` - Request immediate status update

## 🎨 Customization

### Styling
Edit `static/css/dashboard.css` to customize:
- Color schemes and themes
- Card layouts and animations
- Chart styling
- Responsive breakpoints

### Functionality
Modify `static/js/dashboard.js` to add:
- Custom charts and visualizations
- Additional real-time features
- Enhanced user interactions
- Custom notifications

### Backend Features
Extend `app.py` to add:
- New API endpoints
- Additional data sources
- Custom monitoring metrics
- Enhanced integrations

## 🔒 Security Considerations

### Network Security
- **Local Access**: Default configuration only allows localhost connections
- **External Access**: Use `--host 0.0.0.0` only in secure networks
- **Firewall**: Configure firewall rules for production deployments
- **HTTPS**: Consider using reverse proxy with SSL for production

### Authentication
- Current version has no built-in authentication
- Consider adding authentication middleware for production use
- Implement role-based access control if needed

### Data Security
- Sensitive configuration data is not exposed in the UI
- API keys and secrets are handled securely
- Log data is filtered to prevent sensitive information exposure

## 🚨 Troubleshooting

### Common Issues

**Dashboard won't start:**
```bash
# Check dependencies
python start_dashboard.py --install-deps

# Check system requirements
python start_dashboard.py --skip-checks

# Force start with issues
python start_dashboard.py --force
```

**Connection issues:**
```bash
# Check if port is available
netstat -an | grep :5000

# Try different port
python start_dashboard.py --port 8080

# Check firewall settings
```

**Real-time updates not working:**
- Check WebSocket connection in browser developer tools
- Verify network connectivity
- Check for proxy/firewall blocking WebSocket connections

**Charts not displaying:**
- Ensure internet connection for CDN resources
- Check browser console for JavaScript errors
- Verify Plotly.js is loading correctly

### Debug Mode
Enable debug mode for detailed error information:
```bash
python start_dashboard.py --debug
```

### Log Files
Check log files for detailed error information:
- `logs/unified_controller.log` - Main controller logs
- `monitoring/metrics.db` - Metrics database
- Browser developer console - Frontend errors

## 🔄 Integration

### Unified Control System
The dashboard integrates seamlessly with the Tunisia Intelligence unified control system:
- Uses existing configuration system
- Leverages monitoring infrastructure
- Integrates with pipeline controllers
- Shares database connections

### Pipeline Compatibility
Compatible with all Tunisia Intelligence pipelines:
- **RSS Pipeline**: 35+ Tunisian news extractors
- **Facebook Pipeline**: 54 government pages
- **AI Enrichment**: qwen2.5:7b model integration
- **Vectorization**: sentence-transformers processing

## 📊 Performance

### Resource Usage
- **Memory**: ~50-100MB for dashboard application
- **CPU**: Minimal impact, mostly I/O bound
- **Network**: WebSocket connections for real-time updates
- **Storage**: Minimal, uses existing monitoring database

### Scalability
- Supports multiple concurrent users
- Real-time updates scale with WebSocket connections
- Chart rendering handled client-side
- Database queries optimized for dashboard use

## 🔮 Future Enhancements

### Planned Features
- **User Authentication**: Role-based access control
- **Custom Dashboards**: User-configurable dashboard layouts
- **Advanced Analytics**: Deeper insights and trend analysis
- **Mobile App**: Native mobile application
- **API Documentation**: Interactive API documentation
- **Export Features**: Data export and reporting capabilities

### Integration Opportunities
- **External Monitoring**: Integration with Grafana, Prometheus
- **Alerting Systems**: Slack, email, SMS notifications
- **Cloud Deployment**: Docker containers and cloud platforms
- **Database Analytics**: Advanced database performance monitoring

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify system requirements and dependencies
4. Check the main unified control system documentation

### Development
- Built with Flask, SocketIO, Bootstrap 5, and Plotly.js
- Follows Tunisia Intelligence system architecture
- Integrates with existing monitoring and control systems
- Designed for extensibility and customization

---

**Tunisia Intelligence Web Dashboard** - Real-time monitoring and control for comprehensive news intelligence processing.
