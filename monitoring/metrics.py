"""
Monitoring and metrics system for Tunisia Intelligence RSS scraper.

This module provides comprehensive monitoring capabilities including
metrics collection, performance tracking, and alerting.
"""
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class ScrapingMetrics:
    """Metrics for a single scraping session."""
    
    # Session info
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Source metrics
    total_sources: int = 0
    sources_processed: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    
    # Article metrics
    total_articles_found: int = 0
    articles_processed: int = 0
    articles_saved: int = 0
    articles_skipped: int = 0
    articles_duplicate: int = 0
    
    # Error metrics
    total_errors: int = 0
    timeout_errors: int = 0
    network_errors: int = 0
    parsing_errors: int = 0
    database_errors: int = 0
    
    # Performance metrics
    avg_processing_time_per_source: float = 0.0
    avg_articles_per_source: float = 0.0
    throughput_articles_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics from base metrics."""
        if self.end_time and self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if self.sources_processed > 0:
            self.avg_processing_time_per_source = self.duration_seconds / self.sources_processed
            self.avg_articles_per_source = self.articles_processed / self.sources_processed
        
        if self.duration_seconds > 0:
            self.throughput_articles_per_second = self.articles_processed / self.duration_seconds


@dataclass
class SourceMetrics:
    """Metrics for a single source."""
    
    source_id: int
    source_name: str
    source_url: str
    
    # Processing info
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: str = "processing"  # processing, success, failed
    
    # Article metrics
    articles_found: int = 0
    articles_processed: int = 0
    articles_saved: int = 0
    articles_skipped: int = 0
    
    # Error info
    error_count: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


class MetricsCollector:
    """Collects and manages metrics for the RSS scraper."""
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.current_session: Optional[ScrapingMetrics] = None
        self.source_metrics: Dict[int, SourceMetrics] = {}
        self.session_history: deque = deque(maxlen=1000)  # Keep last 1000 sessions
        self.performance_history: deque = deque(maxlen=10000)  # Keep performance samples
        self._lock = threading.Lock()
        
        # Real-time metrics
        self.real_time_stats = {
            'articles_per_minute': deque(maxlen=60),  # Last 60 minutes
            'errors_per_minute': deque(maxlen=60),
            'sources_per_minute': deque(maxlen=60)
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'error_rate_threshold': 0.1,  # 10% error rate
            'timeout_threshold': 300,  # 5 minutes
            'min_articles_threshold': 10  # Minimum articles per session
        }
    
    def start_session(self, session_id: str) -> ScrapingMetrics:
        """Start a new scraping session."""
        with self._lock:
            self.current_session = ScrapingMetrics(
                session_id=session_id,
                start_time=datetime.now(timezone.utc)
            )
            logger.info(f"Started metrics collection for session: {session_id}")
            return self.current_session
    
    def end_session(self) -> Optional[ScrapingMetrics]:
        """End the current scraping session."""
        with self._lock:
            if not self.current_session:
                return None
            
            self.current_session.end_time = datetime.now(timezone.utc)
            self.current_session.calculate_derived_metrics()
            
            # Add to history
            self.session_history.append(self.current_session.to_dict())
            
            # Log session summary
            self._log_session_summary(self.current_session)
            
            # Check for alerts
            self._check_alerts(self.current_session)
            
            session = self.current_session
            self.current_session = None
            return session
    
    def start_source_processing(self, source_id: int, source_name: str, source_url: str) -> SourceMetrics:
        """Start processing a source."""
        with self._lock:
            source_metrics = SourceMetrics(
                source_id=source_id,
                source_name=source_name,
                source_url=source_url,
                start_time=datetime.now(timezone.utc)
            )
            self.source_metrics[source_id] = source_metrics
            
            # Update session metrics
            if self.current_session:
                self.current_session.total_sources += 1
            
            return source_metrics
    
    def end_source_processing(self, source_id: int, status: str = "success", 
                            error_message: Optional[str] = None):
        """End processing a source."""
        with self._lock:
            if source_id not in self.source_metrics:
                return
            
            source_metrics = self.source_metrics[source_id]
            source_metrics.end_time = datetime.now(timezone.utc)
            source_metrics.status = status
            source_metrics.error_message = error_message
            
            if source_metrics.end_time and source_metrics.start_time:
                source_metrics.duration_seconds = (
                    source_metrics.end_time - source_metrics.start_time
                ).total_seconds()
            
            # Update session metrics
            if self.current_session:
                self.current_session.sources_processed += 1
                if status == "success":
                    self.current_session.sources_successful += 1
                else:
                    self.current_session.sources_failed += 1
                    self.current_session.total_errors += 1
    
    def record_articles_found(self, source_id: int, count: int):
        """Record number of articles found for a source."""
        with self._lock:
            if source_id in self.source_metrics:
                self.source_metrics[source_id].articles_found = count
            
            if self.current_session:
                self.current_session.total_articles_found += count
    
    def record_article_processed(self, source_id: int, saved: bool = True, skipped: bool = False):
        """Record that an article was processed."""
        with self._lock:
            if source_id in self.source_metrics:
                self.source_metrics[source_id].articles_processed += 1
                if saved:
                    self.source_metrics[source_id].articles_saved += 1
                elif skipped:
                    self.source_metrics[source_id].articles_skipped += 1
            
            if self.current_session:
                self.current_session.articles_processed += 1
                if saved:
                    self.current_session.articles_saved += 1
                elif skipped:
                    self.current_session.articles_skipped += 1
    
    def record_duplicate_article(self, source_id: int):
        """Record a duplicate article."""
        with self._lock:
            if self.current_session:
                self.current_session.articles_duplicate += 1
    
    def record_error(self, source_id: int, error_type: str, error_message: str):
        """Record an error."""
        with self._lock:
            if source_id in self.source_metrics:
                self.source_metrics[source_id].error_count += 1
            
            if self.current_session:
                self.current_session.total_errors += 1
                
                # Categorize errors
                if "timeout" in error_message.lower():
                    self.current_session.timeout_errors += 1
                elif "network" in error_message.lower() or "connection" in error_message.lower():
                    self.current_session.network_errors += 1
                elif "parse" in error_message.lower():
                    self.current_session.parsing_errors += 1
                elif "database" in error_message.lower():
                    self.current_session.database_errors += 1
    
    def record_retry(self, source_id: int):
        """Record a retry attempt."""
        with self._lock:
            if source_id in self.source_metrics:
                self.source_metrics[source_id].retry_count += 1
    
    def get_current_session_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current session metrics."""
        with self._lock:
            if self.current_session:
                return self.current_session.to_dict()
            return None
    
    def get_source_metrics(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific source."""
        with self._lock:
            if source_id in self.source_metrics:
                return self.source_metrics[source_id].to_dict()
            return None
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent session history."""
        with self._lock:
            return list(self.session_history)[-limit:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        with self._lock:
            if not self.session_history:
                return {}
            
            recent_sessions = list(self.session_history)[-10:]  # Last 10 sessions
            
            total_articles = sum(s.get('articles_processed', 0) for s in recent_sessions)
            total_duration = sum(s.get('duration_seconds', 0) for s in recent_sessions)
            total_errors = sum(s.get('total_errors', 0) for s in recent_sessions)
            total_sources = sum(s.get('sources_processed', 0) for s in recent_sessions)
            
            return {
                'sessions_analyzed': len(recent_sessions),
                'avg_articles_per_session': total_articles / len(recent_sessions) if recent_sessions else 0,
                'avg_duration_per_session': total_duration / len(recent_sessions) if recent_sessions else 0,
                'avg_throughput': total_articles / total_duration if total_duration > 0 else 0,
                'error_rate': total_errors / total_sources if total_sources > 0 else 0,
                'total_articles_processed': total_articles,
                'total_errors': total_errors
            }
    
    def _log_session_summary(self, session: ScrapingMetrics):
        """Log a summary of the session."""
        logger.info("=" * 80)
        logger.info(f"SESSION SUMMARY - {session.session_id}")
        logger.info("=" * 80)
        logger.info(f"Duration: {session.duration_seconds:.2f} seconds")
        logger.info(f"Sources: {session.sources_processed} processed, "
                   f"{session.sources_successful} successful, {session.sources_failed} failed")
        logger.info(f"Articles: {session.articles_processed} processed, "
                   f"{session.articles_saved} saved, {session.articles_skipped} skipped")
        logger.info(f"Duplicates: {session.articles_duplicate}")
        logger.info(f"Errors: {session.total_errors} total")
        logger.info(f"Performance: {session.throughput_articles_per_second:.2f} articles/second")
        logger.info("=" * 80)
    
    def _check_alerts(self, session: ScrapingMetrics):
        """Check if any alert conditions are met."""
        alerts = []
        
        # High error rate
        if session.sources_processed > 0:
            error_rate = session.sources_failed / session.sources_processed
            if error_rate > self.alert_thresholds['error_rate_threshold']:
                alerts.append(f"High error rate: {error_rate:.2%}")
        
        # Long processing time
        if session.duration_seconds > self.alert_thresholds['timeout_threshold']:
            alerts.append(f"Long processing time: {session.duration_seconds:.2f}s")
        
        # Low article count
        if session.articles_processed < self.alert_thresholds['min_articles_threshold']:
            alerts.append(f"Low article count: {session.articles_processed}")
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"ALERT: {alert}")
    
    def export_metrics(self, file_path: str):
        """Export metrics to a JSON file."""
        with self._lock:
            data = {
                'current_session': self.current_session.to_dict() if self.current_session else None,
                'source_metrics': {k: v.to_dict() for k, v in self.source_metrics.items()},
                'session_history': list(self.session_history),
                'performance_summary': self.get_performance_summary(),
                'export_time': datetime.now(timezone.utc).isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to: {file_path}")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        from config.settings import get_settings
        settings = get_settings()
        _metrics_collector = MetricsCollector(
            retention_days=settings.monitoring.metrics_retention_days
        )
    return _metrics_collector


def start_session(session_id: str) -> ScrapingMetrics:
    """Convenience function to start a metrics session."""
    return get_metrics_collector().start_session(session_id)


def end_session() -> Optional[ScrapingMetrics]:
    """Convenience function to end a metrics session."""
    return get_metrics_collector().end_session()


def record_source_start(source_id: int, source_name: str, source_url: str) -> SourceMetrics:
    """Convenience function to start source processing."""
    return get_metrics_collector().start_source_processing(source_id, source_name, source_url)


def record_source_end(source_id: int, status: str = "success", error_message: Optional[str] = None):
    """Convenience function to end source processing."""
    get_metrics_collector().end_source_processing(source_id, status, error_message)
