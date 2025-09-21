#!/usr/bin/env python3
"""
Unified Monitoring System for Tunisia Intelligence

This module provides comprehensive monitoring and reporting for all pipelines:
- Real-time performance metrics
- Resource usage tracking
- Error detection and alerting
- Historical data analysis
- Dashboard generation
- Health checks and diagnostics
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import psutil
import sqlite3
from contextlib import contextmanager

from config.database import DatabaseManager
from config.unified_control import get_monitoring_control

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_gb: float
    disk_percent: float
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    active_threads: int = 0
    open_files: int = 0


@dataclass
class PipelineMetrics:
    """Pipeline-specific metrics."""
    pipeline_name: str
    timestamp: datetime
    status: str
    items_processed: int = 0
    items_failed: int = 0
    items_skipped: int = 0
    processing_rate: float = 0.0
    error_rate: float = 0.0
    avg_processing_time: float = 0.0
    queue_size: int = 0
    active_workers: int = 0
    last_error: Optional[str] = None


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    timestamp: datetime
    connection_count: int
    query_count: int
    avg_query_time: float
    slow_queries: int
    failed_queries: int
    table_sizes: Dict[str, int] = field(default_factory=dict)
    index_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert."""
    id: str
    timestamp: datetime
    level: AlertLevel
    source: str
    message: str
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """Collect and store system metrics."""
    
    def __init__(self):
        self.db_path = Path("monitoring/metrics.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self.process = psutil.Process()
        self.network_counters = psutil.net_io_counters()
        self.init_database()
    
    def init_database(self):
        """Initialize metrics database."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp TEXT PRIMARY KEY,
                    cpu_percent REAL,
                    memory_mb REAL,
                    memory_percent REAL,
                    disk_usage_gb REAL,
                    disk_percent REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_recv INTEGER,
                    active_threads INTEGER,
                    open_files INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_name TEXT,
                    timestamp TEXT,
                    status TEXT,
                    items_processed INTEGER,
                    items_failed INTEGER,
                    items_skipped INTEGER,
                    processing_rate REAL,
                    error_rate REAL,
                    avg_processing_time REAL,
                    queue_size INTEGER,
                    active_workers INTEGER,
                    last_error TEXT
                );
                
                CREATE TABLE IF NOT EXISTS database_metrics (
                    timestamp TEXT PRIMARY KEY,
                    connection_count INTEGER,
                    query_count INTEGER,
                    avg_query_time REAL,
                    slow_queries INTEGER,
                    failed_queries INTEGER,
                    table_sizes TEXT,
                    index_usage TEXT
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    level TEXT,
                    source TEXT,
                    message TEXT,
                    details TEXT,
                    resolved BOOLEAN,
                    resolved_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp 
                ON system_metrics(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_pipeline_timestamp 
                ON pipeline_metrics(pipeline_name, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp_level 
                ON alerts(timestamp, level);
            """)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU and Memory
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            disk_usage_gb = disk_usage.used / (1024**3)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Network
            net_counters = psutil.net_io_counters()
            
            # Process info
            active_threads = self.process.num_threads()
            try:
                open_files = len(self.process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_info.rss / (1024**2),
                memory_percent=memory_percent,
                disk_usage_gb=disk_usage_gb,
                disk_percent=disk_percent,
                network_bytes_sent=net_counters.bytes_sent,
                network_bytes_recv=net_counters.bytes_recv,
                active_threads=active_threads,
                open_files=open_files
            )
            
            # Store metrics
            self.store_system_metrics(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_usage_gb=0.0,
                disk_percent=0.0
            )
    
    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_metrics VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                metrics.cpu_percent,
                metrics.memory_mb,
                metrics.memory_percent,
                metrics.disk_usage_gb,
                metrics.disk_percent,
                metrics.network_bytes_sent,
                metrics.network_bytes_recv,
                metrics.active_threads,
                metrics.open_files
            ))
            conn.commit()
    
    def store_pipeline_metrics(self, metrics: PipelineMetrics):
        """Store pipeline metrics in database."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO pipeline_metrics 
                (pipeline_name, timestamp, status, items_processed, items_failed, 
                 items_skipped, processing_rate, error_rate, avg_processing_time,
                 queue_size, active_workers, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.pipeline_name,
                metrics.timestamp.isoformat(),
                metrics.status,
                metrics.items_processed,
                metrics.items_failed,
                metrics.items_skipped,
                metrics.processing_rate,
                metrics.error_rate,
                metrics.avg_processing_time,
                metrics.queue_size,
                metrics.active_workers,
                metrics.last_error
            ))
            conn.commit()
    
    def get_recent_system_metrics(self, hours: int = 24) -> List[SystemMetrics]:
        """Get recent system metrics."""
        since = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM system_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (since.isoformat(),))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append(SystemMetrics(
                    timestamp=datetime.fromisoformat(row[0]),
                    cpu_percent=row[1],
                    memory_mb=row[2],
                    memory_percent=row[3],
                    disk_usage_gb=row[4],
                    disk_percent=row[5],
                    network_bytes_sent=row[6],
                    network_bytes_recv=row[7],
                    active_threads=row[8],
                    open_files=row[9]
                ))
            
            return metrics
    
    def get_pipeline_metrics_summary(self, pipeline_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get pipeline metrics summary."""
        since = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(items_processed) as total_processed,
                    SUM(items_failed) as total_failed,
                    AVG(processing_rate) as avg_rate,
                    AVG(error_rate) as avg_error_rate,
                    MAX(timestamp) as last_run
                FROM pipeline_metrics 
                WHERE pipeline_name = ? AND timestamp > ?
            """, (pipeline_name, since.isoformat()))
            
            row = cursor.fetchone()
            if row:
                return {
                    'pipeline_name': pipeline_name,
                    'total_runs': row[0] or 0,
                    'total_processed': row[1] or 0,
                    'total_failed': row[2] or 0,
                    'avg_processing_rate': row[3] or 0.0,
                    'avg_error_rate': row[4] or 0.0,
                    'last_run': row[5]
                }
            
            return {'pipeline_name': pipeline_name, 'total_runs': 0}


class HealthChecker:
    """Perform system health checks."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring_config = get_monitoring_control()
    
    def check_system_health(self) -> Tuple[HealthStatus, List[str]]:
        """Perform comprehensive system health check."""
        issues = []
        status = HealthStatus.HEALTHY
        
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_recent_system_metrics(hours=1)
        if not recent_metrics:
            return HealthStatus.UNKNOWN, ["No recent metrics available"]
        
        latest_metrics = recent_metrics[0]
        
        # Check memory usage
        if latest_metrics.memory_percent > 90:
            issues.append(f"High memory usage: {latest_metrics.memory_percent:.1f}%")
            status = HealthStatus.CRITICAL
        elif latest_metrics.memory_percent > 80:
            issues.append(f"Memory usage warning: {latest_metrics.memory_percent:.1f}%")
            status = max(status, HealthStatus.WARNING)
        
        # Check CPU usage
        avg_cpu = sum(m.cpu_percent for m in recent_metrics[:10]) / min(10, len(recent_metrics))
        if avg_cpu > 90:
            issues.append(f"High CPU usage: {avg_cpu:.1f}%")
            status = HealthStatus.CRITICAL
        elif avg_cpu > 80:
            issues.append(f"CPU usage warning: {avg_cpu:.1f}%")
            status = max(status, HealthStatus.WARNING)
        
        # Check disk usage
        if latest_metrics.disk_percent > 95:
            issues.append(f"Disk space critical: {latest_metrics.disk_percent:.1f}%")
            status = HealthStatus.CRITICAL
        elif latest_metrics.disk_percent > 85:
            issues.append(f"Disk space warning: {latest_metrics.disk_percent:.1f}%")
            status = max(status, HealthStatus.WARNING)
        
        # Check database connectivity
        try:
            db = DatabaseManager()
            result = db.client.table("sources").select("id").limit(1).execute()
            if not result:
                issues.append("Database connectivity issue")
                status = HealthStatus.CRITICAL
        except Exception as e:
            issues.append(f"Database error: {str(e)}")
            status = HealthStatus.CRITICAL
        
        return status, issues
    
    def check_pipeline_health(self, pipeline_name: str) -> Tuple[HealthStatus, List[str]]:
        """Check health of specific pipeline."""
        issues = []
        status = HealthStatus.HEALTHY
        
        # Get pipeline metrics summary
        summary = self.metrics_collector.get_pipeline_metrics_summary(pipeline_name, hours=24)
        
        if summary['total_runs'] == 0:
            issues.append(f"No recent runs for {pipeline_name}")
            status = HealthStatus.WARNING
        else:
            # Check error rate
            if summary['avg_error_rate'] > 0.2:  # 20% error rate
                issues.append(f"High error rate: {summary['avg_error_rate']:.2%}")
                status = HealthStatus.CRITICAL
            elif summary['avg_error_rate'] > 0.1:  # 10% error rate
                issues.append(f"Elevated error rate: {summary['avg_error_rate']:.2%}")
                status = max(status, HealthStatus.WARNING)
            
            # Check if pipeline has run recently
            if summary['last_run']:
                last_run = datetime.fromisoformat(summary['last_run'])
                hours_since_last_run = (datetime.now() - last_run).total_seconds() / 3600
                
                if hours_since_last_run > 6:  # No run in 6 hours
                    issues.append(f"No recent activity: {hours_since_last_run:.1f} hours ago")
                    status = max(status, HealthStatus.WARNING)
        
        return status, issues


