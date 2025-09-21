#!/usr/bin/env python3
"""
Tunisia Intelligence Web Dashboard

A comprehensive web-based dashboard and control panel for managing all
Tunisia Intelligence processing pipelines.

Features:
- Real-time pipeline monitoring and control
- System metrics and performance visualization
- Configuration management interface
- Log viewer and alert management
"""

import sys
import os
import json
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Flask and web dependencies
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import json
import time
from datetime import datetime
import threading
import psutil
import os
import sys

# Plotly for chart generation
try:
    import plotly.graph_objects as go
    import plotly.utils
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available - charts will be disabled")

# Import AI configuration manager
try:
    from ai_config_manager import ai_config_bp, AIConfigManager
    AI_CONFIG_AVAILABLE = True
except ImportError:
    try:
        from .ai_config_manager import ai_config_bp, AIConfigManager
        AI_CONFIG_AVAILABLE = True
    except ImportError:
        AI_CONFIG_AVAILABLE = False
        logging.warning("AI configuration manager not available")

# Import Tunisia Intelligence components
from config.unified_control import get_unified_control, reload_unified_control
from unified_pipeline_controller import UnifiedPipelineController
from monitoring.unified_monitoring import get_unified_monitor
from unified_control_cli import UnifiedControlCLI
from config.facebook_config import (
    get_facebook_config, 
    update_facebook_config, 
    set_performance_mode,
    FacebookPipelineConfig,
    DEFAULT_FACEBOOK_CONFIG
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'tunisia_intelligence_dashboard_2024'
app.json_encoder = DateTimeEncoder
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register AI configuration blueprint if available
if AI_CONFIG_AVAILABLE:
    app.register_blueprint(ai_config_bp)
    logger.info("AI configuration blueprint registered")
else:
    logger.warning("AI configuration blueprint not available")

# Global instances
controller_instance = None
monitor_instance = None
cli_instance = None
background_thread = None
thread_lock = threading.Lock()


class DashboardManager:
    """Manages dashboard state and operations."""
    
    def __init__(self):
        self.controller = None
        self.monitor = None
        self.cli = UnifiedControlCLI()
        self.ai_config_manager = AIConfigManager() if AI_CONFIG_AVAILABLE else None
        self.last_update = datetime.now()
        self.update_interval = 5  # seconds
        
    def initialize(self):
        """Initialize dashboard components."""
        try:
            self.controller = UnifiedPipelineController()
            self.monitor = get_unified_monitor()
            self.monitor.start_monitoring()
            logger.info("Dashboard manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize dashboard manager: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            control_settings = get_unified_control()
            
            # Basic system info
            status = {
                'timestamp': datetime.now().isoformat(),
                'master_enabled': control_settings.master_enabled,
                'maintenance_mode': control_settings.maintenance_mode,
                'environment': control_settings.environment,
                'debug': control_settings.debug
            }
            
            # Pipeline status
            pipelines = ['rss', 'facebook', 'ai_enrichment', 'vectorization']
            pipeline_status = {}
            
            for pipeline_name in pipelines:
                enabled = control_settings.is_pipeline_enabled(pipeline_name)
                mode = control_settings.get_pipeline_mode(pipeline_name)
                
                pipeline_status[pipeline_name] = {
                    'enabled': enabled,
                    'mode': mode.value,
                    'display_name': pipeline_name.replace('_', ' ').title()
                }
            
            status['pipelines'] = pipeline_status
            
            # Controller status
            if self.controller:
                controller_status = self.controller.get_status()
                status['controller'] = controller_status
            
            # System metrics
            if self.monitor:
                dashboard_data = self.monitor.get_dashboard_data()
                status['system_metrics'] = dashboard_data.get('system_metrics', {})
                status['system_health'] = dashboard_data.get('system_health', {})
                status['active_alerts'] = dashboard_data.get('active_alerts', [])
                status['pipeline_summaries'] = dashboard_data.get('pipeline_summaries', {})
            
            # AI Configuration status
            if self.ai_config_manager:
                try:
                    status['ai_configuration'] = self.ai_config_manager.get_dashboard_data()
                except Exception as e:
                    logger.error(f"Error getting AI configuration data: {e}")
                    status['ai_configuration'] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'master_enabled': False,
                'pipelines': {}
            }
    
    def execute_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """Execute a specific pipeline."""
        try:
            if not self.controller:
                return {'success': False, 'message': 'Controller not initialized'}
            
            metrics = self.controller.execute_single_pipeline(pipeline_name)
            
            return {
                'success': True,
                'message': f'{pipeline_name} pipeline executed successfully',
                'metrics': {
                    'status': metrics.status.value,
                    'items_processed': metrics.items_processed,
                    'items_failed': metrics.items_failed,
                    'duration_seconds': metrics.duration_seconds,
                    'success_rate': metrics.success_rate
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing pipeline {pipeline_name}: {e}")
            return {'success': False, 'message': str(e)}
    
    def update_configuration(self, section: str, parameter: str, value: str) -> Dict[str, Any]:
        """Update configuration parameter."""
        try:
            # Set environment variable
            env_var_name = f"{section.upper()}_{parameter.upper()}"
            os.environ[env_var_name] = str(value)
            
            # Reload configuration
            reload_unified_control()
            
            return {
                'success': True,
                'message': f'Updated {section}.{parameter} = {value}'
            }
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return {'success': False, 'message': str(e)}


# Global dashboard manager
dashboard_manager = DashboardManager()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """API endpoint for system status."""
    return jsonify(dashboard_manager.get_system_status())


@app.route('/api/pipeline/<pipeline_name>/execute', methods=['POST'])
def api_execute_pipeline(pipeline_name):
    """API endpoint to execute a pipeline."""
    result = dashboard_manager.execute_pipeline(pipeline_name)
    return jsonify(result)


@app.route('/api/controller/start', methods=['POST'])
def api_start_controller():
    """API endpoint to start the controller."""
    try:
        if dashboard_manager.controller and not dashboard_manager.controller.running:
            # Start controller in background thread
            def start_controller():
                dashboard_manager.controller.start()
            
            controller_thread = threading.Thread(target=start_controller, daemon=True)
            controller_thread.start()
            
            return jsonify({'success': True, 'message': 'Controller started'})
        else:
            return jsonify({'success': False, 'message': 'Controller already running or not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/controller/stop', methods=['POST'])
def api_stop_controller():
    """API endpoint to stop the controller."""
    try:
        if dashboard_manager.controller and dashboard_manager.controller.running:
            dashboard_manager.controller.stop()
            return jsonify({'success': True, 'message': 'Controller stopped'})
        else:
            return jsonify({'success': False, 'message': 'Controller not running'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/controller/pause', methods=['POST'])
def api_pause_controller():
    """API endpoint to pause the controller."""
    try:
        if dashboard_manager.controller:
            dashboard_manager.controller.pause()
            return jsonify({'success': True, 'message': 'Controller paused'})
        else:
            return jsonify({'success': False, 'message': 'Controller not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/controller/resume', methods=['POST'])
def api_resume_controller():
    """API endpoint to resume the controller."""
    try:
        if dashboard_manager.controller:
            dashboard_manager.controller.resume()
            return jsonify({'success': True, 'message': 'Controller resumed'})
        else:
            return jsonify({'success': False, 'message': 'Controller not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config')
def api_get_config():
    """API endpoint to get configuration."""
    try:
        control_settings = get_unified_control()
        config_dict = control_settings.to_dict()
        return jsonify(config_dict)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/config/update', methods=['POST'])
def api_update_config():
    """API endpoint to update configuration."""
    try:
        data = request.get_json()
        section = data.get('section')
        parameter = data.get('parameter')
        value = data.get('value')
        
        if not all([section, parameter, value is not None]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        result = dashboard_manager.update_configuration(section, parameter, value)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs')
def api_get_logs():
    """API endpoint to get recent logs."""
    try:
        log_file = Path("logs/unified_controller.log")
        
        if not log_file.exists():
            return jsonify({'logs': [], 'message': 'Log file not found'})
        
        # Get last 100 lines
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines
        
        logs = []
        for line in recent_lines:
            line = line.strip()
            if line:
                logs.append(line)
        
        return jsonify({'logs': logs})
        
    except Exception as e:
        return jsonify({'logs': [], 'error': str(e)})


@app.route('/api/metrics/chart/<chart_type>')
def api_get_chart_data(chart_type):
    """API endpoint to get chart data."""
    try:
        if not PLOTLY_AVAILABLE:
            return jsonify({'error': 'Plotly not available - charts disabled'})
            
        if not dashboard_manager.monitor:
            return jsonify({'error': 'Monitor not initialized'})
        
        dashboard_data = dashboard_manager.get_system_status()
        
        if chart_type == 'system_resources':
            # System resources chart
            system_metrics = dashboard_data.get('system_metrics', {})
            current_metrics = system_metrics.get('current', {})
            
            if current_metrics:
                fig = go.Figure()
                
                # CPU Usage
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=current_metrics.get('cpu_percent', 0),
                    domain={'x': [0, 0.5], 'y': [0.5, 1]},
                    title={'text': "CPU %"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': "darkblue"},
                           'steps': [{'range': [0, 50], 'color': "lightgray"},
                                   {'range': [50, 80], 'color': "yellow"},
                                   {'range': [80, 100], 'color': "red"}]}
                ))
                
                # Memory Usage
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=current_metrics.get('memory_percent', 0),
                    domain={'x': [0.5, 1], 'y': [0.5, 1]},
                    title={'text': "Memory %"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': "darkgreen"},
                           'steps': [{'range': [0, 50], 'color': "lightgray"},
                                   {'range': [50, 80], 'color': "yellow"},
                                   {'range': [80, 100], 'color': "red"}]}
                ))
                
                fig.update_layout(height=400, title="System Resources")
                return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        elif chart_type == 'pipeline_performance':
            # Pipeline performance chart
            pipeline_summaries = dashboard_data.get('pipeline_summaries', {})
            
            pipelines = list(pipeline_summaries.keys())
            processed = [pipeline_summaries[p].get('total_processed', 0) for p in pipelines]
            failed = [pipeline_summaries[p].get('total_failed', 0) for p in pipelines]
            
            fig = go.Figure(data=[
                go.Bar(name='Processed', x=pipelines, y=processed, marker_color='green'),
                go.Bar(name='Failed', x=pipelines, y=failed, marker_color='red')
            ])
            
            fig.update_layout(
                barmode='group',
                title='Pipeline Performance (24h)',
                xaxis_title='Pipeline',
                yaxis_title='Items',
                height=400
            )
            
            return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        return jsonify({'error': 'Unknown chart type'})
        
    except Exception as e:
        logger.error(f"Error generating chart {chart_type}: {e}")
        return jsonify({'error': str(e)})


# Facebook Configuration API Endpoints

@app.route('/api/facebook/config')
def api_get_facebook_config():
    """API endpoint to get Facebook configuration."""
    try:
        config = get_facebook_config()
        config_dict = config.to_dict()
        return jsonify(config_dict)
    except Exception as e:
        logger.error(f"Error getting Facebook configuration: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/facebook/config/update', methods=['POST'])
def api_update_facebook_config():
    """API endpoint to update Facebook configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # Update configuration with provided values
        extraction_updates = {}
        loader_updates = {}
        
        # Map form fields to configuration sections with validation
        extraction_fields = {
            'hours_back': {'type': int, 'min': 1, 'max': 720},  # 1 hour to 30 days
            'min_api_delay': {'type': float, 'min': 0.1, 'max': 5.0},
            'page_cache_duration': {'type': int, 'min': 300, 'max': 86400},  # 5 min to 24 hours
            'max_api_calls_per_run': {'type': int, 'min': 10, 'max': 1000},
            'api_timeout': {'type': int, 'min': 5, 'max': 120},
            'max_pages_per_run': {'type': int, 'min': 1, 'max': 100},
            'posts_limit_per_page': {'type': int, 'min': 5, 'max': 100},
            'api_version': {'type': str, 'allowed': ['v18.0', 'v19.0', 'v20.0']},
            'default_page_priority': {'type': float, 'min': 1.0, 'max': 10.0},
            'priority_increase_for_activity': {'type': float, 'min': 0.1, 'max': 2.0}
        }
        
        loader_fields = {
            'use_batch_inserts': {'type': bool},
            'check_duplicates': {'type': bool},
            'enable_state_tracking': {'type': bool}
        }
        
        # Validate and process extraction fields
        for field, validation in extraction_fields.items():
            if field in data:
                value = data[field]
                
                # Type validation and conversion
                try:
                    if validation['type'] == int:
                        value = int(value)
                    elif validation['type'] == float:
                        value = float(value)
                    elif validation['type'] == bool:
                        value = bool(value) if isinstance(value, bool) else str(value).lower() in ['true', '1', 'yes']
                    elif validation['type'] == str:
                        value = str(value)
                    
                    # Range validation
                    if 'min' in validation and value < validation['min']:
                        return jsonify({'success': False, 'message': f'{field} must be at least {validation["min"]}'})
                    if 'max' in validation and value > validation['max']:
                        return jsonify({'success': False, 'message': f'{field} must be at most {validation["max"]}'})
                    if 'allowed' in validation and value not in validation['allowed']:
                        return jsonify({'success': False, 'message': f'{field} must be one of: {validation["allowed"]}'})
                    
                    extraction_updates[field] = value
                    
                except (ValueError, TypeError) as e:
                    return jsonify({'success': False, 'message': f'Invalid value for {field}: {str(e)}'})
        
        # Validate and process loader fields
        for field, validation in loader_fields.items():
            if field in data:
                value = data[field]
                
                try:
                    if validation['type'] == bool:
                        value = bool(value) if isinstance(value, bool) else str(value).lower() in ['true', '1', 'yes']
                    
                    loader_updates[field] = value
                    
                except (ValueError, TypeError) as e:
                    return jsonify({'success': False, 'message': f'Invalid value for {field}: {str(e)}'})
        
        # Apply updates
        update_params = {}
        if extraction_updates:
            update_params['extraction'] = extraction_updates
        if loader_updates:
            update_params['loader'] = loader_updates
        
        if update_params:
            update_facebook_config(**update_params)
            
            # Automatically trigger configuration reload in running processes
            try:
                reload_signal_file = Path("facebook_config_reload.signal")
                with open(reload_signal_file, 'w') as f:
                    f.write(str(datetime.now()))
                logger.info("Configuration reload signal sent to Facebook processes")
            except Exception as e:
                logger.warning(f"Could not send reload signal: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Facebook configuration updated and reload signal sent',
            'updated_fields': list(data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error updating Facebook configuration: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/performance-mode', methods=['POST'])
def api_set_facebook_performance_mode():
    """API endpoint to set Facebook performance mode."""
    try:
        data = request.get_json()
        mode = data.get('mode')
        
        if mode not in ['conservative', 'balanced', 'aggressive']:
            return jsonify({'success': False, 'message': 'Invalid performance mode'})
        
        set_performance_mode(mode)
        
        return jsonify({
            'success': True,
            'message': f'Performance mode set to {mode}',
            'mode': mode
        })
        
    except Exception as e:
        logger.error(f"Error setting Facebook performance mode: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/reset', methods=['POST'])
def api_reset_facebook_config():
    """API endpoint to reset Facebook configuration to defaults."""
    try:
        # Reset to default configuration
        global FACEBOOK_CONFIG
        from config.facebook_config import DEFAULT_FACEBOOK_CONFIG
        FACEBOOK_CONFIG = FacebookPipelineConfig()
        
        return jsonify({
            'success': True,
            'message': 'Facebook configuration reset to defaults'
        })
        
    except Exception as e:
        logger.error(f"Error resetting Facebook configuration: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/reload', methods=['POST'])
def api_reload_facebook_config():
    """API endpoint to reload Facebook configuration in running processes."""
    try:
        # Signal running Facebook processes to reload configuration
        # This could be done through a shared file, database flag, or process communication
        
        # For now, we'll create a reload signal file
        reload_signal_file = Path("facebook_config_reload.signal")
        with open(reload_signal_file, 'w') as f:
            f.write(str(datetime.now()))
        
        return jsonify({
            'success': True,
            'message': 'Configuration reload signal sent to Facebook processes'
        })
        
    except Exception as e:
        logger.error(f"Error sending reload signal: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/backup', methods=['POST'])
def api_backup_facebook_config():
    """API endpoint to backup current Facebook configuration."""
    try:
        config = get_facebook_config()
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'config': config.to_dict()
        }
        
        # Save backup to file
        backup_dir = Path("config_backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_filename = f"facebook_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = backup_dir / backup_filename
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Configuration backed up to {backup_filename}',
            'backup_file': backup_filename
        })
        
    except Exception as e:
        logger.error(f"Error backing up Facebook configuration: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/restore', methods=['POST'])
def api_restore_facebook_config():
    """API endpoint to restore Facebook configuration from backup."""
    try:
        data = request.get_json()
        backup_file = data.get('backup_file')
        
        if not backup_file:
            return jsonify({'success': False, 'message': 'No backup file specified'})
        
        backup_path = Path("config_backups") / backup_file
        if not backup_path.exists():
            return jsonify({'success': False, 'message': 'Backup file not found'})
        
        # Load backup data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        config_data = backup_data.get('config', {})
        
        # Restore configuration
        extraction_config = config_data.get('extraction', {})
        loader_config = config_data.get('loader', {})
        
        update_params = {}
        if extraction_config:
            update_params['extraction'] = extraction_config
        if loader_config:
            update_params['loader'] = loader_config
        
        if update_params:
            update_facebook_config(**update_params)
            
            # Send reload signal
            reload_signal_file = Path("facebook_config_reload.signal")
            with open(reload_signal_file, 'w') as f:
                f.write(str(datetime.now()))
        
        return jsonify({
            'success': True,
            'message': f'Configuration restored from {backup_file}',
            'restored_timestamp': backup_data.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error restoring Facebook configuration: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/facebook/config/backups')
def api_list_facebook_config_backups():
    """API endpoint to list available configuration backups."""
    try:
        backup_dir = Path("config_backups")
        if not backup_dir.exists():
            return jsonify({'backups': []})
        
        backups = []
        for backup_file in backup_dir.glob("facebook_config_backup_*.json"):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                
                backups.append({
                    'filename': backup_file.name,
                    'timestamp': backup_data.get('timestamp'),
                    'size': backup_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"Could not read backup file {backup_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'backups': backups})
        
    except Exception as e:
        logger.error(f"Error listing configuration backups: {e}")
        return jsonify({'backups': [], 'error': str(e)})


@app.route('/api/facebook/config/test', methods=['POST'])
def api_test_facebook_config():
    """API endpoint to test Facebook configuration."""
    try:
        config = get_facebook_config()
        
        # Calculate estimated metrics based on configuration
        max_pages = config.extraction.max_pages_per_run
        min_delay = config.extraction.min_api_delay
        posts_per_page = config.extraction.posts_limit_per_page
        
        # Estimate API calls (ultra-minimal: ~3-4 calls per source)
        estimated_api_calls = max_pages * 3.5  # Average of 3-4 calls per source
        
        # Estimate processing time
        api_time = estimated_api_calls * min_delay
        processing_time = max_pages * 2  # ~2 seconds processing per page
        estimated_time = api_time + processing_time
        
        # Determine efficiency rating
        calls_per_source = estimated_api_calls / max_pages if max_pages > 0 else 0
        
        if calls_per_source <= config.scraper.perfect_efficiency_threshold:
            efficiency_rating = "Perfect"
        elif calls_per_source <= config.scraper.excellent_efficiency_threshold:
            efficiency_rating = "Excellent"
        elif calls_per_source <= config.scraper.moderate_efficiency_threshold:
            efficiency_rating = "Moderate"
        else:
            efficiency_rating = "Needs Optimization"
        
        return jsonify({
            'success': True,
            'estimated_api_calls': int(estimated_api_calls),
            'estimated_time': int(estimated_time),
            'efficiency_rating': efficiency_rating,
            'calls_per_source': round(calls_per_source, 1),
            'max_pages': max_pages,
            'configuration_valid': True
        })
        
    except Exception as e:
        logger.error(f"Error testing Facebook configuration: {e}")
        return jsonify({'success': False, 'message': str(e)})


def serialize_for_json(obj):
    """Serialize objects for JSON transmission."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return {k: serialize_for_json(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected to dashboard')
    try:
        status = dashboard_manager.get_system_status()
        serialized_status = serialize_for_json(status)
        emit('status', serialized_status)
    except Exception as e:
        logger.error(f"Error sending status on connect: {e}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected from dashboard')


@socketio.on('request_update')
def handle_request_update():
    """Handle client request for status update."""
    try:
        status = dashboard_manager.get_system_status()
        serialized_status = serialize_for_json(status)
        emit('status', serialized_status)
    except Exception as e:
        logger.error(f"Error sending status update: {e}")


def background_task():
    """Background task to send periodic updates."""
    while True:
        try:
            time.sleep(5)  # Update every 5 seconds
            status = dashboard_manager.get_system_status()
            serialized_status = serialize_for_json(status)
            socketio.emit('status', serialized_status)
        except Exception as e:
            logger.error(f"Background task error: {e}")
            time.sleep(10)  # Wait longer on error


def start_background_thread():
    """Start background thread for real-time updates."""
    global background_thread
    with thread_lock:
        if background_thread is None:
            background_thread = socketio.start_background_task(background_task)


if __name__ == '__main__':
    # Initialize dashboard manager
    if dashboard_manager.initialize():
        logger.info("Dashboard initialized successfully")
    else:
        logger.warning("Dashboard initialization had issues, some features may not work")
    
    # Start background thread
    start_background_thread()
    
    # Run the Flask app
    logger.info("Tunisia Intelligence Web Dashboard")
    logger.info("=" * 50)
    logger.info("Starting web server...")
    logger.info("Dashboard will be available at: http://localhost:5000")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Use threading mode to avoid SSL issues
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False,
            log_output=False
        )
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        logger.error(f"Dashboard error: {e}", exc_info=True)
