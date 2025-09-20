"""
Unit tests for configuration management.
"""
import pytest
import os
from unittest.mock import patch, Mock
from pydantic import ValidationError

from config.settings import (
    Settings, DatabaseSettings, ScrapingSettings, LoggingSettings,
    MonitoringSettings, ContentSettings, get_settings, reload_settings
)
from config.secrets import SecretManager, get_secret_manager


class TestDatabaseSettings:
    """Test database configuration settings."""
    
    def test_valid_database_settings(self):
        """Test valid database configuration."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'a' * 60  # Valid length key
        }):
            settings = DatabaseSettings()
            assert settings.url == 'https://test.supabase.co'
            assert len(settings.secret_key) == 60
    
    def test_invalid_database_url(self):
        """Test invalid database URL validation."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'http://insecure.com',  # Not HTTPS
            'SUPABASE_SECRET_KEY': 'a' * 60
        }):
            with pytest.raises(ValidationError):
                DatabaseSettings()
    
    def test_invalid_secret_key(self):
        """Test invalid secret key validation."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'short'  # Too short
        }):
            with pytest.raises(ValidationError):
                DatabaseSettings()


class TestScrapingSettings:
    """Test scraping configuration settings."""
    
    def test_default_scraping_settings(self):
        """Test default scraping configuration."""
        settings = ScrapingSettings()
        assert settings.max_retries == 3
        assert settings.initial_timeout == 60
        assert settings.rate_limit_delay == 1.0
        assert settings.batch_size == 100
        assert settings.max_workers == 5
    
    def test_custom_scraping_settings(self):
        """Test custom scraping configuration."""
        with patch.dict(os.environ, {
            'SCRAPING_MAX_RETRIES': '5',
            'SCRAPING_INITIAL_TIMEOUT': '120',
            'SCRAPING_RATE_LIMIT_DELAY': '2.0'
        }):
            settings = ScrapingSettings()
            assert settings.max_retries == 5
            assert settings.initial_timeout == 120
            assert settings.rate_limit_delay == 2.0
    
    def test_invalid_scraping_settings(self):
        """Test invalid scraping configuration."""
        # Test invalid max_retries
        with patch.dict(os.environ, {'SCRAPING_MAX_RETRIES': '15'}):  # Too high
            with pytest.raises(ValidationError):
                ScrapingSettings()
        
        # Test invalid timeout
        with patch.dict(os.environ, {'SCRAPING_INITIAL_TIMEOUT': '5'}):  # Too low
            with pytest.raises(ValidationError):
                ScrapingSettings()
        
        # Test invalid rate limit
        with patch.dict(os.environ, {'SCRAPING_RATE_LIMIT_DELAY': '15.0'}):  # Too high
            with pytest.raises(ValidationError):
                ScrapingSettings()


class TestLoggingSettings:
    """Test logging configuration settings."""
    
    def test_default_logging_settings(self):
        """Test default logging configuration."""
        settings = LoggingSettings()
        assert settings.level == "INFO"
        assert settings.file_path == "rss_loader.log"
        assert settings.max_file_size == 10485760  # 10MB
        assert settings.backup_count == 5
    
    def test_custom_logging_settings(self):
        """Test custom logging configuration."""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE_PATH': 'custom.log',
            'LOG_MAX_FILE_SIZE': '5242880'  # 5MB
        }):
            settings = LoggingSettings()
            assert settings.level == "DEBUG"
            assert settings.file_path == "custom.log"
            assert settings.max_file_size == 5242880
    
    def test_invalid_log_level(self):
        """Test invalid log level validation."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'INVALID'}):
            with pytest.raises(ValidationError):
                LoggingSettings()


class TestMonitoringSettings:
    """Test monitoring configuration settings."""
    
    def test_default_monitoring_settings(self):
        """Test default monitoring configuration."""
        settings = MonitoringSettings()
        assert settings.enabled is True
        assert settings.metrics_retention_days == 30
        assert settings.alert_on_errors is True
        assert settings.alert_error_threshold == 5
    
    def test_custom_monitoring_settings(self):
        """Test custom monitoring configuration."""
        with patch.dict(os.environ, {
            'MONITORING_ENABLED': 'false',
            'MONITORING_METRICS_RETENTION_DAYS': '60',
            'MONITORING_WEBHOOK_URL': 'https://hooks.slack.com/test'
        }):
            settings = MonitoringSettings()
            assert settings.enabled is False
            assert settings.metrics_retention_days == 60
            assert settings.webhook_url == 'https://hooks.slack.com/test'
    
    def test_invalid_retention_days(self):
        """Test invalid retention days validation."""
        with patch.dict(os.environ, {'MONITORING_METRICS_RETENTION_DAYS': '400'}):  # Too high
            with pytest.raises(ValidationError):
                MonitoringSettings()


class TestContentSettings:
    """Test content processing configuration settings."""
    
    def test_default_content_settings(self):
        """Test default content configuration."""
        settings = ContentSettings()
        assert settings.min_title_length == 5
        assert settings.min_content_length == 50
        assert settings.max_content_length == 50000
        assert settings.enable_deduplication is True
        assert settings.default_language == "ar"
        assert "ar" in settings.supported_languages
    
    def test_custom_content_settings(self):
        """Test custom content configuration."""
        with patch.dict(os.environ, {
            'CONTENT_MIN_TITLE_LENGTH': '10',
            'CONTENT_ENABLE_SENTIMENT_ANALYSIS': 'true',
            'CONTENT_DEFAULT_LANGUAGE': 'fr'
        }):
            settings = ContentSettings()
            assert settings.min_title_length == 10
            assert settings.enable_sentiment_analysis is True
            assert settings.default_language == "fr"


