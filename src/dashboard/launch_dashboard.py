#!/usr/bin/env python3
"""
Tunisia Intelligence Dashboard Launcher

This script provides a convenient way to launch the web dashboard
with proper integration to the unified control system.

Usage:
    python launch_dashboard.py                  # Launch with default settings
    python launch_dashboard.py --port 8080     # Launch on custom port
    python launch_dashboard.py --external      # Allow external connections
    python launch_dashboard.py --with-controller # Start controller alongside dashboard
"""

import argparse
import sys
import os
import subprocess
import time
import threading
from pathlib import Path
import signal
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


class DashboardLauncher:
    """Launcher for the Tunisia Intelligence Dashboard with integrated control."""
    
    def __init__(self):
        self.dashboard_process = None
        self.controller_process = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def check_prerequisites(self):
        """Check if all prerequisites are met."""
        logger.info("Checking prerequisites...")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ required")
        
        # Check if unified control system is available
        try:
            from config.unified_control import get_unified_control
            control_settings = get_unified_control()
            logger.info("Unified control system available")
        except Exception as e:
            issues.append(f"Unified control system not available: {e}")
        
        # Check if web dashboard files exist
        dashboard_dir = project_root / "web_dashboard"
        required_files = [
            dashboard_dir / "app.py",
            dashboard_dir / "templates" / "dashboard.html",
            dashboard_dir / "requirements.txt"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                issues.append(f"Missing dashboard file: {file_path}")
        
        # Check database connectivity
        try:
            from config.database import DatabaseManager
            db = DatabaseManager()
            result = db.client.table("sources").select("id").limit(1).execute()
            logger.info("Database connectivity verified")
        except Exception as e:
            issues.append(f"Database connectivity issue: {e}")
        
        if issues:
            logger.error("Prerequisites not met:")
            for issue in issues:
                logger.error(f"   - {issue}")
            return False
        
        logger.info("All prerequisites satisfied")
        return True
    
    def install_dashboard_dependencies(self):
        """Install dashboard dependencies."""
        logger.info("Installing dashboard dependencies...")
        
        requirements_file = project_root / "web_dashboard" / "requirements.txt"
        
        if not requirements_file.exists():
            logger.error("Dashboard requirements file not found")
            return False
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            logger.info("Dashboard dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dashboard dependencies: {e}")
            return False
    
    def start_controller(self):
        """Start the unified pipeline controller in background."""
        logger.info("Starting unified pipeline controller...")
        
        try:
            controller_script = project_root / "unified_control.py"
            
            if not controller_script.exists():
                logger.error("Unified control script not found")
                return False
            
            # Start controller process
            self.controller_process = subprocess.Popen([
                sys.executable, str(controller_script), "--start", "--background"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it's still running
            if self.controller_process.poll() is None:
                logger.info("Unified pipeline controller started successfully")
                return True
            else:
                stdout, stderr = self.controller_process.communicate()
                logger.error(f"Controller failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start controller: {e}")
            return False
    
    def start_dashboard(self, host='localhost', port=5000, debug=False):
        """Start the web dashboard."""
        logger.info("Starting Tunisia Intelligence Web Dashboard...")
        
        try:
            dashboard_script = project_root / "web_dashboard" / "start_dashboard.py"
            
            if not dashboard_script.exists():
                logger.error("Dashboard startup script not found")
                return False
            
            # Prepare command arguments
            cmd = [
                sys.executable, str(dashboard_script),
                "--host", host,
                "--port", str(port)
            ]
            
            if debug:
                cmd.append("--debug")
            
            # Start dashboard process
            self.dashboard_process = subprocess.Popen(
                cmd,
                cwd=str(dashboard_script.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            # Monitor dashboard output in a separate thread
            def monitor_dashboard():
                try:
                    for line in iter(self.dashboard_process.stdout.readline, ''):
                        if line.strip():
                            logger.info(f"Dashboard: {line.strip()}")
                except Exception as e:
                    logger.error(f"Error monitoring dashboard output: {e}")
            
            monitor_thread = threading.Thread(target=monitor_dashboard, daemon=True)
            monitor_thread.start()
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if self.dashboard_process.poll() is None:
                logger.info(f"Dashboard started successfully on http://{host}:{port}")
                return True
            else:
                logger.error("Dashboard failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            return False
    
    def wait_for_processes(self):
        """Wait for processes to complete."""
        self.running = True
        
        try:
            while self.running:
                # Check if dashboard is still running
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    logger.warning("Dashboard process has stopped")
                    break
                
                # Check if controller is still running (if started)
                if self.controller_process and self.controller_process.poll() is not None:
                    logger.warning("Controller process has stopped")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop_all()
    
    def stop_all(self):
        """Stop all processes."""
        self.running = False
        
        logger.info("Stopping all processes...")
        
        # Stop dashboard
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=10)
                logger.info("Dashboard stopped")
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
                logger.info("Dashboard force stopped")
            except Exception as e:
                logger.error(f"Error stopping dashboard: {e}")
        
        # Stop controller
        if self.controller_process:
            try:
                self.controller_process.terminate()
                self.controller_process.wait(timeout=10)
                logger.info("Controller stopped")
            except subprocess.TimeoutExpired:
                self.controller_process.kill()
                logger.info("Controller force stopped")
            except Exception as e:
                logger.error(f"Error stopping controller: {e}")
    
    def launch(self, host='localhost', port=5000, debug=False, with_controller=False, install_deps=False):
        """Launch the dashboard with optional controller."""
        
        print("Tunisia Intelligence Dashboard Launcher")
        print("=" * 60)
        
        # Install dependencies if requested
        if install_deps:
            if not self.install_dashboard_dependencies():
                return False
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites not met. Use --install-deps to install dependencies.")
            return False
        
        # Start controller if requested
        if with_controller:
            if not self.start_controller():
                logger.error("Failed to start controller")
                return False
        
        # Start dashboard
        if not self.start_dashboard(host, port, debug):
            logger.error("Failed to start dashboard")
            self.stop_all()
            return False
        
        # Print access information
        print("\n" + "=" * 60)
        print("Dashboard Access Information:")
        print(f"   Local URL: http://localhost:{port}")
        if host != 'localhost':
            print(f"   Network URL: http://{host}:{port}")
        print("\nAvailable Features:")
        print("   • Real-time pipeline monitoring")
        print("   • Interactive pipeline controls")
        print("   • System metrics and alerts")
        print("   • Live log viewer")
        print("   • Performance analytics")
        if with_controller:
            print("   • Integrated pipeline controller")
        print("\nPress Ctrl+C to stop")
        print("=" * 60)
        
        # Wait for processes
        self.wait_for_processes()
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tunisia Intelligence Dashboard Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Launch dashboard only
  %(prog)s --with-controller        # Launch with integrated controller
  %(prog)s --port 8080             # Launch on custom port
  %(prog)s --external              # Allow external connections
  %(prog)s --install-deps          # Install dependencies first
        """
    )
    
    parser.add_argument('--host', default='localhost',
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--external', action='store_true',
                       help='Allow external connections (sets host to 0.0.0.0)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--with-controller', action='store_true',
                       help='Start unified pipeline controller alongside dashboard')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install dashboard dependencies before starting')
    
    args = parser.parse_args()
    
    # Handle external connections
    if args.external:
        args.host = '0.0.0.0'
        logger.warning("Dashboard will be accessible from external networks")
    
    # Create and run launcher
    launcher = DashboardLauncher()
    
    try:
        success = launcher.launch(
            host=args.host,
            port=args.port,
            debug=args.debug,
            with_controller=args.with_controller,
            install_deps=args.install_deps
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Launcher error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
