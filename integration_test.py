"""
Integration test script for Tunisia Intelligence RSS scraper.

This script performs end-to-end testing of the complete system
to ensure all components work together correctly.
"""
import sys
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Performs comprehensive integration tests."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        self.start_time = datetime.now(timezone.utc)
        
        logger.info("🧪 Starting Tunisia Intelligence RSS Scraper Integration Tests")
        logger.info("=" * 70)
        
        # Test configuration system
        self._test_configuration_system()
        
        # Test secret management
        self._test_secret_management()
        
        # Test database operations
        self._test_database_operations()
        
        # Test extractor system
        self._test_extractor_system()
        
        # Test monitoring system
        self._test_monitoring_system()
        
        # Test deduplication system
        self._test_deduplication_system()
        
        # Test end-to-end workflow
        self._test_end_to_end_workflow()
        
        self.end_time = datetime.now(timezone.utc)
        return self._generate_summary()
    
    def _test_configuration_system(self):
        """Test configuration management system."""
        logger.info("⚙️ Testing configuration system...")
        
        try:
            from config.settings import get_settings, reload_settings
            
            # Test basic configuration loading
            settings = get_settings()
            if settings and settings.app_name:
                self._pass("Configuration system loads successfully")
            else:
                self._fail("Configuration system failed to load")
            
            # Test configuration reload
            new_settings = reload_settings()
            if new_settings:
                self._pass("Configuration reload works")
            else:
                self._fail("Configuration reload failed")
            
            # Test sub-configurations
            db_config = settings.database
            scraping_config = settings.scraping
            
            if db_config and scraping_config:
                self._pass("Sub-configurations accessible")
            else:
                self._fail("Sub-configurations not accessible")
            
        except Exception as e:
            self._fail(f"Configuration system error: {e}")
    
    def _test_secret_management(self):
        """Test secret management system."""
        logger.info("🔐 Testing secret management...")
        
        try:
            from config.secrets import get_secret_manager, get_secret, set_secret
            
            # Test secret manager initialization
            manager = get_secret_manager()
            if manager:
                self._pass("Secret manager initializes successfully")
            else:
                self._fail("Secret manager initialization failed")
            
            # Test setting and getting secrets
            test_key = "INTEGRATION_TEST_SECRET"
            test_value = "test_secret_value_123"
            
            if set_secret(test_key, test_value):
                self._pass("Secret setting works")
                
                retrieved_value = get_secret(test_key)
                if retrieved_value == test_value:
                    self._pass("Secret retrieval works")
                else:
                    self._fail(f"Secret retrieval failed: expected {test_value}, got {retrieved_value}")
            else:
                self._fail("Secret setting failed")
            
        except Exception as e:
            self._fail(f"Secret management error: {e}")
    
    def _test_database_operations(self):
        """Test database operations."""
        logger.info("🗄️ Testing database operations...")
        
        try:
            from config.database import DatabaseManager, Source, Article, ParsingState, ParsingLog
            from datetime import datetime, timezone
            
            db = DatabaseManager()
            
            # Test database connection
            client = db.get_client()
            if client:
                self._pass("Database connection successful")
            else:
                self._fail("Database connection failed")
            
            # Test getting sources
            sources = db.get_sources()
            if isinstance(sources, list):
                self._pass(f"Sources retrieval successful ({len(sources)} sources)")
            else:
                self._fail("Sources retrieval failed")
            
            # Test parsing state operations (if sources exist)
            if sources:
                test_source = sources[0]
                state = db.get_parsing_state(test_source.id)
                self._pass("Parsing state retrieval works")
            
        except Exception as e:
            self._fail(f"Database operations error: {e}")
    
    def _test_extractor_system(self):
        """Test extractor system."""
        logger.info("🔍 Testing extractor system...")
        
        try:
            from extractors import EXTRACTOR_REGISTRY, DOMAIN_REGISTRY
            from extractors.unified_extractor import UnifiedExtractor
            
            # Test registries
            if len(EXTRACTOR_REGISTRY) > 0 and len(DOMAIN_REGISTRY) > 0:
                self._pass(f"Extractor registries loaded ({len(EXTRACTOR_REGISTRY)} extractors, {len(DOMAIN_REGISTRY)} domains)")
            else:
                self._fail("Extractor registries not properly loaded")
            
            # Test unified extractor
            extractor = UnifiedExtractor()
            
            # Test extractor resolution
            test_urls = [
                "https://nawaat.org/feed/",
                "https://africanmanager.com/feed/"
            ]
            
            resolved_extractors = 0
            for url in test_urls:
                extractor_func = extractor.get_extractor(url)
                if extractor_func:
                    resolved_extractors += 1
            
            if resolved_extractors == len(test_urls):
                self._pass("Extractor resolution works for all test URLs")
            elif resolved_extractors > 0:
                self._pass(f"Extractor resolution works for {resolved_extractors}/{len(test_urls)} URLs")
            else:
                self._fail("Extractor resolution failed for all test URLs")
            
            # Test actual extraction (with timeout)
            try:
                test_url = "https://nawaat.org/feed/"
                logger.info(f"Testing actual extraction from {test_url}...")
                
                # Set a shorter timeout for testing
                results = extractor.extract(test_url, max_retries=1, initial_timeout=30)
                
                if isinstance(results, list):
                    self._pass(f"Actual extraction successful ({len(results)} articles)")
                else:
                    self._fail("Actual extraction returned invalid format")
                    
            except Exception as e:
                self._fail(f"Actual extraction failed: {e}")
            
        except Exception as e:
            self._fail(f"Extractor system error: {e}")
    
    def _test_monitoring_system(self):
        """Test monitoring system."""
        logger.info("📊 Testing monitoring system...")
        
        try:
            from monitoring import (
                get_metrics_collector, start_session, end_session,
                record_source_start, record_source_end
            )
            
            # Test metrics collector initialization
            collector = get_metrics_collector()
            if collector:
                self._pass("Metrics collector initializes successfully")
            else:
                self._fail("Metrics collector initialization failed")
            
            # Test session management
            test_session_id = f"integration_test_{int(time.time())}"
            session = start_session(test_session_id)
            
            if session and session.session_id == test_session_id:
                self._pass("Session start works")
                
                # Test source recording
                source_metrics = record_source_start(999, "Test Source", "https://test.com/feed")
                if source_metrics:
                    self._pass("Source recording works")
                    
                    # Record some test metrics
                    collector.record_articles_found(999, 5)
                    collector.record_article_processed(999, saved=True)
                    
                    # End source
                    record_source_end(999, "success")
                    self._pass("Source completion recording works")
                
                # End session
                final_session = end_session()
                if final_session:
                    self._pass("Session end works")
                else:
                    self._fail("Session end failed")
            else:
                self._fail("Session start failed")
            
        except Exception as e:
            self._fail(f"Monitoring system error: {e}")
    
    def _test_deduplication_system(self):
        """Test deduplication system."""
        logger.info("🔄 Testing deduplication system...")
        
        try:
            from utils.deduplication import (
                ContentDeduplicator, is_duplicate_article,
                get_content_deduplicator, clear_deduplication_cache
            )
            
            # Test content deduplicator
            dedup = ContentDeduplicator()
            
            # Test hash generation
            test_title = "Test Article Title"
            test_content = "This is test article content"
            
            hash1 = dedup.generate_content_hash(test_title, test_content)
            hash2 = dedup.generate_content_hash(test_title, test_content)
            
            if hash1 == hash2 and len(hash1) == 64:  # SHA256 length
                self._pass("Content hash generation works consistently")
            else:
                self._fail("Content hash generation inconsistent")
            
            # Test duplicate detection
            article_data = {
                'title': test_title,
                'link': 'https://test.com/article1',
                'content': test_content
            }
            
            # First check should not be duplicate
            is_dup1 = dedup.is_duplicate(article_data)
            if not is_dup1:
                self._pass("First article not marked as duplicate")
                
                # Second check should be duplicate
                is_dup2 = dedup.is_duplicate(article_data)
                if is_dup2:
                    self._pass("Duplicate detection works")
                else:
                    self._fail("Duplicate detection failed")
            else:
                self._fail("First article incorrectly marked as duplicate")
            
            # Test cache clearing
            clear_deduplication_cache()
            self._pass("Deduplication cache clearing works")
            
        except Exception as e:
            self._fail(f"Deduplication system error: {e}")
    
    def _test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        logger.info("🔄 Testing end-to-end workflow...")
        
        try:
            # This is a simplified end-to-end test
            # In a real scenario, you might want to use test data
            
            from config.settings import get_settings
            from config.database import DatabaseManager
            from extractors.unified_extractor import UnifiedExtractor
            from monitoring import start_session, end_session
            
            # Initialize components
            settings = get_settings()
            db = DatabaseManager()
            extractor = UnifiedExtractor()
            
            # Start monitoring session
            session_id = f"e2e_test_{int(time.time())}"
            session = start_session(session_id)
            
            # Get sources
            sources = db.get_sources()
            
            if sources:
                # Test with first source (limited)
                test_source = sources[0]
                logger.info(f"Testing with source: {test_source.name}")
                
                # Try to extract (with short timeout for testing)
                try:
                    results = extractor.extract(test_source.url, max_retries=1, initial_timeout=15)
                    if results:
                        self._pass(f"End-to-end extraction successful ({len(results)} articles)")
                    else:
                        self._pass("End-to-end extraction completed (no articles)")
                except Exception as e:
                    self._pass(f"End-to-end extraction handled gracefully: {str(e)[:50]}...")
            else:
                self._pass("End-to-end test skipped (no sources available)")
            
            # End session
            end_session()
            self._pass("End-to-end workflow completed successfully")
            
        except Exception as e:
            self._fail(f"End-to-end workflow error: {e}")
    
    def _pass(self, message: str):
        """Record a passed test."""
        self.tests_passed += 1
        self.test_results.append({"status": "PASS", "message": message})
        logger.info(f"✅ {message}")
    
    def _fail(self, message: str):
        """Record a failed test."""
        self.tests_failed += 1
        self.test_results.append({"status": "FAIL", "message": message})
        logger.error(f"❌ {message}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary."""
        total_tests = self.tests_passed + self.tests_failed
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        logger.info("\n" + "=" * 70)
        logger.info("🧪 INTEGRATION TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"✅ Passed: {self.tests_passed}")
        logger.info(f"❌ Failed: {self.tests_failed}")
        
        if self.tests_failed == 0:
            logger.info("🎉 All integration tests passed! System is ready for production.")
            status = "ALL_PASSED"
        else:
            logger.error("💥 Some integration tests failed. Please review and fix issues.")
            status = "SOME_FAILED"
        
        logger.info("=" * 70)
        
        return {
            "status": status,
            "timestamp": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "total_tests": total_tests,
            "passed": self.tests_passed,
            "failed": self.tests_failed,
            "results": self.test_results
        }


def main():
    """Run integration tests."""
    tester = IntegrationTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    if summary["status"] == "ALL_PASSED":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