class TestMainSettings:
    """Test main application settings."""
    
    @patch('config.settings.Path.mkdir')
    @patch('config.settings.Path.exists')
    def test_settings_initialization(self, mock_exists, mock_mkdir):
        """Test settings initialization."""
        mock_exists.return_value = False  # Log directory doesn't exist
        
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'a' * 60
        }):
            settings = Settings()
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.app_name == "Tunisia Intelligence RSS Scraper"
            
            # Check that log directory creation was attempted
            mock_mkdir.assert_called_once()
    
    def test_environment_validation(self):
        """Test environment validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'invalid',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'a' * 60
        }):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_settings_methods(self):
        """Test settings utility methods."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'a' * 60
        }):
            settings = Settings()
            
            assert settings.is_production() is True
            assert settings.is_development() is False
            assert settings.get_database_url() == 'https://test.supabase.co'
            assert len(settings.get_database_key()) == 60
            
            # Test to_dict excludes sensitive data
            settings_dict = settings.to_dict()
            assert 'secret_key' not in str(settings_dict)
    
    def test_global_settings_functions(self):
        """Test global settings functions."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SECRET_KEY': 'a' * 60
        }):
            # Test get_settings
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2  # Should be singleton
            
            # Test reload_settings
            settings3 = reload_settings()
            assert settings3 is not settings1  # Should be new instance


class TestSecretManager:
    """Test secret management functionality."""
    
    def test_env_backend_initialization(self):
        """Test environment variable backend initialization."""
        manager = SecretManager(backend="env")
        assert manager.backend == "env"
    
    def test_get_secret_from_env(self):
        """Test getting secret from environment variables."""
        with patch.dict(os.environ, {'TEST_SECRET': 'test_value'}):
            manager = SecretManager(backend="env")
            result = manager.get_secret('TEST_SECRET')
            assert result == 'test_value'
            
            # Test with default
            result = manager.get_secret('NONEXISTENT', 'default_value')
            assert result == 'default_value'
    
    def test_set_secret_env_backend(self):
        """Test setting secret with environment backend."""
        manager = SecretManager(backend="env")
        success = manager.set_secret('NEW_SECRET', 'new_value')
        assert success is True
        assert os.environ.get('NEW_SECRET') == 'new_value'
    
    def test_file_backend_initialization(self):
        """Test file backend initialization."""
        with patch('config.secrets.Path.exists') as mock_exists:
            mock_exists.return_value = False  # Key file doesn't exist
            
            with patch('config.secrets.SecretManager._generate_encryption_key') as mock_gen:
                with patch('config.secrets.SecretManager._load_encryption_key') as mock_load:
                    mock_load.return_value = b'test_key_32_bytes_long_exactly!!'
                    
                    manager = SecretManager(backend="file")
                    assert manager.backend == "file"
                    mock_gen.assert_called_once()
    
    def test_unsupported_backend(self):
        """Test unsupported backend raises error."""
        with pytest.raises(ValueError):
            SecretManager(backend="unsupported")
    
    def test_global_secret_manager(self):
        """Test global secret manager functions."""
        with patch.dict(os.environ, {'TEST_GLOBAL_SECRET': 'global_value'}):
            # Test get_secret function
            result = get_secret('TEST_GLOBAL_SECRET')
            assert result == 'global_value'
            
            # Test get_secret_manager function
            manager1 = get_secret_manager()
            manager2 = get_secret_manager()
            assert manager1 is manager2  # Should be singleton


class TestConfigIntegration:
    """Integration tests for configuration system."""
    
    def test_settings_with_secrets(self):
        """Test settings integration with secret management."""
        with patch('config.secrets.get_secret') as mock_get_secret:
            mock_get_secret.side_effect = lambda key, default=None: {
                'SUPABASE_URL': 'https://secret.supabase.co',
                'SUPABASE_SECRET_KEY': 'secret_key_from_vault_' + 'x' * 40
            }.get(key, default)
            
            # This should work without environment variables
            with patch.dict(os.environ, {}, clear=True):
                from config.database import DatabaseConfig
                config = DatabaseConfig()
                
                assert config.url == 'https://secret.supabase.co'
                assert 'secret_key_from_vault' in config.secret_key
    
    def test_complete_configuration_loading(self):
        """Test loading complete configuration from environment."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'SUPABASE_URL': 'https://prod.supabase.co',
            'SUPABASE_SECRET_KEY': 'production_key_' + 'x' * 45,
            'SCRAPING_MAX_RETRIES': '5',
            'LOG_LEVEL': 'WARNING',
            'MONITORING_ENABLED': 'true',
            'CONTENT_ENABLE_DEDUPLICATION': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Verify all subsettings are configured correctly
            assert settings.environment == 'production'
            assert settings.debug is False
            assert settings.database.url == 'https://prod.supabase.co'
            assert settings.scraping.max_retries == 5
            assert settings.logging.level == 'WARNING'
            assert settings.monitoring.enabled is True
            assert settings.content.enable_deduplication is True


if __name__ == "__main__":
    pytest.main([__file__])
