#!/usr/bin/env python3
"""
Integration Test Suite for Tunisia Intelligence Unified Control System

This script tests all components of the unified control system to ensure
proper integration and functionality.

Usage:
    python test_unified_control.py                    # Run all tests
    python test_unified_control.py --quick            # Run quick tests only
    python test_unified_control.py --component rss    # Test specific component
"""

import argparse
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import test components
from config.unified_control import get_unified_control, reload_unified_control
from unified_pipeline_controller import UnifiedPipelineController
from monitoring.unified_monitoring import get_unified_monitor
from unified_control_cli import UnifiedControlCLI


class TestResult:
    """Test result container."""
    
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now()


class UnifiedControlTester:
    """Comprehensive test suite for unified control system."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.verbose = True
    
    def log(self, message: str, level: str = "INFO"):
        """Log test message."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and record result."""
        self.log(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            test_func(*args, **kwargs)
            duration = time.time() - start_time
            result = TestResult(test_name, True, "PASSED", duration)
            self.log(f"✅ {test_name} - PASSED ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            result = TestResult(test_name, False, error_msg, duration)
            self.log(f"❌ {test_name} - FAILED: {error_msg} ({duration:.2f}s)", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc(), "DEBUG")
        
        self.results.append(result)
        return result
    
    def test_configuration_loading(self):
        """Test configuration system loading."""
        # Test basic configuration loading
        control_settings = get_unified_control()
        assert control_settings is not None, "Failed to load unified control settings"
        
        # Test configuration sections
        assert hasattr(control_settings, 'rss'), "RSS configuration missing"
        assert hasattr(control_settings, 'facebook'), "Facebook configuration missing"
        assert hasattr(control_settings, 'ai_enrichment'), "AI enrichment configuration missing"
        assert hasattr(control_settings, 'vectorization'), "Vectorization configuration missing"
        assert hasattr(control_settings, 'monitoring'), "Monitoring configuration missing"
        assert hasattr(control_settings, 'scheduling'), "Scheduling configuration missing"
        
        # Test configuration reload
        reload_unified_control()
        reloaded_settings = get_unified_control()
        assert reloaded_settings is not None, "Failed to reload configuration"
    
    def test_pipeline_configuration(self):
        """Test pipeline-specific configuration."""
        control_settings = get_unified_control()
        
        # Test RSS configuration
        rss_config = control_settings.rss
        assert rss_config.batch_size > 0, "Invalid RSS batch size"
        assert rss_config.max_retries >= 0, "Invalid RSS max retries"
        assert rss_config.delay_between_sources >= 0, "Invalid RSS delay"
        
        # Test Facebook configuration
        facebook_config = control_settings.facebook
        assert facebook_config.api_calls_per_hour > 0, "Invalid Facebook API calls limit"
        assert facebook_config.pages_per_batch > 0, "Invalid Facebook batch size"
        
        # Test AI enrichment configuration
        ai_config = control_settings.ai_enrichment
        assert ai_config.batch_size > 0, "Invalid AI batch size"
        assert ai_config.model_temperature >= 0, "Invalid AI model temperature"
        assert ai_config.max_tokens > 0, "Invalid AI max tokens"
        
        # Test vectorization configuration
        vector_config = control_settings.vectorization
        assert vector_config.batch_size > 0, "Invalid vectorization batch size"
        assert vector_config.embedding_dimensions > 0, "Invalid embedding dimensions"
    
    def test_pipeline_enablement(self):
        """Test pipeline enablement logic."""
        control_settings = get_unified_control()
        
        # Test pipeline enablement checks
        pipelines = ['rss', 'facebook', 'ai_enrichment', 'vectorization']
        for pipeline in pipelines:
            enabled = control_settings.is_pipeline_enabled(pipeline)
            mode = control_settings.get_pipeline_mode(pipeline)
            assert isinstance(enabled, bool), f"Pipeline {pipeline} enablement check failed"
            assert mode is not None, f"Pipeline {pipeline} mode check failed"
        
        # Test processing order
        order = control_settings.get_processing_order()
        assert isinstance(order, list), "Processing order should be a list"
        assert len(order) > 0, "Processing order should not be empty"
    
    def test_controller_initialization(self):
        """Test pipeline controller initialization."""
        controller = UnifiedPipelineController()
        assert controller is not None, "Failed to initialize controller"
        assert hasattr(controller, 'control_settings'), "Controller missing control settings"
        assert hasattr(controller, 'resource_monitor'), "Controller missing resource monitor"
        assert hasattr(controller, 'pipeline_metrics'), "Controller missing pipeline metrics"
    
    def test_monitoring_system(self):
        """Test monitoring system initialization."""
        monitor = get_unified_monitor()
        assert monitor is not None, "Failed to initialize monitoring system"
        assert hasattr(monitor, 'metrics_collector'), "Monitor missing metrics collector"
        assert hasattr(monitor, 'alert_manager'), "Monitor missing alert manager"
        assert hasattr(monitor, 'health_checker'), "Monitor missing health checker"
        
        # Test metrics collection
        dashboard_data = monitor.get_dashboard_data()
        assert isinstance(dashboard_data, dict), "Dashboard data should be a dictionary"
        assert 'timestamp' in dashboard_data, "Dashboard data missing timestamp"
        assert 'system_health' in dashboard_data, "Dashboard data missing system health"
    
    def test_cli_interface(self):
        """Test CLI interface initialization."""
        cli = UnifiedControlCLI()
        assert cli is not None, "Failed to initialize CLI"
        assert hasattr(cli, 'controller'), "CLI missing controller reference"
        
        # Test configuration display (should not raise exceptions)
        try:
            cli.show_configuration()
        except Exception as e:
            raise AssertionError(f"CLI configuration display failed: {e}")
    
    def test_database_connectivity(self):
        """Test database connectivity."""
        try:
            from config.database import DatabaseManager
            db = DatabaseManager()
            
            # Test basic connectivity
            result = db.client.table("sources").select("id").limit(1).execute()
            assert result is not None, "Database query failed"
            
        except Exception as e:
            raise AssertionError(f"Database connectivity test failed: {e}")
    
    def test_ollama_connectivity(self):
        """Test Ollama server connectivity (if enabled)."""
        control_settings = get_unified_control()
        
        if not control_settings.ai_enrichment.enabled:
            self.log("Skipping Ollama test - AI enrichment disabled")
            return
        
        try:
            import requests
            url = f"{control_settings.ai_enrichment.ollama_url}/api/tags"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                self.log("✅ Ollama server is accessible")
            else:
                raise AssertionError(f"Ollama server returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"Ollama connectivity failed: {e}")
    
    def test_resource_monitoring(self):
        """Test resource monitoring functionality."""
        monitor = get_unified_monitor()
        
        # Test system metrics collection
        system_metrics = monitor.metrics_collector.collect_system_metrics()
        assert system_metrics is not None, "Failed to collect system metrics"
        assert system_metrics.cpu_percent >= 0, "Invalid CPU percentage"
        assert system_metrics.memory_mb > 0, "Invalid memory usage"
        
        # Test health check
        health_status, issues = monitor.health_checker.check_system_health()
        assert health_status is not None, "Health check failed"
        assert isinstance(issues, list), "Health issues should be a list"
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from unified_pipeline_controller import RateLimiter
        
        # Test rate limiter initialization
        rate_limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        assert rate_limiter is not None, "Failed to initialize rate limiter"
        
        # Test rate limiting logic
        can_proceed = rate_limiter.can_proceed()
        assert isinstance(can_proceed, bool), "Rate limiter check should return boolean"
        
        # Record a request and test again
        rate_limiter.record_request()
        can_proceed_after = rate_limiter.can_proceed()
        assert isinstance(can_proceed_after, bool), "Rate limiter check after request should return boolean"
    
    def test_pipeline_metrics(self):
        """Test pipeline metrics functionality."""
        from unified_pipeline_controller import PipelineMetrics, PipelineStatus
        
        # Test metrics creation
        metrics = PipelineMetrics(
            pipeline_name="test_pipeline",
            status=PipelineStatus.COMPLETED,
            items_processed=10,
            items_failed=1
        )
        
        assert metrics.pipeline_name == "test_pipeline", "Pipeline name not set correctly"
        assert metrics.success_rate == 0.9, "Success rate calculation incorrect"
    
    def test_alert_system(self):
        """Test alert system functionality."""
        monitor = get_unified_monitor()
        alert_manager = monitor.alert_manager
        
        # Test alert creation
        from monitoring.unified_monitoring import AlertLevel
        alert = alert_manager.create_alert(
            AlertLevel.WARNING,
            "test_source",
            "Test alert message"
        )
        
        assert alert is not None, "Failed to create alert"
        assert alert.level == AlertLevel.WARNING, "Alert level not set correctly"
        assert alert.source == "test_source", "Alert source not set correctly"
        
        # Test alert retrieval
        active_alerts = alert_manager.get_active_alerts()
        assert isinstance(active_alerts, list), "Active alerts should be a list"
        
        # Clean up test alert
        if alert.id in alert_manager.active_alerts:
            alert_manager.resolve_alert(alert.id)
    
    def run_quick_tests(self):
        """Run quick tests for basic functionality."""
        self.log("🚀 Running Quick Test Suite")
        self.log("=" * 50)
        
        quick_tests = [
            ("Configuration Loading", self.test_configuration_loading),
            ("Pipeline Configuration", self.test_pipeline_configuration),
            ("Pipeline Enablement", self.test_pipeline_enablement),
            ("Controller Initialization", self.test_controller_initialization),
            ("CLI Interface", self.test_cli_interface),
        ]
        
        for test_name, test_func in quick_tests:
            self.run_test(test_name, test_func)
    
    def run_full_tests(self):
        """Run comprehensive test suite."""
        self.log("🚀 Running Full Test Suite")
        self.log("=" * 50)
        
        all_tests = [
            ("Configuration Loading", self.test_configuration_loading),
            ("Pipeline Configuration", self.test_pipeline_configuration),
            ("Pipeline Enablement", self.test_pipeline_enablement),
            ("Controller Initialization", self.test_controller_initialization),
            ("Monitoring System", self.test_monitoring_system),
            ("CLI Interface", self.test_cli_interface),
            ("Database Connectivity", self.test_database_connectivity),
            ("Ollama Connectivity", self.test_ollama_connectivity),
            ("Resource Monitoring", self.test_resource_monitoring),
            ("Rate Limiting", self.test_rate_limiting),
            ("Pipeline Metrics", self.test_pipeline_metrics),
            ("Alert System", self.test_alert_system),
        ]
        
        for test_name, test_func in all_tests:
            self.run_test(test_name, test_func)
    
    def run_component_tests(self, component: str):
        """Run tests for specific component."""
        self.log(f"🚀 Running {component.upper()} Component Tests")
        self.log("=" * 50)
        
        component_tests = {
            'config': [
                ("Configuration Loading", self.test_configuration_loading),
                ("Pipeline Configuration", self.test_pipeline_configuration),
                ("Pipeline Enablement", self.test_pipeline_enablement),
            ],
            'controller': [
                ("Controller Initialization", self.test_controller_initialization),
                ("Pipeline Metrics", self.test_pipeline_metrics),
                ("Rate Limiting", self.test_rate_limiting),
            ],
            'monitoring': [
                ("Monitoring System", self.test_monitoring_system),
                ("Resource Monitoring", self.test_resource_monitoring),
                ("Alert System", self.test_alert_system),
            ],
            'cli': [
                ("CLI Interface", self.test_cli_interface),
            ],
            'database': [
                ("Database Connectivity", self.test_database_connectivity),
            ],
            'ollama': [
                ("Ollama Connectivity", self.test_ollama_connectivity),
            ]
        }
        
        if component not in component_tests:
            self.log(f"❌ Unknown component: {component}")
            self.log(f"Available components: {', '.join(component_tests.keys())}")
            return
        
        for test_name, test_func in component_tests[component]:
            self.run_test(test_name, test_func)
    
    def print_summary(self):
        """Print test results summary."""
        if not self.results:
            self.log("No tests were run")
            return
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.passed])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        self.log("\n" + "=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        # Overall results
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        status_emoji = "✅" if failed_tests == 0 else "⚠️" if success_rate >= 70 else "❌"
        
        self.log(f"{status_emoji} Overall Status: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        self.log(f"⏱️ Total Duration: {total_duration:.2f} seconds")
        
        if failed_tests > 0:
            self.log(f"\n❌ Failed Tests ({failed_tests}):")
            for result in self.results:
                if not result.passed:
                    self.log(f"   • {result.name}: {result.message}")
        
        self.log(f"\n✅ Passed Tests ({passed_tests}):")
        for result in self.results:
            if result.passed:
                self.log(f"   • {result.name} ({result.duration:.2f}s)")
        
        # Recommendations
        if failed_tests > 0:
            self.log(f"\n💡 Recommendations:")
            if any("Database" in r.name for r in self.results if not r.passed):
                self.log("   • Check database configuration and connectivity")
            if any("Ollama" in r.name for r in self.results if not r.passed):
                self.log("   • Ensure Ollama server is running and accessible")
            if any("Configuration" in r.name for r in self.results if not r.passed):
                self.log("   • Review .env file and configuration settings")
        
        return failed_tests == 0


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Tunisia Intelligence Unified Control System Test Suite"
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only')
    parser.add_argument('--component', choices=['config', 'controller', 'monitoring', 'cli', 'database', 'ollama'],
                       help='Test specific component only')
    parser.add_argument('--verbose', '-v', action='store_true', default=True,
                       help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet output (overrides verbose)')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = UnifiedControlTester()
    tester.verbose = args.verbose and not args.quiet
    
    # Print banner
    if tester.verbose:
        print("🧪 Tunisia Intelligence Unified Control System - Test Suite")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    # Run appropriate tests
    try:
        if args.component:
            tester.run_component_tests(args.component)
        elif args.quick:
            tester.run_quick_tests()
        else:
            tester.run_full_tests()
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        if tester.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
