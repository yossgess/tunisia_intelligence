#!/usr/bin/env python3
"""
Tunisia Intelligence Web Dashboard Startup Script

This script provides an easy way to start the web dashboard with proper
initialization and error handling.

Usage:
    python start_dashboard.py                    # Start with default settings
    python start_dashboard.py --port 8080       # Start on custom port
    python start_dashboard.py --debug           # Start in debug mode
    python start_dashboard.py --host 0.0.0.0    # Allow external connections
"""

import argparse
import sys
import os
import logging
from pathlib import Path
import subprocess
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'flask',
        'flask-socketio',
        'plotly',
        'psutil',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger = logging.getLogger(__name__)
        logger.error("Missing required packages:")
        for package in missing_packages:
            logger.error(f"   - {package}")
        logger.info("Install missing packages with:")
        logger.info(f"   pip install {' '.join(missing_packages)}")
        logger.info("Or install all dashboard requirements:")
        logger.info("   pip install -r web_dashboard/requirements.txt")
        return False
    
    return True

def check_system_requirements():
    """Check system requirements and dependencies."""
    logger = logging.getLogger(__name__)
    logger.info("Checking system requirements...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check required directories
    required_dirs = ['logs', 'monitoring', 'config']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_name}")
    
    # Check configuration
    try:
        from config.unified_control import get_unified_control
        control_settings = get_unified_control()
        if not control_settings.master_enabled:
            issues.append("Master control is disabled (MASTER_ENABLED=false)")
    except Exception as e:
        issues.append(f"Configuration error: {e}")
    
    # Check database connectivity
    try:
        from config.database import DatabaseManager
        db = DatabaseManager()
        result = db.client.table("sources").select("id").limit(1).execute()
        logger.info("Database connectivity verified")
    except Exception as e:
        issues.append(f"Database connectivity issue: {e}")
    
    # Check Ollama connectivity (for AI enrichment)
    try:
        import requests
        from config.unified_control import get_unified_control
        control_settings = get_unified_control()
        if control_settings.ai_enrichment.enabled:
            response = requests.get(f"{control_settings.ai_enrichment.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama server connectivity verified")
            else:
                issues.append("Ollama server not responding")
    except Exception as e:
        if control_settings.ai_enrichment.enabled:
            issues.append(f"Ollama connectivity issue: {e}")
    
    if issues:
        logger.warning("System Issues Found:")
        for issue in issues:
            logger.warning(f"   - {issue}")
        logger.warning("Some features may not work properly. Please resolve these issues.")
        return False
    else:
        logger.info("All system requirements satisfied")
        return True

def start_dashboard(host='localhost', port=5000, debug=False):
    """Start the web dashboard."""
    logger = logging.getLogger(__name__)
    logger.info("Tunisia Intelligence Web Dashboard")
    logger.info("=" * 60)
    logger.info(f"Starting web server on http://{host}:{port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        # Import and start the Flask app
        from app import app, socketio, dashboard_manager
        
        # Initialize dashboard manager
        if dashboard_manager.initialize():
            logger.info("Dashboard manager initialized successfully")
        else:
            logger.warning("Dashboard initialization had issues, some features may not work")
        
        # Configure logging
        if not debug:
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
            logging.getLogger('socketio').setLevel(logging.WARNING)
            logging.getLogger('engineio').setLevel(logging.WARNING)
        
        # Start the server with threading mode to avoid SSL issues
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=debug,
            use_reloader=False,  # Disable reloader to prevent issues
            log_output=debug
        )
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard startup error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return False
    
    return True

def install_dependencies():
    """Install required dependencies."""
    logger = logging.getLogger(__name__)
    logger.info("Installing dashboard dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error("Requirements file not found")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main entry point."""
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Tunisia Intelligence Web Dashboard Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start with default settings
  %(prog)s --port 8080             # Start on custom port
  %(prog)s --debug                 # Start in debug mode
  %(prog)s --host 0.0.0.0          # Allow external connections
  %(prog)s --install-deps          # Install dependencies only
        """
    )
    
    parser.add_argument('--host', default='localhost',
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install dependencies and exit')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip system requirement checks')
    parser.add_argument('--force', action='store_true',
                       help='Force start even if checks fail')
    
    args = parser.parse_args()
    
    # Handle dependency installation
    if args.install_deps:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    # Check dependencies
    if not check_dependencies():
        if not args.force:
            logger.info("Use --install-deps to install missing packages")
            logger.info("Or use --force to start anyway (some features may not work)")
            sys.exit(1)
        else:
            logger.warning("Starting with missing dependencies (--force used)")
    
    # Check system requirements
    if not args.skip_checks:
        if not check_system_requirements():
            if not args.force:
                logger.info("Use --force to start anyway or --skip-checks to skip validation")
                sys.exit(1)
            else:
                logger.warning("Starting with system issues (--force used)")
    
    # Start the dashboard
    success = start_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
