"""
Unit tests for database operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from config.database import DatabaseManager, Source, Article, ParsingState, ParsingLog


class TestDatabaseModels:
    """Test Pydantic models for database operations."""
    
    def test_source_model(self):
        """Test Source model validation."""
        source_data = {
            "id": 1,
            "name": "Test Source",
            "url": "https://example.com/feed",
            "source_type": "rss"
        }
        
        source = Source(**source_data)
        assert source.id == 1
        assert source.name == "Test Source"
        assert source.url == "https://example.com/feed"
        assert source.source_type == "rss"
        
        # Test with string ID
        source_with_str_id = Source(id="test-id", name="Test", url="https://test.com", source_type="rss")
        assert source_with_str_id.id == "test-id"
        
        # Test hashability
        source_set = {source, source_with_str_id}
        assert len(source_set) == 2
    
    def test_article_model(self):
        """Test Article model validation."""
        article_data = {
            "title": "Test Article",
            "link": "https://example.com/article",
            "description": "Test description",
            "content": "Test content",
            "source_id": 1,
            "pub_date": datetime.now(timezone.utc)
        }
        
        article = Article(**article_data)
        assert article.title == "Test Article"
        assert article.link == "https://example.com/article"
        assert article.source_id == 1
        assert article.pub_date is not None
    
    def test_parsing_state_model(self):
        """Test ParsingState model validation."""
        state_data = {
            "source_id": 1,
            "last_parsed_at": datetime.now(timezone.utc),
            "last_article_link": "https://example.com/last-article"
        }
        
        state = ParsingState(**state_data)
        assert state.source_id == 1
        assert state.last_parsed_at is not None
        assert state.last_article_link == "https://example.com/last-article"
    
    def test_parsing_log_model(self):
        """Test ParsingLog model validation."""
        log_data = {
            "source_id": 1,
            "started_at": datetime.now(timezone.utc),
            "finished_at": datetime.now(timezone.utc),
            "articles_fetched": 5,
            "status": "success"
        }
        
        log = ParsingLog(**log_data)
        assert log.source_id == 1
        assert log.articles_fetched == 5
        assert log.status == "success"


class TestDatabaseManager:
    """Test DatabaseManager operations."""
    
    @patch('config.database.db_config.get_client')
    def test_get_sources(self, mock_get_client):
        """Test getting sources from database."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        # Chain the method calls
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Mock response data
        mock_execute.data = [
            {
                "id": 1,
                "name": "Test Source",
                "url": "https://example.com/feed",
                "source_type": "rss"
            }
        ]
        
        mock_get_client.return_value = mock_client
        
        # Test the method
        db_manager = DatabaseManager()
        sources = db_manager.get_sources()
        
        assert len(sources) == 1
        assert isinstance(sources[0], Source)
        assert sources[0].name == "Test Source"
        
        # Verify the correct table and filter were used
        mock_client.table.assert_called_with("sources")
        mock_table.select.assert_called_with("*")
        mock_select.eq.assert_called_with("source_type", "rss")
    
    @patch('config.database.db_config.get_client')
    def test_get_parsing_state(self, mock_get_client):
        """Test getting parsing state from database."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        # Chain the method calls
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Mock response data
        mock_execute.data = [
            {
                "source_id": 1,
                "last_parsed_at": "2024-01-01T12:00:00Z",
                "last_article_link": "https://example.com/last-article"
            }
        ]
        
        mock_get_client.return_value = mock_client
        
        # Test the method
        db_manager = DatabaseManager()
        state = db_manager.get_parsing_state("1")
        
        assert state is not None
        assert isinstance(state, ParsingState)
        assert state.source_id == 1
        assert state.last_article_link == "https://example.com/last-article"
        
        # Test with no data
        mock_execute.data = []
        state_none = db_manager.get_parsing_state("999")
        assert state_none is None
    
    @patch('config.database.db_config.get_client')
    def test_insert_article(self, mock_get_client):
        """Test inserting article into database."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_upsert = Mock()
        mock_execute = Mock()
        
        # Chain the method calls
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = mock_execute
        
        # Mock response data
        mock_execute.data = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://example.com/article",
                "description": "Test description",
                "content": "Test content",
                "source_id": 1
            }
        ]
        
        mock_get_client.return_value = mock_client
        
        # Create test article
        article = Article(
            title="Test Article",
            link="https://example.com/article",
            description="Test description",
            content="Test content",
            source_id=1
        )
        
        # Test the method
        db_manager = DatabaseManager()
        result = db_manager.insert_article(article)
        
        assert result is not None
        assert isinstance(result, Article)
        assert result.title == "Test Article"
        assert result.link == "https://example.com/article"  # Should be converted back from 'url'
        
        # Verify upsert was called
        mock_table.upsert.assert_called_once()
        mock_upsert.execute.assert_called_once()
    
    @patch('config.database.db_config.get_client')
    def test_update_parsing_state(self, mock_get_client):
        """Test updating parsing state in database."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_update = Mock()
        mock_insert = Mock()
        
        # Chain the method calls for checking existing record
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Mock for update/insert operations
        mock_table.update.return_value = mock_update
        mock_table.insert.return_value = mock_insert
        mock_update.eq.return_value = mock_eq
        mock_insert.execute.return_value = mock_execute
        mock_update.execute.return_value = mock_execute
        
        # Mock response data for existing record check
        mock_execute.data = [{"source_id": 1}]  # Record exists
        
        # Mock response data for update
        update_response = Mock()
        update_response.data = [
            {
                "source_id": 1,
                "last_parsed_at": "2024-01-01T12:00:00Z",
                "last_article_link": "https://example.com/new-article"
            }
        ]
        mock_eq.execute.return_value = update_response
        
        mock_get_client.return_value = mock_client
        
        # Create test parsing state
        state = ParsingState(
            source_id=1,
            last_parsed_at=datetime.now(timezone.utc),
            last_article_link="https://example.com/new-article"
        )
        
        # Test the method
        db_manager = DatabaseManager()
        result = db_manager.update_parsing_state(state)
        
        assert result is not None
        assert isinstance(result, ParsingState)
        assert result.source_id == 1
    
    @patch('config.database.db_config.get_client')
    def test_create_parsing_log(self, mock_get_client):
        """Test creating parsing log entry."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        # Chain the method calls
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Mock response data
        mock_execute.data = [
            {
                "id": 1,
                "source_id": 1,
                "started_at": "2024-01-01T12:00:00Z",
                "finished_at": "2024-01-01T12:05:00Z",
                "articles_fetched": 5,
                "status": "success"
            }
        ]
        
        mock_get_client.return_value = mock_client
        
        # Create test parsing log
        log = ParsingLog(
            source_id=1,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            articles_fetched=5,
            status="success"
        )
        
        # Test the method
        db_manager = DatabaseManager()
        result = db_manager.create_parsing_log(log)
        
        assert result is not None
        assert isinstance(result, ParsingLog)
        assert result.source_id == 1
        assert result.articles_fetched == 5
        assert result.status == "success"
        
        # Verify insert was called
        mock_table.insert.assert_called_once()
        mock_insert.execute.assert_called_once()


class TestDatabaseErrorHandling:
    """Test error handling in database operations."""
    
    @patch('config.database.db_config.get_client')
    def test_database_connection_error(self, mock_get_client):
        """Test handling of database connection errors."""
        # Mock connection error
        mock_get_client.side_effect = Exception("Connection failed")
        
        # Should raise the exception
        with pytest.raises(Exception):
            DatabaseManager()
    
    @patch('config.database.db_config.get_client')
    def test_insert_article_error_handling(self, mock_get_client):
        """Test error handling in article insertion."""
        # Mock Supabase client that raises an error
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Database error")
        mock_get_client.return_value = mock_client
        
        # Create test article
        article = Article(
            title="Test Article",
            link="https://example.com/article",
            source_id=1
        )
        
        # Test the method - should handle error gracefully
        db_manager = DatabaseManager()
        result = db_manager.insert_article(article)
        
        # Should return None on error
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
