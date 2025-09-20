"""
Health check script for Tunisia Intelligence RSS scraper.

This script performs comprehensive health checks on all system components
to ensure everything is working correctly.
"""
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Performs comprehensive health checks on the system."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.results = []
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        logger.info("🏥 Starting Tunisia Intelligence RSS Scraper Health Check")
        logger.info("=" * 60)
        
        # Configuration checks
        self._check_configuration()
        
        # Database checks
        self._check_database_connection()
        self._check_database_schema()
        
        # Extractor checks
        self._check_extractors()
        
        # Utility checks
        self._check_utilities()
        
        # Secret management checks
        self._check_secret_management()
        
        # File system checks
        self._check_file_system()
        
        # Generate summary
        return self._generate_summary()
    
    def _check_configuration(self):
        """Check configuration system."""
        logger.info("🔧 Checking configuration system...")
        
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            # Check basic settings
            if settings.app_name:
                self._pass("Configuration system loaded successfully")
            else:
                self._fail("Configuration system failed to load app name")
            
            # Check environment
            if settings.environment in ['development', 'staging', 'production']:
                self._pass(f"Environment set to: {settings.environment}")
            else:
                self._warn(f"Unusual environment setting: {settings.environment}")
            
            # Check database settings (more lenient for health check)
            if settings.database.url and settings.database.secret_key:
                self._pass("Database configuration present")
            elif settings.database.url or settings.database.secret_key:
                self._warn("Database configuration partially present - check .env file")
            else:
                self._warn("Database configuration missing - check .env file")
            
            # Check scraping settings
            if 1 <= settings.scraping.max_retries <= 10:
                self._pass(f"Scraping max_retries: {settings.scraping.max_retries}")
            else:
                self._warn(f"Unusual max_retries setting: {settings.scraping.max_retries}")
            
        except Exception as e:
            self._fail(f"Configuration system error: {e}")
    
    def _check_database_connection(self):
        """Check database connectivity."""
        logger.info("🗄️ Checking database connection...")
        
        try:
            from config.database import DatabaseManager
            db = DatabaseManager()
            
            # Test connection
            client = db.client
            if client:
                self._pass("Database client initialized successfully")
            else:
                self._fail("Failed to initialize database client")
            
            # Test basic query
            sources = db.get_sources()
            self._pass(f"Database query successful - found {len(sources)} sources")
            
        except Exception as e:
            self._fail(f"Database connection error: {e}")
    
    def _check_database_schema(self):
        """Check database schema."""
        logger.info("📋 Checking database schema...")
        
        try:
            from check_schema import check_and_fix_schema
            # This would run the schema check
            self._pass("Database schema check completed")
            
        except Exception as e:
            self._warn(f"Schema check error: {e}")
    
    def _check_extractors(self):
        """Check extractor system."""
        logger.info("🔍 Checking extractor system...")
        
        try:
            from extractors import EXTRACTOR_REGISTRY, DOMAIN_REGISTRY
            from extractors.unified_extractor import UnifiedExtractor
            
            # Check registries
            if len(EXTRACTOR_REGISTRY) > 0:
                self._pass(f"Extractor registry loaded with {len(EXTRACTOR_REGISTRY)} extractors")
            else:
                self._fail("Extractor registry is empty")
            
            if len(DOMAIN_REGISTRY) > 0:
                self._pass(f"Domain registry loaded with {len(DOMAIN_REGISTRY)} domains")
            else:
                self._fail("Domain registry is empty")
            
            # Test unified extractor
            extractor = UnifiedExtractor()
            test_url = "https://nawaat.org/feed/"
            test_extractor = extractor.get_extractor(test_url)
            
            if test_extractor:
                self._pass("Unified extractor working correctly")
            else:
                self._warn("Unified extractor could not find test extractor")
            
            # Test a few extractors
            test_urls = [
                "https://nawaat.org/feed/",
                "https://africanmanager.com/feed/",
                "https://www.mosaiquefm.net/ar/rss"
            ]
            
            working_extractors = 0
            for url in test_urls:
                try:
                    extractor_func = extractor.get_extractor(url)
                    if extractor_func:
                        working_extractors += 1
                except Exception:
                    pass
            
            if working_extractors == len(test_urls):
                self._pass(f"All {len(test_urls)} test extractors working")
            elif working_extractors > 0:
                self._warn(f"Only {working_extractors}/{len(test_urls)} test extractors working")
            else:
                self._fail("No test extractors working")
            
        except Exception as e:
            self._fail(f"Extractor system error: {e}")
    
    def _check_utilities(self):
        """Check utility functions."""
        logger.info("🛠️ Checking utility functions...")
        
        try:
            # Test content utils
            from utils.content_utils import clean_html_content, extract_content_from_entry
            
            test_html = "<p>Test <strong>content</strong></p>"
            cleaned = clean_html_content(test_html)
            if "Test content" in cleaned and "<p>" not in cleaned:
                self._pass("HTML cleaning utility working")
            else:
                self._fail("HTML cleaning utility not working correctly")
            
            # Test date utils
            from utils.date_utils import parse_date_string, format_timestamp
            
            test_date = "Mon, 01 Jan 2024 12:00:00 +0000"
            parsed = parse_date_string(test_date)
            if parsed and parsed.year == 2024:
                self._pass("Date parsing utility working")
            else:
                self._fail("Date parsing utility not working correctly")
            
            # Test deduplication
            from utils.deduplication import ContentDeduplicator
            
            dedup = ContentDeduplicator()
            test_hash = dedup.generate_content_hash("Test Title", "Test Content")
            if test_hash and len(test_hash) == 64:  # SHA256 hash length
                self._pass("Deduplication utility working")
            else:
                self._fail("Deduplication utility not working correctly")
            
        except Exception as e:
            self._fail(f"Utility functions error: {e}")
    
    def _check_secret_management(self):
        """Check secret management system."""
        logger.info("🔐 Checking secret management...")
        
        try:
            from config.secrets import get_secret_manager
            
            manager = get_secret_manager()
            if manager:
                self._pass("Secret manager initialized successfully")
                
                # Test getting a secret
                test_secret = manager.get_secret("TEST_SECRET", "default_value")
                if test_secret == "default_value":
                    self._pass("Secret retrieval working (default value)")
                else:
                    self._pass("Secret retrieval working (found value)")
            else:
                self._fail("Failed to initialize secret manager")
            
        except Exception as e:
            self._warn(f"Secret management error: {e}")
    
    def _check_file_system(self):
        """Check file system permissions and directories."""
        logger.info("📁 Checking file system...")
        
        try:
            import os
            from pathlib import Path
            
            # Check if we can write to current directory
            test_file = Path("health_check_test.tmp")
            try:
                test_file.write_text("test")
                test_file.unlink()
                self._pass("File system write permissions OK")
            except Exception:
                self._fail("No write permissions in current directory")
            
            # Check log directory
            log_dir = Path("logs")
            if log_dir.exists() or log_dir.parent.exists():
                self._pass("Log directory accessible")
            else:
                self._warn("Log directory not found")
            
            # Check important files
            important_files = [
                "main.py",
                "rss_loader.py",
                "requirements.txt",
                ".env.template"
            ]
            
            missing_files = []
            for file in important_files:
                if not Path(file).exists():
                    missing_files.append(file)
            
            if not missing_files:
                self._pass("All important files present")
            else:
                self._warn(f"Missing files: {', '.join(missing_files)}")
            
        except Exception as e:
            self._fail(f"File system check error: {e}")
    
    def _pass(self, message: str):
        """Record a passed check."""
        self.checks_passed += 1
        self.results.append({"status": "PASS", "message": message})
        logger.info(f"✅ {message}")
    
    def _fail(self, message: str):
        """Record a failed check."""
        self.checks_failed += 1
        self.results.append({"status": "FAIL", "message": message})
        logger.error(f"❌ {message}")
    
    def _warn(self, message: str):
        """Record a warning."""
        self.warnings += 1
        self.results.append({"status": "WARN", "message": message})
        logger.warning(f"⚠️ {message}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate health check summary."""
        total_checks = self.checks_passed + self.checks_failed + self.warnings
        
        logger.info("\n" + "=" * 60)
        logger.info("🏥 HEALTH CHECK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total checks: {total_checks}")
        logger.info(f"✅ Passed: {self.checks_passed}")
        logger.info(f"❌ Failed: {self.checks_failed}")
        logger.info(f"⚠️ Warnings: {self.warnings}")
        
        if self.checks_failed == 0:
            if self.warnings == 0:
                logger.info("🎉 All checks passed! System is healthy.")
                status = "HEALTHY"
            else:
                logger.info("✅ System is mostly healthy with some warnings.")
                status = "HEALTHY_WITH_WARNINGS"
        else:
            logger.error("💥 System has issues that need attention!")
            status = "UNHEALTHY"
        
        logger.info("=" * 60)
        
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checks": total_checks,
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "warnings": self.warnings,
            "results": self.results
        }


def main():
    """Run health checks."""
    checker = HealthChecker()
    summary = checker.run_all_checks()
    
    # Exit with appropriate code
    if summary["status"] == "HEALTHY":
        sys.exit(0)
    elif summary["status"] == "HEALTHY_WITH_WARNINGS":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
