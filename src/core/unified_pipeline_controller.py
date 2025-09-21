#!/usr/bin/env python3
"""
Unified Pipeline Controller for Tunisia Intelligence System

This controller orchestrates all processing pipelines:
- RSS Extraction and Loading
- Facebook Extraction and Loading
- AI Enrichment Processing
- Vectorization Processing

Features:
- Centralized control and coordination
- Rate limiting and resource management
- Pipeline scheduling and sequencing
- Comprehensive monitoring and logging
- Error handling and recovery
- Status reporting and metrics
"""

import asyncio
import logging
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
import json
from pathlib import Path
import psutil
import signal

# Import configuration
from config.unified_control import (
    get_unified_control, PipelineMode, ProcessingPriority,
    get_rss_control, get_facebook_control, get_ai_enrichment_control,
    get_vectorization_control, get_monitoring_control, get_scheduling_control
)
from config.database import DatabaseManager

# Pipeline modules will be imported dynamically when needed
# This avoids import issues and lets each pipeline handle its own dependencies

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class PipelineMetrics:
    """Metrics for pipeline execution."""
    pipeline_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.IDLE
    items_processed: int = 0
    items_failed: int = 0
    items_skipped: int = 0
    processing_rate: float = 0.0  # items per second
    error_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.items_processed + self.items_failed
        if total > 0:
            return self.items_processed / total
        return 0.0


class ResourceMonitor:
    """Monitor system resources during pipeline execution."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.metrics_history = []
    
    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Resource monitoring loop."""
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                cpu_percent = self.process.cpu_percent()
                
                metrics = {
                    'timestamp': datetime.now(),
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'num_threads': self.process.num_threads()
                }
                
                self.metrics_history.append(metrics)
                
                # Keep only last 100 measurements
                if len(self.metrics_history) > 100:
                    self.metrics_history.pop(0)
                
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
            
            time.sleep(5)  # Monitor every 5 seconds
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current resource metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return {'memory_mb': 0.0, 'cpu_percent': 0.0, 'num_threads': 0}


class RateLimiter:
    """Rate limiting for pipeline operations."""
    
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
        self.lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed based on rate limits."""
        with self.lock:
            now = datetime.now()
            
            # Clean old requests
            self.minute_requests = [req for req in self.minute_requests 
                                  if now - req < timedelta(minutes=1)]
            self.hour_requests = [req for req in self.hour_requests 
                                if now - req < timedelta(hours=1)]
            
            # Check limits
            if len(self.minute_requests) >= self.requests_per_minute:
                return False
            if len(self.hour_requests) >= self.requests_per_hour:
                return False
            
            return True
    
    def record_request(self):
        """Record a request for rate limiting."""
        with self.lock:
            now = datetime.now()
            self.minute_requests.append(now)
            self.hour_requests.append(now)
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded."""
        while not self.can_proceed():
            time.sleep(1)
        self.record_request()


