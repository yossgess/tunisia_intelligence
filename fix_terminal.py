#!/usr/bin/env python3
"""
Terminal recovery script for Tunisia Intelligence RSS scraper.

Run this if your terminal gets stuck after running the RSS loader.
"""
import sys
import os

def fix_terminal():
    """Fix terminal state and restore prompt."""
    print("🔧 Fixing terminal state...")
    
    # Flush all streams
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Reset terminal (Windows)
    if os.name == 'nt':
        os.system('cls')
        print("✅ Terminal cleared (Windows)")
    else:
        # Unix/Linux/Mac
        os.system('reset')
        print("✅ Terminal reset (Unix)")
    
    # Print current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Show environment info
    if 'VIRTUAL_ENV' in os.environ:
        venv_path = os.environ['VIRTUAL_ENV']
        print(f"🐍 Virtual environment: {venv_path}")
    else:
        print("🐍 No virtual environment detected")
    
    print("\n✅ Terminal should be working now!")
    print("💡 You can now type commands normally.")
    
    # Test prompt
    print("\n" + "="*50)
    print("🧪 TERMINAL TEST")
    print("="*50)
    print("If you can see this message clearly, your terminal is working!")
    print("Try typing: python --version")

if __name__ == "__main__":
    fix_terminal()
