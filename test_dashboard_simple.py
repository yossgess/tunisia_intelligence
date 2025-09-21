#!/usr/bin/env python3
"""
Simple test script for the Tunisia Intelligence Web Dashboard

This script tests the basic functionality of the dashboard without
the full unified control system integration.
"""

import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_flask_socketio():
    """Test basic Flask-SocketIO functionality."""
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        
        # Create a simple test app
        app = Flask(__name__)
        app.secret_key = 'test_key'
        
        # Initialize SocketIO with threading mode
        socketio = SocketIO(app, async_mode='threading')
        
        @app.route('/')
        def index():
            return '<h1>Tunisia Intelligence Dashboard Test</h1><p>Flask-SocketIO is working!</p>'
        
        @socketio.on('connect')
        def handle_connect():
            logger.info('Client connected')
        
        @socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected')
        
        logger.info("Flask-SocketIO test app created successfully")
        logger.info("Starting test server on http://localhost:5001")
        logger.info("Press Ctrl+C to stop")
        
        # Run the test server
        socketio.run(
            app,
            host='localhost',
            port=5001,
            debug=False,
            use_reloader=False,
            log_output=False
        )
        
    except KeyboardInterrupt:
        logger.info("Test server stopped by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_imports():
    """Test importing dashboard components."""
    try:
        logger.info("Testing imports...")
        
        # Test Flask imports
        from flask import Flask
        from flask_socketio import SocketIO
        logger.info("✓ Flask and Flask-SocketIO imported successfully")
        
        # Test Plotly import
        import plotly.graph_objs as go
        import plotly.utils
        logger.info("✓ Plotly imported successfully")
        
        # Test other dependencies
        import requests
        import psutil
        logger.info("✓ Additional dependencies imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during imports: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Tunisia Intelligence Dashboard - Simple Test")
    logger.info("=" * 50)
    
    # Test imports first
    if not test_imports():
        logger.error("Import tests failed")
        return False
    
    logger.info("All imports successful, starting Flask-SocketIO test...")
    
    # Test Flask-SocketIO
    return test_flask_socketio()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
