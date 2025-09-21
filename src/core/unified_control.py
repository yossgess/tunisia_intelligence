#!/usr/bin/env python3
"""
Tunisia Intelligence Unified Control System - Main Entry Point

This is the main entry point for the unified control system that manages all
processing pipelines in the Tunisia Intelligence system.

Usage:
    python unified_control.py                    # Start interactive mode
    python unified_control.py --start            # Start all pipelines
    python unified_control.py --status           # Show status
    python unified_control.py --config           # Show configuration
    python unified_control.py --monitor          # Start monitoring only
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import unified control components
from src.core.unified_control_cli import UnifiedControlCLI
from src.core.unified_pipeline_controller import UnifiedPipelineController
from monitoring.unified_monitoring import get_unified_monitor, start_monitoring, get_status_report
from config.unified_control import get_unified_control

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print system banner."""
    banner = """
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘                                                                              â•‘
â•‘                    Tunisia Intelligence Unified Control                      â•‘
â•‘                                                                              â•‘
â•‘    ðŸŽ›ï¸  Centralized Pipeline Management and Orchestration System             â•‘
â•‘                                                                              â•‘
â•‘    Modules:                                                                  â•‘
â•‘    â€¢ RSS Extraction & Loading Pipeline                                      â•‘
â•‘    â€¢ Facebook Extraction & Loading Pipeline                                 â•‘
â•‘    â€¢ AI Enrichment Processing Pipeline                                      â•‘
â•‘    â€¢ Vectorization Processing Pipeline                                      â•‘
â•‘    â€¢ Unified Monitoring & Alerting System                                   â•‘
â•‘                                                                              â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """
    print(banner)


def check_system_requirements():
    """Check system requirements and dependencies."""
    print("ðŸ” Checking system requirements...")
    
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
            print(f"âœ… Created directory: {dir_name}")
    
    # Check configuration
    try:
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
        print("âœ… Database connectivity verified")
    except Exception as e:
        issues.append(f"Database connectivity issue: {e}")
    
    # Check Ollama connectivity (for AI enrichment)
    try:
        import requests
        control_settings = get_unified_control()
        if control_settings.ai_enrichment.enabled:
            response = requests.get(f"{control_settings.ai_enrichment.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("âœ… Ollama server connectivity verified")
            else:
                issues.append("Ollama server not responding")
    except Exception as e:
        if control_settings.ai_enrichment.enabled:
            issues.append(f"Ollama connectivity issue: {e}")
    
    if issues:
        print("\nâš ï¸ System Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nSome features may not work properly. Please resolve these issues.")
        return False
    else:
        print("âœ… All system requirements satisfied")
        return True


def show_quick_status():
    """Show quick system status."""
    print("\nðŸ“Š Quick System Status")
    print("=" * 50)
    
    try:
        control_settings = get_unified_control()
        
        # Master controls
        print(f"Master Enabled: {'âœ…' if control_settings.master_enabled else 'âŒ'}")
        print(f"Maintenance Mode: {'ðŸ”§' if control_settings.maintenance_mode else 'âœ…'}")
        print(f"Environment: {control_settings.environment}")
        
        # Pipeline status
        pipelines = [
            ('RSS', 'rss'),
            ('Facebook', 'facebook'), 
            ('AI Enrichment', 'ai_enrichment'),
            ('Vectorization', 'vectorization')
        ]
        
        print(f"\nPipeline Status:")
        for display_name, pipeline_name in pipelines:
            enabled = control_settings.is_pipeline_enabled(pipeline_name)
            mode = control_settings.get_pipeline_mode(pipeline_name)
            status_icon = "âœ…" if enabled else "âŒ"
            print(f"  {status_icon} {display_name}: {mode.value}")
        
        # Monitoring status
        monitor = get_unified_monitor()
        print(f"\nMonitoring: {'âœ… Active' if monitor else 'âŒ Inactive'}")
        
    except Exception as e:
        print(f"âŒ Error getting status: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tunisia Intelligence Unified Control System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Interactive mode
  %(prog)s --start             # Start all pipelines
  %(prog)s --status            # Show system status
  %(prog)s --config            # Show configuration
  %(prog)s --monitor           # Start monitoring only
  %(prog)s --check             # Check system requirements
        """
    )
    
    parser.add_argument('--start', action='store_true', 
                       help='Start all pipelines automatically')
    parser.add_argument('--status', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--config', action='store_true',
                       help='Show configuration and exit')
    parser.add_argument('--monitor', action='store_true',
                       help='Start monitoring system only')
    parser.add_argument('--check', action='store_true',
                       help='Check system requirements and exit')
    parser.add_argument('--background', '-b', action='store_true',
                       help='Run in background mode')
    parser.add_argument('--no-banner', action='store_true',
                       help='Skip banner display')
    
    args = parser.parse_args()
    
    # Print banner unless suppressed
    if not args.no_banner:
        print_banner()
    
    # Handle specific actions
    if args.check:
        check_system_requirements()
        return
    
    if args.status:
        show_quick_status()
        return
    
    if args.config:
        cli = UnifiedControlCLI()
        cli.show_configuration()
        return
    
    if args.monitor:
        print("ðŸ” Starting monitoring system...")
        start_monitoring()
        try:
            import time
            while True:
                time.sleep(60)
                print(get_status_report())
                print("\n" + "="*60 + "\n")
        except KeyboardInterrupt:
            print("\nðŸ›‘ Monitoring stopped")
        return
    
    # Check system requirements
    if not check_system_requirements():
        print("\nâš ï¸ System requirements not met. Use --check for details.")
        if not args.start:  # Don't exit if explicitly starting
            return
    
    # Initialize CLI
    cli = UnifiedControlCLI()
    
    if args.start:
        print("ðŸš€ Starting Tunisia Intelligence Unified Control System...")
        show_quick_status()
        print("\n" + "="*60 + "\n")
        
        try:
            cli.start_controller(background=args.background)
        except KeyboardInterrupt:
            print("\nðŸ›‘ Startup interrupted by user")
        except Exception as e:
            print(f"âŒ Startup error: {e}")
            logger.error(f"Startup error: {e}", exc_info=True)
    else:
        # Default to interactive mode
        print("ðŸŽ›ï¸ Starting interactive mode...")
        print("Type 'help' for available commands, 'exit' to quit")
        show_quick_status()
        
        try:
            cli.interactive_mode()
        except KeyboardInterrupt:
            print("\nðŸ›‘ Interactive mode interrupted")
        except Exception as e:
            print(f"âŒ Interactive mode error: {e}")
            logger.error(f"Interactive mode error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
