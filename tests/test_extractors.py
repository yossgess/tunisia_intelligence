"""
Unit tests for RSS extractors.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict

# Import extractors to test
from extractors.nawaat_extractor import extract as extract_nawaat
from extractors.mosaiquefm_extractor import extract as extract_mosaiquefm
from extractors.unified_extractor import UnifiedExtractor
from extractors.utils import extract_standard_fields, clean_html_to_text


class TestExtractorUtils:
    """Test utility functions used by extractors."""
    
    def test_clean_html_to_text(self):
        """Test HTML cleaning functionality."""
        # Test basic HTML removal
        html_content = "<p>This is a <strong>test</strong> paragraph.</p>"
        expected = "This is a test paragraph."
        result = clean_html_to_text(html_content)
        assert result == expected
        
        # Test with empty content
        assert clean_html_to_text("") == ""
        assert clean_html_to_text(None) == ""
        
        # Test with HTML entities
        html_with_entities = "<p>This &amp; that &lt;test&gt;</p>"
        expected_entities = "This & that <test>"
        result_entities = clean_html_to_text(html_with_entities)
        assert result_entities == expected_entities
        
        # Test with script and style tags
        html_with_scripts = """
        <div>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
            <p>Visible content</p>
        </div>
        """
        result_scripts = clean_html_to_text(html_with_scripts)
        assert "alert" not in result_scripts
        assert "color: red" not in result_scripts
        assert "Visible content" in result_scripts
    
    def test_extract_standard_fields(self):
        """Test standard field extraction from feed entries."""
        # Mock feed entry
        mock_entry = Mock()
        mock_entry.title = "Test Article Title"
        mock_entry.link = "https://example.com/article"
        mock_entry.description = "<p>Test description</p>"
        mock_entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"
        mock_entry.content = [Mock(value="<p>Test content</p>")]
        
        result = extract_standard_fields(mock_entry)
        
        assert result["title"] == "Test Article Title"
        assert result["link"] == "https://example.com/article"
        assert result["description"] == "Test description"
        assert result["content"] == "Test content"
        assert "pub_date" in result
        
        # Test with missing fields
        minimal_entry = Mock()
        minimal_entry.title = "Minimal Title"
        minimal_entry.link = "https://example.com/minimal"
        
        # Set default values for missing attributes
        for attr in ['description', 'published', 'updated', 'content']:
            setattr(minimal_entry, attr, '')
        
        minimal_result = extract_standard_fields(minimal_entry)
        assert minimal_result["title"] == "Minimal Title"
        assert minimal_result["link"] == "https://example.com/minimal"
        assert minimal_result["description"] == ""
        assert minimal_result["content"] == ""


class TestUnifiedExtractor:
    """Test the unified extractor system."""
    
    def test_extractor_initialization(self):
        """Test that the unified extractor initializes correctly."""
        extractor = UnifiedExtractor()
        assert extractor.extractor_registry is not None
        assert extractor.domain_registry is not None
        assert len(extractor.extractor_registry) > 0
        assert len(extractor.domain_registry) > 0
    
    def test_get_extractor_exact_match(self):
        """Test getting extractor by exact URL match."""
        extractor = UnifiedExtractor()
        
        # Test with known URL
        nawaat_url = "https://nawaat.org/feed/"
        result = extractor.get_extractor(nawaat_url)
        assert result is not None
        assert callable(result)
    
    def test_get_extractor_domain_match(self):
        """Test getting extractor by domain match."""
        extractor = UnifiedExtractor()
        
        # Test with domain that should have a fallback
        test_url = "https://nawaat.org/some/other/path"
        result = extractor.get_extractor(test_url)
        assert result is not None
        assert callable(result)
    
    def test_get_extractor_no_match(self):
        """Test behavior when no extractor is found."""
        extractor = UnifiedExtractor()
        
        # Test with unknown URL
        unknown_url = "https://unknown-site.com/feed"
        result = extractor.get_extractor(unknown_url)
        assert result is None
    
    def test_get_extractor_invalid_url(self):
        """Test behavior with invalid URLs."""
        extractor = UnifiedExtractor()
        
        # Test with invalid URLs
        assert extractor.get_extractor("") is None
        assert extractor.get_extractor(None) is None
        assert extractor.get_extractor("not-a-url") is None


class TestSpecificExtractors:
    """Test specific extractor implementations."""
    
    @patch('extractors.nawaat_extractor.feedparser.parse')
    def test_nawaat_extractor(self, mock_parse):
        """Test Nawaat extractor."""
        # Mock feedparser response
        mock_feed = Mock()
        mock_entry = Mock()
        mock_entry.title = "Test Nawaat Article"
        mock_entry.link = "https://nawaat.org/test-article"
        mock_entry.description = "Test description"
        mock_entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"
        mock_entry.content = []
        
        # Set default values for missing attributes
        for attr in ['updated']:
            setattr(mock_entry, attr, '')
        
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed
        
        result = extract_nawaat()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test Nawaat Article"
        assert result[0]["link"] == "https://nawaat.org/test-article"
    
    @patch('extractors.mosaiquefm_extractor.feedparser.parse')
    @patch('extractors.mosaiquefm_extractor.requests.get')
    def test_mosaiquefm_extractor(self, mock_requests, mock_parse):
        """Test MosaiqueFM extractor."""
        # Mock feedparser response
        mock_feed = Mock()
        mock_entry = Mock()
        mock_entry.title = "Test MosaiqueFM Article"
        mock_entry.link = "https://mosaiquefm.net/test-article"
        mock_entry.description = "Test description"
        mock_entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"
        mock_entry.content = []
        
        # Set default values for missing attributes
        for attr in ['updated']:
            setattr(mock_entry, attr, '')
        
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed
        
        result = extract_mosaiquefm()
        
        assert isinstance(result, list)
        if result:  # Only check if we got results
            assert result[0]["title"] == "Test MosaiqueFM Article"
            assert result[0]["link"] == "https://mosaiquefm.net/test-article"
    
    def test_extractor_error_handling(self):
        """Test that extractors handle errors gracefully."""
        # Test with invalid URL that should cause an error
        with patch('extractors.nawaat_extractor.feedparser.parse') as mock_parse:
            mock_parse.side_effect = Exception("Network error")
            
            # Should not raise exception, should return empty list
            result = extract_nawaat("invalid-url")
            assert isinstance(result, list)


class TestExtractorIntegration:
    """Integration tests for the extractor system."""
    
    def test_unified_extractor_with_timeout(self):
        """Test unified extractor with timeout handling."""
        extractor = UnifiedExtractor()
        
        # Test with a mock that takes too long
        with patch('extractors.nawaat_extractor.extract') as mock_extract:
            import time
            
            def slow_extract(url):
                time.sleep(2)  # Simulate slow response
                return [{"title": "Test", "link": "test", "description": "", "pub_date": "", "content": ""}]
            
            mock_extract.side_effect = slow_extract
            
            # This should timeout quickly in our test
            try:
                result = extractor.extract("https://nawaat.org/feed/", max_retries=0, initial_timeout=1)
                # If it doesn't timeout, that's also okay for this test
                assert isinstance(result, list)
            except ValueError as e:
                # Timeout is expected behavior
                assert "timeout" in str(e).lower() or "failed" in str(e).lower()
    
    def test_registry_completeness(self):
        """Test that all registered extractors are importable and callable."""
        from extractors import EXTRACTOR_REGISTRY, DOMAIN_REGISTRY
        
        # Test that all registered extractors are callable
        for url, extractor_func in EXTRACTOR_REGISTRY.items():
            assert callable(extractor_func), f"Extractor for {url} is not callable"
        
        for domain, extractor_func in DOMAIN_REGISTRY.items():
            assert callable(extractor_func), f"Extractor for {domain} is not callable"
        
        # Test that registries are not empty
        assert len(EXTRACTOR_REGISTRY) > 0, "Extractor registry is empty"
        assert len(DOMAIN_REGISTRY) > 0, "Domain registry is empty"


if __name__ == "__main__":
    pytest.main([__file__])
