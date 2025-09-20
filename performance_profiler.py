"""
Performance profiler for Tunisia Intelligence RSS scraper.

This script provides performance analysis and optimization recommendations
for the RSS scraping system.
"""
import cProfile
import pstats
import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Profiles system performance and provides optimization recommendations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.system_stats = {}
        self.profiler = None
        self.profile_data = None
    
    def start_profiling(self):
        """Start performance profiling."""
        self.start_time = time.time()
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        
        # Collect initial system stats
        self.system_stats['start'] = self._collect_system_stats()
        logger.info("🔍 Performance profiling started")
    
    def stop_profiling(self):
        """Stop performance profiling."""
        if not self.profiler:
            return
        
        self.profiler.disable()
        self.end_time = time.time()
        
        # Collect final system stats
        self.system_stats['end'] = self._collect_system_stats()
        
        # Create stats object
        self.profile_data = pstats.Stats(self.profiler)
        logger.info("🔍 Performance profiling stopped")
    
    def _collect_system_stats(self) -> Dict[str, Any]:
        """Collect system performance statistics."""
        try:
            process = psutil.Process()
            
            return {
                'timestamp': time.time(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available': psutil.virtual_memory().available,
                'memory_used': psutil.virtual_memory().used,
                'disk_usage': psutil.disk_usage('.').percent,
                'process_memory': process.memory_info().rss,
                'process_cpu': process.cpu_percent(),
                'open_files': len(process.open_files()),
                'threads': process.num_threads()
            }
        except Exception as e:
            logger.error(f"Error collecting system stats: {e}")
            return {'timestamp': time.time(), 'error': str(e)}
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.profile_data:
            logger.error("No profiling data available")
            return {}
        
        # Calculate duration
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Analyze top functions
        top_functions = self._analyze_top_functions()
        
        # Analyze system resource usage
        resource_analysis = self._analyze_resource_usage()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(top_functions, resource_analysis)
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration_seconds': duration,
            'top_functions': top_functions,
            'resource_analysis': resource_analysis,
            'recommendations': recommendations,
            'system_stats': self.system_stats
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Performance report saved to: {output_file}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _analyze_top_functions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Analyze top time-consuming functions."""
        if not self.profile_data:
            return []
        
        # Sort by cumulative time
        self.profile_data.sort_stats('cumulative')
        
        # Get stats
        stats = self.profile_data.get_stats()
        
        top_functions = []
        for func, (cc, nc, tt, ct, callers) in list(stats.items())[:limit]:
            filename, line_num, func_name = func
            
            top_functions.append({
                'function': func_name,
                'filename': Path(filename).name if filename else 'unknown',
                'line_number': line_num,
                'call_count': cc,
                'total_time': tt,
                'cumulative_time': ct,
                'time_per_call': tt / cc if cc > 0 else 0,
                'cumulative_per_call': ct / cc if cc > 0 else 0
            })
        
        return top_functions
    
    def _analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyze system resource usage during profiling."""
        if 'start' not in self.system_stats or 'end' not in self.system_stats:
            return {}
        
        start_stats = self.system_stats['start']
        end_stats = self.system_stats['end']
        
        return {
            'memory_delta_mb': (end_stats.get('process_memory', 0) - start_stats.get('process_memory', 0)) / 1024 / 1024,
            'cpu_usage_avg': (start_stats.get('cpu_percent', 0) + end_stats.get('cpu_percent', 0)) / 2,
            'memory_usage_avg': (start_stats.get('memory_percent', 0) + end_stats.get('memory_percent', 0)) / 2,
            'threads_delta': end_stats.get('threads', 0) - start_stats.get('threads', 0),
            'open_files_delta': end_stats.get('open_files', 0) - start_stats.get('open_files', 0),
            'peak_memory_mb': max(start_stats.get('process_memory', 0), end_stats.get('process_memory', 0)) / 1024 / 1024
        }
    
    def _generate_recommendations(self, top_functions: List[Dict], resource_analysis: Dict) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze top functions for bottlenecks
        if top_functions:
            slowest_func = top_functions[0]
            if slowest_func['cumulative_time'] > 10:  # More than 10 seconds
                recommendations.append(
                    f"🐌 Optimize '{slowest_func['function']}' - consuming {slowest_func['cumulative_time']:.2f}s"
                )
            
            # Check for excessive function calls
            for func in top_functions[:5]:
                if func['call_count'] > 10000:
                    recommendations.append(
                        f"🔄 Reduce calls to '{func['function']}' - called {func['call_count']} times"
                    )
        
        # Analyze resource usage
        memory_delta = resource_analysis.get('memory_delta_mb', 0)
        if memory_delta > 100:  # More than 100MB increase
            recommendations.append(
                f"🧠 High memory usage detected - {memory_delta:.1f}MB increase. Consider memory optimization."
            )
        
        cpu_avg = resource_analysis.get('cpu_usage_avg', 0)
        if cpu_avg > 80:
            recommendations.append(
                f"⚡ High CPU usage detected - {cpu_avg:.1f}% average. Consider parallel processing."
            )
        
        threads_delta = resource_analysis.get('threads_delta', 0)
        if threads_delta > 10:
            recommendations.append(
                f"🧵 Thread count increased by {threads_delta}. Monitor for thread leaks."
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Performance looks good! No major bottlenecks detected.")
        
        # Add specific RSS scraper recommendations
        recommendations.extend([
            "💡 Consider implementing connection pooling for database operations",
            "💡 Use async/await for concurrent RSS feed processing",
            "💡 Implement caching for frequently accessed data",
            "💡 Consider batch processing for database insertions"
        ])
        
        return recommendations
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print performance summary to console."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 PERFORMANCE ANALYSIS SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"⏱️ Total Duration: {report['duration_seconds']:.2f} seconds")
        
        # Resource usage
        resource = report.get('resource_analysis', {})
        logger.info(f"🧠 Memory Delta: {resource.get('memory_delta_mb', 0):.1f} MB")
        logger.info(f"⚡ CPU Usage: {resource.get('cpu_usage_avg', 0):.1f}%")
        logger.info(f"📊 Peak Memory: {resource.get('peak_memory_mb', 0):.1f} MB")
        
        # Top functions
        logger.info("\n🔝 TOP TIME-CONSUMING FUNCTIONS:")
        for i, func in enumerate(report.get('top_functions', [])[:5], 1):
            logger.info(f"{i}. {func['function']} - {func['cumulative_time']:.3f}s ({func['call_count']} calls)")
        
        # Recommendations
        logger.info("\n💡 OPTIMIZATION RECOMMENDATIONS:")
        for rec in report.get('recommendations', [])[:5]:
            logger.info(f"   {rec}")
        
        logger.info("=" * 80)
    
    def save_detailed_profile(self, filename: str):
        """Save detailed profiling data to file."""
        if not self.profile_data:
            logger.error("No profiling data available")
            return
        
        # Save as text report
        with open(filename, 'w') as f:
            self.profile_data.print_stats(file=f)
        
        logger.info(f"Detailed profile saved to: {filename}")


def profile_rss_loader():
    """Profile the RSS loader performance."""
    profiler = PerformanceProfiler()
    
    try:
        # Start profiling
        profiler.start_profiling()
        
        # Import and run RSS loader
        from rss_loader import RSSLoader
        loader = RSSLoader()
        
        # Run a limited test (process only first few sources)
        logger.info("Running RSS loader with profiling...")
        loader.run()
        
    except Exception as e:
        logger.error(f"Error during profiling: {e}")
    finally:
        # Stop profiling and generate report
        profiler.stop_profiling()
        
        # Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_report_{timestamp}.json"
        profile_file = f"detailed_profile_{timestamp}.txt"
        
        profiler.generate_report(report_file)
        profiler.save_detailed_profile(profile_file)


def profile_single_extractor(url: str):
    """Profile a single extractor performance."""
    profiler = PerformanceProfiler()
    
    try:
        profiler.start_profiling()
        
        # Import and test single extractor
        from extractors.unified_extractor import UnifiedExtractor
        extractor = UnifiedExtractor()
        
        logger.info(f"Profiling extractor for: {url}")
        results = extractor.extract(url)
        logger.info(f"Extracted {len(results)} articles")
        
    except Exception as e:
        logger.error(f"Error during extractor profiling: {e}")
    finally:
        profiler.stop_profiling()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"extractor_profile_{timestamp}.json"
        
        profiler.generate_report(report_file)


def main():
    """Main profiling function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Profiler for Tunisia Intelligence RSS Scraper")
    parser.add_argument("--mode", choices=["full", "extractor"], default="full",
                       help="Profiling mode: full system or single extractor")
    parser.add_argument("--url", help="URL for single extractor profiling")
    
    args = parser.parse_args()
    
    if args.mode == "extractor":
        if not args.url:
            parser.error("--url is required for extractor profiling")
        profile_single_extractor(args.url)
    else:
        profile_rss_loader()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
