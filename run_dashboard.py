#!/usr/bin/env python3
"""
Tunisia Intelligence Dashboard Runner
Simple script to launch the enhanced dashboard with pipeline tabs and Facebook configuration.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run the Tunisia Intelligence Dashboard"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    dashboard_dir = project_root / "web_dashboard"
    
    # Check if dashboard directory exists
    if not dashboard_dir.exists():
        print("❌ Error: Dashboard directory not found!")
        print(f"Expected: {dashboard_dir}")
        return 1
    
    # Check if app.py exists
    app_file = dashboard_dir / "app.py"
    if not app_file.exists():
        print("❌ Error: Dashboard app.py not found!")
        print(f"Expected: {app_file}")
        return 1
    
    print("🚀 Starting Tunisia Intelligence Dashboard...")
    print("=" * 60)
    print("📊 Features Available:")
    print("  • Pipeline Tabs (RSS, Facebook, AI, Vectorization)")
    print("  • Facebook Configuration Interface")
    print("  • Real-time System Monitoring")
    print("  • Interactive Controls")
    print("=" * 60)
    print(f"🌐 Dashboard will be available at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the dashboard")
    print("=" * 60)
    
    try:
        # Change to dashboard directory and run the app
        os.chdir(dashboard_dir)
        
        # Run the dashboard
        result = subprocess.run([
            sys.executable, "app.py"
        ], cwd=dashboard_dir)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