class AlertManager:
    """Manage system alerts and notifications."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring_config = get_monitoring_control()
        self.active_alerts = {}
    
    def create_alert(self, level: AlertLevel, source: str, message: str, 
                    details: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert."""
        alert_id = f"{source}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            level=level,
            source=source,
            message=message,
            details=details
        )
        
        # Store alert
        self.store_alert(alert)
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        logger.warning(f"Alert created: {level.value} - {source} - {message}")
        
        return alert
    
    def store_alert(self, alert: Alert):
        """Store alert in database."""
        with self.metrics_collector.get_connection() as conn:
            conn.execute("""
                INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.source,
                alert.message,
                json.dumps(alert.details) if alert.details else None,
                alert.resolved,
                alert.resolved_at.isoformat() if alert.resolved_at else None
            ))
            conn.commit()
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Update database
            with self.metrics_collector.get_connection() as conn:
                conn.execute("""
                    UPDATE alerts SET resolved = ?, resolved_at = ? WHERE id = ?
                """, (True, alert.resolved_at.isoformat(), alert_id))
                conn.commit()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def check_and_create_alerts(self):
        """Check system status and create alerts if needed."""
        # Check system health
        health_status, issues = HealthChecker(self.metrics_collector).check_system_health()
        
        if health_status == HealthStatus.CRITICAL:
            for issue in issues:
                self.create_alert(AlertLevel.CRITICAL, "system", issue)
        elif health_status == HealthStatus.WARNING:
            for issue in issues:
                self.create_alert(AlertLevel.WARNING, "system", issue)
        
        # Check pipeline health
        pipelines = ['rss', 'facebook', 'ai_enrichment', 'vectorization']
        health_checker = HealthChecker(self.metrics_collector)
        
        for pipeline in pipelines:
            pipeline_health, pipeline_issues = health_checker.check_pipeline_health(pipeline)
            
            if pipeline_health == HealthStatus.CRITICAL:
                for issue in pipeline_issues:
                    self.create_alert(AlertLevel.ERROR, pipeline, issue)
            elif pipeline_health == HealthStatus.WARNING:
                for issue in pipeline_issues:
                    self.create_alert(AlertLevel.WARNING, pipeline, issue)


class UnifiedMonitor:
    """Main unified monitoring system."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.health_checker = HealthChecker(self.metrics_collector)
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start the monitoring system."""
        if self.monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🔍 Unified monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logger.info("🛑 Unified monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Collect system metrics
                self.metrics_collector.collect_system_metrics()
                
                # Check for alerts every 5 minutes
                if int(time.time()) % 300 == 0:
                    self.alert_manager.check_and_create_alerts()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def record_pipeline_metrics(self, pipeline_name: str, **kwargs):
        """Record metrics for a pipeline."""
        metrics = PipelineMetrics(
            pipeline_name=pipeline_name,
            timestamp=datetime.now(),
            **kwargs
        )
        
        self.metrics_collector.store_pipeline_metrics(metrics)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        # System health
        health_status, health_issues = self.health_checker.check_system_health()
        
        # Recent system metrics
        recent_metrics = self.metrics_collector.get_recent_system_metrics(hours=24)
        
        # Pipeline summaries
        pipeline_summaries = {}
        for pipeline in ['rss', 'facebook', 'ai_enrichment', 'vectorization']:
            pipeline_summaries[pipeline] = self.metrics_collector.get_pipeline_metrics_summary(pipeline)
        
        # Active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': {
                'status': health_status.value,
                'issues': health_issues
            },
            'system_metrics': {
                'current': asdict(recent_metrics[0]) if recent_metrics else None,
                'history': [asdict(m) for m in recent_metrics[-100:]]  # Last 100 points
            },
            'pipeline_summaries': pipeline_summaries,
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'alert_counts': {
                'critical': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                'error': len([a for a in active_alerts if a.level == AlertLevel.ERROR]),
                'warning': len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
                'info': len([a for a in active_alerts if a.level == AlertLevel.INFO])
            }
        }
    
    def generate_status_report(self) -> str:
        """Generate a comprehensive status report."""
        dashboard_data = self.get_dashboard_data()
        
        report = []
        report.append("🔍 Tunisia Intelligence System Status Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System Health
        health = dashboard_data['system_health']
        health_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌", "unknown": "❓"}
        report.append(f"🏥 System Health: {health_emoji.get(health['status'], '❓')} {health['status'].upper()}")
        
        if health['issues']:
            report.append("   Issues:")
            for issue in health['issues']:
                report.append(f"   - {issue}")
        report.append("")
        
        # System Metrics
        if dashboard_data['system_metrics']['current']:
            metrics = dashboard_data['system_metrics']['current']
            report.append("💻 System Resources:")
            report.append(f"   CPU Usage: {metrics['cpu_percent']:.1f}%")
            report.append(f"   Memory: {metrics['memory_mb']:.1f} MB ({metrics['memory_percent']:.1f}%)")
            report.append(f"   Disk: {metrics['disk_usage_gb']:.1f} GB ({metrics['disk_percent']:.1f}%)")
            report.append(f"   Threads: {metrics['active_threads']}")
            report.append("")
        
        # Pipeline Status
        report.append("🔧 Pipeline Status:")
        for pipeline_name, summary in dashboard_data['pipeline_summaries'].items():
            report.append(f"   {pipeline_name.replace('_', ' ').title()}:")
            report.append(f"     Runs: {summary['total_runs']}")
            report.append(f"     Processed: {summary['total_processed']}")
            report.append(f"     Failed: {summary['total_failed']}")
            if summary['total_runs'] > 0:
                report.append(f"     Error Rate: {summary['avg_error_rate']:.2%}")
                report.append(f"     Processing Rate: {summary['avg_processing_rate']:.2f} items/sec")
        report.append("")
        
        # Alerts
        alert_counts = dashboard_data['alert_counts']
        total_alerts = sum(alert_counts.values())
        report.append(f"🚨 Active Alerts: {total_alerts}")
        if total_alerts > 0:
            report.append(f"   Critical: {alert_counts['critical']}")
            report.append(f"   Error: {alert_counts['error']}")
            report.append(f"   Warning: {alert_counts['warning']}")
            report.append(f"   Info: {alert_counts['info']}")
        
        return "\n".join(report)


# Global monitoring instance
_monitor: Optional[UnifiedMonitor] = None


def get_unified_monitor() -> UnifiedMonitor:
    """Get the global unified monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = UnifiedMonitor()
    return _monitor


def start_monitoring():
    """Start unified monitoring."""
    monitor = get_unified_monitor()
    monitor.start_monitoring()


def stop_monitoring():
    """Stop unified monitoring."""
    monitor = get_unified_monitor()
    monitor.stop_monitoring()


def record_pipeline_metrics(pipeline_name: str, **kwargs):
    """Record pipeline metrics."""
    monitor = get_unified_monitor()
    monitor.record_pipeline_metrics(pipeline_name, **kwargs)


def get_status_report() -> str:
    """Get system status report."""
    monitor = get_unified_monitor()
    return monitor.generate_status_report()


if __name__ == "__main__":
    # Test monitoring system
    monitor = UnifiedMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(60)
            print(monitor.generate_status_report())
            print("\n" + "="*60 + "\n")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("Monitoring stopped")
