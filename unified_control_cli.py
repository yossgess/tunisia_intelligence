#!/usr/bin/env python3
"""
Unified Control CLI for Tunisia Intelligence System

Command-line interface for managing and monitoring all processing pipelines:
- Start/stop/pause/resume pipeline controller
- Execute individual pipelines
- Monitor pipeline status and metrics
- Configure pipeline parameters
- View logs and reports

Usage:
    python unified_control_cli.py start                    # Start all pipelines
    python unified_control_cli.py stop                     # Stop all pipelines
    python unified_control_cli.py status                   # Show status
    python unified_control_cli.py run rss                  # Run RSS pipeline only
    python unified_control_cli.py config show              # Show configuration
    python unified_control_cli.py config set rss.batch_size 25  # Set parameter
    python unified_control_cli.py logs                     # Show recent logs
    python unified_control_cli.py metrics                  # Show metrics
"""

import argparse
import asyncio
import json
import logging
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import signal
import os

# Import unified control components
from config.unified_control import (
    get_unified_control, reload_unified_control,
    PipelineMode, ProcessingPriority
)
from unified_pipeline_controller import UnifiedPipelineController, PipelineStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class UnifiedControlCLI:
    """Command-line interface for unified pipeline control."""
    
    def __init__(self):
        self.controller = None
        self.controller_thread = None
        self.running = False
    
    def start_controller(self, background: bool = False):
        """Start the unified pipeline controller."""
        if self.controller and self.running:
            print("❌ Controller is already running")
            return
        
        print("🚀 Starting Tunisia Intelligence Unified Pipeline Controller...")
        
        self.controller = UnifiedPipelineController()
        
        if background:
            self.controller_thread = threading.Thread(
                target=self.controller.start,
                daemon=True
            )
            self.controller_thread.start()
            self.running = True
            print("✅ Controller started in background")
        else:
            try:
                self.controller.start()
            except KeyboardInterrupt:
                print("\n🛑 Controller stopped by user")
            finally:
                self.running = False
    
    def stop_controller(self):
        """Stop the unified pipeline controller."""
        if not self.controller or not self.running:
            print("❌ Controller is not running")
            return
        
        print("🛑 Stopping controller...")
        self.controller.stop()
        self.running = False
        
        if self.controller_thread:
            self.controller_thread.join(timeout=10)
        
        print("✅ Controller stopped")
    
    def pause_controller(self):
        """Pause the pipeline controller."""
        if not self.controller or not self.running:
            print("❌ Controller is not running")
            return
        
        self.controller.pause()
        print("⏸️ Controller paused")
    
    def resume_controller(self):
        """Resume the pipeline controller."""
        if not self.controller or not self.running:
            print("❌ Controller is not running")
            return
        
        self.controller.resume()
        print("▶️ Controller resumed")
    
    def show_status(self):
        """Show current controller and pipeline status."""
        control_settings = get_unified_control()
        
        print("🎛️ Tunisia Intelligence Unified Control Status")
        print("=" * 60)
        
        # Master controls
        print(f"Master Enabled: {'✅' if control_settings.master_enabled else '❌'}")
        print(f"Maintenance Mode: {'🔧' if control_settings.maintenance_mode else '✅'}")
        print(f"Environment: {control_settings.environment}")
        print(f"Debug Mode: {'🐛' if control_settings.debug else '✅'}")
        
        print("\n📊 Pipeline Status:")
        print("-" * 40)
        
        # Pipeline status
        pipelines = ['rss', 'facebook', 'ai_enrichment', 'vectorization']
        for pipeline_name in pipelines:
            enabled = control_settings.is_pipeline_enabled(pipeline_name)
            mode = control_settings.get_pipeline_mode(pipeline_name)
            
            status_icon = "✅" if enabled else "❌"
            print(f"{status_icon} {pipeline_name.replace('_', ' ').title()}: {mode.value}")
        
        # Controller status
        if self.controller and self.running:
            controller_status = self.controller.get_status()
            print(f"\n🎯 Controller Status:")
            print(f"   Running: {'✅' if controller_status['running'] else '❌'}")
            print(f"   Paused: {'⏸️' if controller_status['paused'] else '▶️'}")
            print(f"   Current Cycle: {controller_status['current_cycle']}")
            
            # Resource metrics
            resource_metrics = controller_status.get('resource_metrics', {})
            if resource_metrics:
                print(f"   Memory Usage: {resource_metrics.get('memory_mb', 0):.1f} MB")
                print(f"   CPU Usage: {resource_metrics.get('cpu_percent', 0):.1f}%")
        else:
            print(f"\n🎯 Controller Status: ❌ Not Running")
    
    def run_single_pipeline(self, pipeline_name: str):
        """Run a single pipeline manually."""
        valid_pipelines = ['rss', 'facebook', 'ai_enrichment', 'vectorization']
        
        if pipeline_name not in valid_pipelines:
            print(f"❌ Invalid pipeline: {pipeline_name}")
            print(f"Valid pipelines: {', '.join(valid_pipelines)}")
            return
        
        print(f"🎯 Running {pipeline_name} pipeline...")
        
        try:
            controller = UnifiedPipelineController()
            metrics = controller.execute_single_pipeline(pipeline_name)
            
            print(f"\n📊 Pipeline Results:")
            print(f"   Status: {metrics.status.value}")
            print(f"   Duration: {metrics.duration_seconds:.1f}s")
            print(f"   Items Processed: {metrics.items_processed}")
            print(f"   Items Failed: {metrics.items_failed}")
            print(f"   Success Rate: {metrics.success_rate:.2%}")
            
            if metrics.processing_rate > 0:
                print(f"   Processing Rate: {metrics.processing_rate:.2f} items/sec")
            
            if metrics.errors:
                print(f"\n⚠️ Errors ({len(metrics.errors)}):")
                for error in metrics.errors[:5]:  # Show first 5 errors
                    print(f"   - {error}")
        
        except Exception as e:
            print(f"❌ Pipeline execution failed: {e}")
    
    def show_configuration(self, section: Optional[str] = None):
        """Show current configuration."""
        control_settings = get_unified_control()
        config_dict = control_settings.to_dict()
        
        print("⚙️ Tunisia Intelligence Configuration")
        print("=" * 50)
        
        if section:
            if section in config_dict:
                self._print_config_section(section, config_dict[section])
            else:
                print(f"❌ Configuration section '{section}' not found")
                print(f"Available sections: {', '.join(config_dict.keys())}")
        else:
            for section_name, section_data in config_dict.items():
                if isinstance(section_data, dict):
                    self._print_config_section(section_name, section_data)
                    print()
    
    def _print_config_section(self, section_name: str, section_data: Dict[str, Any]):
        """Print a configuration section."""
        print(f"📋 {section_name.replace('_', ' ').title()}:")
        print("-" * 30)
        
        for key, value in section_data.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    
    def set_configuration(self, parameter_path: str, value: str):
        """Set a configuration parameter."""
        print(f"⚙️ Setting {parameter_path} = {value}")
        
        # Parse parameter path (e.g., "rss.batch_size" or "ai_enrichment.model_name")
        path_parts = parameter_path.split('.')
        
        if len(path_parts) != 2:
            print("❌ Parameter path must be in format: section.parameter")
            print("Example: rss.batch_size or ai_enrichment.model_name")
            return
        
        section_name, param_name = path_parts
        
        # Convert value to appropriate type
        converted_value = self._convert_value(value)
        
        # Set environment variable
        env_var_name = f"{section_name.upper()}_{param_name.upper()}"
        os.environ[env_var_name] = str(converted_value)
        
        print(f"✅ Set {env_var_name} = {converted_value}")
        print("🔄 Reload configuration to apply changes")
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def reload_configuration(self):
        """Reload configuration from environment variables."""
        print("🔄 Reloading configuration...")
        reload_unified_control()
        print("✅ Configuration reloaded")
    
    def show_logs(self, lines: int = 50, follow: bool = False):
        """Show recent logs."""
        log_file = Path("logs/unified_controller.log")
        
        if not log_file.exists():
            print("❌ Log file not found")
            return
        
        print(f"📋 Recent Logs (last {lines} lines):")
        print("=" * 60)
        
        if follow:
            # Follow logs (like tail -f)
            self._follow_logs(log_file)
        else:
            # Show last N lines
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:]
                    
                    for line in recent_lines:
                        print(line.rstrip())
            except Exception as e:
                print(f"❌ Error reading log file: {e}")
    
    def _follow_logs(self, log_file: Path):
        """Follow log file like tail -f."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Go to end of file
                f.seek(0, 2)
                
                print("📡 Following logs (Ctrl+C to stop)...")
                
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n🛑 Stopped following logs")
        except Exception as e:
            print(f"❌ Error following logs: {e}")
    
    def show_metrics(self):
        """Show pipeline metrics and statistics."""
        if not self.controller or not self.running:
            print("❌ Controller is not running - showing configuration only")
            self.show_configuration()
            return
        
        status = self.controller.get_status()
        
        print("📊 Pipeline Metrics")
        print("=" * 40)
        
        # Pipeline metrics
        pipeline_metrics = status.get('pipeline_metrics', {})
        if pipeline_metrics:
            for pipeline_name, metrics in pipeline_metrics.items():
                print(f"\n🔧 {pipeline_name.replace('_', ' ').title()}:")
                print(f"   Status: {metrics['status']}")
                print(f"   Items Processed: {metrics['items_processed']}")
                print(f"   Items Failed: {metrics['items_failed']}")
                print(f"   Success Rate: {metrics['success_rate']:.2%}")
                print(f"   Duration: {metrics['duration_seconds']:.1f}s")
        else:
            print("No pipeline metrics available")
        
        # Resource metrics
        resource_metrics = status.get('resource_metrics', {})
        if resource_metrics:
            print(f"\n💻 System Resources:")
            print(f"   Memory Usage: {resource_metrics.get('memory_mb', 0):.1f} MB")
            print(f"   CPU Usage: {resource_metrics.get('cpu_percent', 0):.1f}%")
            print(f"   Threads: {resource_metrics.get('num_threads', 0)}")
    
    def interactive_mode(self):
        """Start interactive mode."""
        print("🎛️ Tunisia Intelligence Unified Control - Interactive Mode")
        print("Type 'help' for available commands, 'exit' to quit")
        print("=" * 60)
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command in ['exit', 'quit', 'q']:
                    break
                elif command == 'help':
                    self._show_interactive_help()
                elif command == 'status':
                    self.show_status()
                elif command == 'start':
                    self.start_controller(background=True)
                elif command == 'stop':
                    self.stop_controller()
                elif command == 'pause':
                    self.pause_controller()
                elif command == 'resume':
                    self.resume_controller()
                elif command == 'config':
                    self.show_configuration()
                elif command == 'metrics':
                    self.show_metrics()
                elif command == 'logs':
                    self.show_logs(lines=20)
                elif command.startswith('run '):
                    pipeline = command.split(' ', 1)[1]
                    self.run_single_pipeline(pipeline)
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n🛑 Exiting interactive mode...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Cleanup
        if self.running:
            self.stop_controller()
    
    def _show_interactive_help(self):
        """Show help for interactive mode."""
        print("\n📚 Available Commands:")
        print("-" * 30)
        print("status    - Show system status")
        print("start     - Start controller")
        print("stop      - Stop controller")
        print("pause     - Pause controller")
        print("resume    - Resume controller")
        print("config    - Show configuration")
        print("metrics   - Show metrics")
        print("logs      - Show recent logs")
        print("run <pipeline> - Run single pipeline")
        print("help      - Show this help")
        print("exit      - Exit interactive mode")


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Tunisia Intelligence Unified Control CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start                          # Start all pipelines
  %(prog)s stop                           # Stop all pipelines
  %(prog)s status                         # Show status
  %(prog)s run rss                        # Run RSS pipeline only
  %(prog)s config show                    # Show configuration
  %(prog)s config set rss.batch_size 25   # Set parameter
  %(prog)s logs --follow                  # Follow logs
  %(prog)s interactive                    # Interactive mode
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start pipeline controller')
    start_parser.add_argument('--background', '-b', action='store_true',
                             help='Run in background')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop pipeline controller')
    
    # Pause command
    subparsers.add_parser('pause', help='Pause pipeline controller')
    
    # Resume command
    subparsers.add_parser('resume', help='Resume pipeline controller')
    
    # Status command
    subparsers.add_parser('status', help='Show controller status')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run single pipeline')
    run_parser.add_argument('pipeline', choices=['rss', 'facebook', 'ai_enrichment', 'vectorization'],
                           help='Pipeline to run')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    
    show_config_parser = config_subparsers.add_parser('show', help='Show configuration')
    show_config_parser.add_argument('section', nargs='?', help='Configuration section')
    
    set_config_parser = config_subparsers.add_parser('set', help='Set configuration parameter')
    set_config_parser.add_argument('parameter', help='Parameter path (e.g., rss.batch_size)')
    set_config_parser.add_argument('value', help='Parameter value')
    
    config_subparsers.add_parser('reload', help='Reload configuration')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show logs')
    logs_parser.add_argument('--lines', '-n', type=int, default=50,
                            help='Number of lines to show')
    logs_parser.add_argument('--follow', '-f', action='store_true',
                            help='Follow logs (like tail -f)')
    
    # Metrics command
    subparsers.add_parser('metrics', help='Show metrics')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Start interactive mode')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = UnifiedControlCLI()
    
    try:
        if args.command == 'start':
            cli.start_controller(background=args.background)
        
        elif args.command == 'stop':
            cli.stop_controller()
        
        elif args.command == 'pause':
            cli.pause_controller()
        
        elif args.command == 'resume':
            cli.resume_controller()
        
        elif args.command == 'status':
            cli.show_status()
        
        elif args.command == 'run':
            cli.run_single_pipeline(args.pipeline)
        
        elif args.command == 'config':
            if args.config_action == 'show':
                cli.show_configuration(args.section if hasattr(args, 'section') else None)
            elif args.config_action == 'set':
                cli.set_configuration(args.parameter, args.value)
            elif args.config_action == 'reload':
                cli.reload_configuration()
            else:
                print("❌ Config action required: show, set, or reload")
        
        elif args.command == 'logs':
            cli.show_logs(lines=args.lines, follow=args.follow)
        
        elif args.command == 'metrics':
            cli.show_metrics()
        
        elif args.command == 'interactive':
            cli.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"CLI error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