class PipelineExecutor:
    """Execute individual pipelines with monitoring and control."""
    
    def __init__(self, pipeline_name: str, control_settings):
        self.pipeline_name = pipeline_name
        self.control_settings = control_settings
        self.metrics = PipelineMetrics(pipeline_name)
        self.rate_limiter = None
        self.cancelled = False
        
        # Initialize rate limiter based on pipeline type
        if hasattr(control_settings, 'requests_per_minute'):
            self.rate_limiter = RateLimiter(
                control_settings.requests_per_minute,
                getattr(control_settings, 'requests_per_hour', control_settings.requests_per_minute * 60)
            )
    
    def execute(self, **kwargs) -> PipelineMetrics:
        """Execute the pipeline with monitoring."""
        self.metrics.start_time = datetime.now()
        self.metrics.status = PipelineStatus.RUNNING
        
        try:
            logger.info(f"ðŸš€ Starting {self.pipeline_name} pipeline")
            
            if self.pipeline_name == 'rss':
                self._execute_rss_pipeline(**kwargs)
            elif self.pipeline_name == 'facebook':
                self._execute_facebook_pipeline(**kwargs)
            elif self.pipeline_name == 'ai_enrichment':
                self._execute_ai_enrichment_pipeline(**kwargs)
            elif self.pipeline_name == 'vectorization':
                self._execute_vectorization_pipeline(**kwargs)
            else:
                raise ValueError(f"Unknown pipeline: {self.pipeline_name}")
            
            self.metrics.status = PipelineStatus.COMPLETED
            logger.info(f"âœ… Completed {self.pipeline_name} pipeline")
            
        except Exception as e:
            self.metrics.status = PipelineStatus.FAILED
            self.metrics.errors.append(str(e))
            logger.error(f"âŒ Failed {self.pipeline_name} pipeline: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            self.metrics.end_time = datetime.now()
            self._calculate_final_metrics()
        
        return self.metrics
    
    def _execute_rss_pipeline(self, **kwargs):
        """Execute RSS extraction and loading using existing RSS loader."""
        try:
            # Use the existing RSS loader main function
            from src.data_collection.rss_loader import src.core.main as rss_main
            logger.info("Starting RSS pipeline...")
            result = rss_main()
            
            # Extract metrics from result if available
            if isinstance(result, dict):
                self.metrics.items_processed += result.get('articles_processed', 0)
                if result.get('errors'):
                    self.metrics.errors.extend(result['errors'])
            else:
                # If no detailed result, assume some processing happened
                self.metrics.items_processed += 1
                
        except Exception as e:
            self.metrics.items_failed += 1
            self.metrics.errors.append(f"RSS pipeline error: {str(e)}")
            logger.error(f"RSS pipeline failed: {e}")
    
    def _execute_facebook_pipeline(self, **kwargs):
        """Execute Facebook extraction and loading using existing Facebook loader."""
        try:
            # Display Facebook configuration parameters
            self._display_facebook_configuration()
            
            # Use the existing Facebook loader main function
            from src.data_collection.facebook_loader import src.core.main as facebook_main
            logger.info("Starting Facebook pipeline...")
            result = facebook_main()
            
            # Extract metrics from result if available
            if isinstance(result, dict):
                # Use correct key names from Facebook loader result
                posts_loaded = result.get('total_posts_loaded', 0)
                self.metrics.items_processed += posts_loaded
                
                # Log detailed Facebook metrics
                logger.info(f"Facebook pipeline completed:")
                logger.info(f"  - Status: {result.get('status', 'unknown')}")
                logger.info(f"  - Sources processed: {result.get('sources_processed', 0)}")
                logger.info(f"  - Posts loaded: {posts_loaded}")
                logger.info(f"  - API calls made: {result.get('api_calls_made', 0)}")
                logger.info(f"  - Efficiency: {result.get('efficiency', 0):.1f} calls/source")
                
                if result.get('errors'):
                    self.metrics.errors.extend(result['errors'])
            else:
                # If no detailed result, assume some processing happened
                self.metrics.items_processed += 1
                
        except Exception as e:
            self.metrics.items_failed += 1
            self.metrics.errors.append(f"Facebook pipeline error: {str(e)}")
            logger.error(f"Facebook pipeline failed: {e}")
    
    def _execute_ai_enrichment_pipeline(self, **kwargs):
        """Execute AI enrichment processing using existing enrichment system."""
        try:
            # Use the existing AI enrichment main function
            from simple_batch_enrich import src.core.main as ai_main
            logger.info("Starting AI enrichment pipeline...")
            result = ai_main()
            
            # Extract metrics from result if available
            if isinstance(result, dict):
                self.metrics.items_processed += result.get('items_processed', 0)
                self.metrics.items_failed += result.get('items_failed', 0)
                if result.get('errors'):
                    self.metrics.errors.extend(result['errors'])
            else:
                # If no detailed result, assume some processing happened
                self.metrics.items_processed += 1
                
        except Exception as e:
            self.metrics.items_failed += 1
            self.metrics.errors.append(f"AI enrichment pipeline error: {str(e)}")
            logger.error(f"AI enrichment pipeline failed: {e}")
    
    def _execute_vectorization_pipeline(self, **kwargs):
        """Execute vectorization processing using existing vectorization system."""
        try:
            # Use the existing vectorization main function
            from batch_vectorize_articles import src.core.main as vectorization_main
            logger.info("Starting vectorization pipeline...")
            result = vectorization_main()
            
            # Extract metrics from result if available
            if isinstance(result, dict):
                self.metrics.items_processed += result.get('items_processed', 0)
                if result.get('errors'):
                    self.metrics.errors.extend(result['errors'])
            else:
                # If no detailed result, assume some processing happened
                self.metrics.items_processed += 1
                
        except Exception as e:
            self.metrics.items_failed += 1
            self.metrics.errors.append(f"Vectorization pipeline error: {str(e)}")
            logger.error(f"Vectorization pipeline failed: {e}")
    
    def _calculate_final_metrics(self):
        """Calculate final metrics after execution."""
        if self.metrics.duration_seconds > 0:
            self.metrics.processing_rate = self.metrics.items_processed / self.metrics.duration_seconds
        
        total_items = self.metrics.items_processed + self.metrics.items_failed
        if total_items > 0:
            self.metrics.error_rate = self.metrics.items_failed / total_items
    
    def cancel(self):
        """Cancel pipeline execution."""
        self.cancelled = True
        self.metrics.status = PipelineStatus.CANCELLED
    
    def _display_facebook_configuration(self):
        """Display Facebook configuration parameters in terminal."""
        try:
            from config.facebook_config import get_facebook_config
            
            logger.info("ðŸ“‹ Facebook Pipeline Configuration:")
            logger.info("=" * 50)
            
            # Get current Facebook configuration
            config = get_facebook_config()
            
            # Display extraction settings
            logger.info("ðŸ”§ Extraction Settings:")
            logger.info(f"  â€¢ Max pages per run: {config.extraction.max_pages_per_run}")
            logger.info(f"  â€¢ Max API calls per run: {config.extraction.max_api_calls_per_run}")
            logger.info(f"  â€¢ Min API delay: {config.extraction.min_api_delay}s")
            logger.info(f"  â€¢ API version: {config.extraction.api_version}")
            logger.info(f"  â€¢ Hours back: {config.extraction.hours_back}")
            
            # Display content filtering
            logger.info("ðŸŽ¯ Content Filtering:")
            logger.info(f"  â€¢ Min content length: {config.content_filtering.min_content_length}")
            logger.info(f"  â€¢ Max content length: {config.content_filtering.max_content_length}")
            logger.info(f"  â€¢ Skip empty posts: {config.content_filtering.skip_empty_posts}")
            logger.info(f"  â€¢ Skip link-only posts: {config.content_filtering.skip_link_only_posts}")
            
            # Display rate limiting
            logger.info("â±ï¸ Rate Limiting:")
            logger.info(f"  â€¢ Requests per minute: {config.rate_limiting.requests_per_minute}")
            logger.info(f"  â€¢ Requests per hour: {config.rate_limiting.requests_per_hour}")
            logger.info(f"  â€¢ Burst limit: {config.rate_limiting.burst_limit}")
            logger.info(f"  â€¢ Cooldown period: {config.rate_limiting.cooldown_period_minutes}min")
            
            # Display processing settings
            logger.info("âš™ï¸ Processing Settings:")
            logger.info(f"  â€¢ Batch size: {config.processing.batch_size}")
            logger.info(f"  â€¢ Max retries: {config.processing.max_retries}")
            logger.info(f"  â€¢ Retry delay: {config.processing.retry_delay_seconds}s")
            logger.info(f"  â€¢ Timeout: {config.processing.timeout_seconds}s")
            logger.info(f"  â€¢ Enable duplicate detection: {config.processing.enable_duplicate_detection}")
            
            # Display monitoring settings
            logger.info("ðŸ“Š Monitoring Settings:")
            logger.info(f"  â€¢ Log level: {config.monitoring.log_level}")
            logger.info(f"  â€¢ Enable metrics: {config.monitoring.enable_metrics}")
            logger.info(f"  â€¢ Metrics interval: {config.monitoring.metrics_interval_seconds}s")
            logger.info(f"  â€¢ Enable alerts: {config.monitoring.enable_alerts}")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"âŒ Error displaying Facebook configuration: {e}")


class UnifiedPipelineController:
    """Main controller for all Tunisia Intelligence pipelines."""
    
    def __init__(self):
        self.control_settings = get_unified_control()
        self.resource_monitor = ResourceMonitor()
        self.pipeline_metrics = {}
        self.running = False
        self.paused = False
        self.current_cycle = 0
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("ðŸŽ›ï¸ Unified Pipeline Controller initialized")
    
    def _setup_logging(self):
        """Setup comprehensive logging."""
        log_level = logging.DEBUG if self.control_settings.debug else logging.INFO
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(logs_dir / "unified_controller.log", encoding='utf-8'),
                logging.FileHandler(logs_dir / f"controller_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the unified pipeline controller."""
        if not self.control_settings.master_enabled:
            logger.warning("Master control is disabled, not starting")
            return
        
        if self.control_settings.maintenance_mode:
            logger.warning("System is in maintenance mode, not starting")
            return
        
        self.running = True
        self.resource_monitor.start_monitoring()
        
        logger.info("ðŸš€ Starting Tunisia Intelligence Unified Pipeline Controller")
        logger.info(f"Environment: {self.control_settings.environment}")
        logger.info(f"Debug mode: {self.control_settings.debug}")
        
        try:
            if self.control_settings.scheduling.coordination_mode == "sequential":
                self._run_sequential_mode()
            else:
                self._run_parallel_mode()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Controller error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.stop()
    
    def _run_sequential_mode(self):
        """Run pipelines in sequential mode."""
        logger.info("Running in sequential coordination mode")
        
        while self.running:
            if self.paused:
                time.sleep(10)
                continue
            
            try:
                self.current_cycle += 1
                logger.info(f"ðŸ”„ Starting processing cycle {self.current_cycle}")
                
                # Get processing order
                pipeline_order = self.control_settings.get_processing_order()
                logger.info(f"Pipeline order: {' â†’ '.join(pipeline_order)}")
                
                cycle_start = datetime.now()
                cycle_metrics = {}
                
                # Execute pipelines in order
                for pipeline_name in pipeline_order:
                    if not self.running or self.paused:
                        break
                    
                    if self.control_settings.is_pipeline_enabled(pipeline_name):
                        metrics = self._execute_pipeline(pipeline_name)
                        cycle_metrics[pipeline_name] = metrics
                        
                        # Delay between pipelines
                        if self.control_settings.scheduling.pipeline_delay_minutes > 0:
                            delay_seconds = self.control_settings.scheduling.pipeline_delay_minutes * 60
                            logger.info(f"â³ Waiting {delay_seconds}s before next pipeline")
                            time.sleep(delay_seconds)
                
                # Report cycle completion
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                self._report_cycle_completion(self.current_cycle, cycle_duration, cycle_metrics)
                
                # Wait for next cycle
                if self.running:
                    interval_seconds = self.control_settings.scheduling.full_cycle_interval_hours * 3600
                    logger.info(f"â³ Waiting {interval_seconds}s for next cycle")
                    time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Cycle {self.current_cycle} error: {e}")
                logger.error(traceback.format_exc())
                time.sleep(60)  # Wait before retrying
    
    def _run_parallel_mode(self):
        """Run pipelines in parallel mode."""
        logger.info("Running in parallel coordination mode")
        # TODO: Implement parallel execution with proper coordination
        logger.warning("Parallel mode not yet implemented, falling back to sequential")
        self._run_sequential_mode()
    
    def _execute_pipeline(self, pipeline_name: str) -> PipelineMetrics:
        """Execute a specific pipeline."""
        logger.info(f"ðŸ”§ Executing {pipeline_name} pipeline")
        
        # Get pipeline-specific settings
        control_settings = getattr(self.control_settings, pipeline_name)
        
        # Create and execute pipeline
        executor = PipelineExecutor(pipeline_name, control_settings)
        metrics = executor.execute()
        
        # Store metrics
        self.pipeline_metrics[pipeline_name] = metrics
        
        # Log results
        self._log_pipeline_results(metrics)
        
        return metrics
    
    def _log_pipeline_results(self, metrics: PipelineMetrics):
        """Log pipeline execution results."""
        status_text = {
            PipelineStatus.COMPLETED: "âœ…",
            PipelineStatus.FAILED: "âŒ", 
            PipelineStatus.RUNNING: "ðŸ”„",
            PipelineStatus.IDLE: "â¸ï¸"
        }
        
        status_prefix = status_text.get(metrics.status, "INFO")
        
        logger.info(f"{status_prefix} {metrics.pipeline_name} Pipeline Results:")
        logger.info(f"   Status: {metrics.status.value}")
        logger.info(f"   Duration: {metrics.duration_seconds:.1f}s")
        logger.info(f"   Items Processed: {metrics.items_processed}")
        logger.info(f"   Items Failed: {metrics.items_failed}")
        logger.info(f"   Success Rate: {metrics.success_rate:.2%}")
        
        if metrics.processing_rate > 0:
            logger.info(f"   Processing Rate: {metrics.processing_rate:.2f} items/sec")
        
        if metrics.errors:
            logger.warning(f"   Errors: {len(metrics.errors)}")
            for error in metrics.errors[:3]:  # Show first 3 errors
                logger.warning(f"     - {error}")
    
    def _report_cycle_completion(self, cycle_num: int, duration: float, cycle_metrics: Dict[str, PipelineMetrics]):
        """Report completion of a full processing cycle."""
        logger.info(f"ðŸŽ¯ Cycle {cycle_num} completed in {duration:.1f}s")
        
        total_processed = sum(m.items_processed for m in cycle_metrics.values())
        total_failed = sum(m.items_failed for m in cycle_metrics.values())
        
        logger.info(f"   Total Items Processed: {total_processed}")
        logger.info(f"   Total Items Failed: {total_failed}")
        
        if total_processed + total_failed > 0:
            success_rate = total_processed / (total_processed + total_failed)
            logger.info(f"   Overall Success Rate: {success_rate:.2%}")
        
        # Resource usage
        resource_metrics = self.resource_monitor.get_current_metrics()
        logger.info(f"   Memory Usage: {resource_metrics.get('memory_mb', 0):.1f} MB")
        logger.info(f"   CPU Usage: {resource_metrics.get('cpu_percent', 0):.1f}%")
    
    def pause(self):
        """Pause pipeline execution."""
        self.paused = True
        logger.info("â¸ï¸ Pipeline controller paused")
    
    def resume(self):
        """Resume pipeline execution."""
        self.paused = False
        logger.info("â–¶ï¸ Pipeline controller resumed")
    
    def stop(self):
        """Stop the pipeline controller."""
        self.running = False
        self.resource_monitor.stop_monitoring()
        logger.info("ðŸ›‘ Pipeline controller stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            'running': self.running,
            'paused': self.paused,
            'current_cycle': self.current_cycle,
            'master_enabled': self.control_settings.master_enabled,
            'maintenance_mode': self.control_settings.maintenance_mode,
            'pipeline_metrics': {name: {
                'status': metrics.status.value,
                'items_processed': metrics.items_processed,
                'items_failed': metrics.items_failed,
                'success_rate': metrics.success_rate,
                'duration_seconds': metrics.duration_seconds
            } for name, metrics in self.pipeline_metrics.items()},
            'resource_metrics': self.resource_monitor.get_current_metrics()
        }
    
    def execute_single_pipeline(self, pipeline_name: str) -> PipelineMetrics:
        """Execute a single pipeline manually."""
        if not self.control_settings.is_pipeline_enabled(pipeline_name):
            raise ValueError(f"Pipeline {pipeline_name} is not enabled")
        
        logger.info(f"ðŸŽ¯ Manual execution of {pipeline_name} pipeline")
        return self._execute_pipeline(pipeline_name)


def main():
    """Main entry point for the unified controller."""
    controller = UnifiedPipelineController()
    
    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Controller startup error: {e}")
        logger.error(traceback.format_exc())
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
