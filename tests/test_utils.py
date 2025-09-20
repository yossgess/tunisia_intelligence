"""
Unit tests for utility functions.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from utils.content_utils import clean_html_content, extract_content_from_entry, extract_media_info
from utils.date_utils import parse_date_enhanced, parse_date_string, format_timestamp, is_recent


class TestContentUtils:
    """Test content utility functions."""
    
    def test_clean_html_content(self):
        """Test HTML content cleaning."""
        # Test basic HTML removal
        html = "<p>This is a <strong>test</strong> paragraph.</p>"
        expected = "This is a test paragraph."
        result = clean_html_content(html)
        assert result == expected
        
        # Test with empty content
        assert clean_html_content("") == ""
        assert clean_html_content(None) == ""
        
        # Test with complex HTML
        complex_html = """
        <div>
            <script>alert('malicious');</script>
            <style>body { color: red; }</style>
            <nav>Navigation</nav>
            <header>Header</header>
            <footer>Footer</footer>
            <p>Main content here</p>
        </div>
        """
        result = clean_html_content(complex_html)
        assert "malicious" not in result
        assert "color: red" not in result
        assert "Navigation" not in result
        assert "Header" not in result
        assert "Footer" not in result
        assert "Main content here" in result
        
        # Test with HTML entities
        html_entities = "<p>This &amp; that &lt;test&gt; &quot;quoted&quot;</p>"
        result = clean_html_content(html_entities)
        assert "This & that <test> \"quoted\"" == result
    
    def test_extract_content_from_entry(self):
        """Test content extraction from feed entries."""
        # Test with content field
        entry_with_content = {
            "content": [{"value": "Content from content field"}],
            "summary": "Summary content",
            "description": "Description content"
        }
        result = extract_content_from_entry(entry_with_content)
        assert result == "Content from content field"
        
        # Test with summary field (fallback)
        entry_with_summary = {
            "summary": "Summary content",
            "description": "Description content"
        }
        result = extract_content_from_entry(entry_with_summary)
        assert result == "Summary content"
        
        # Test with description field (fallback)
        entry_with_description = {
            "description": "Description content"
        }
        result = extract_content_from_entry(entry_with_description)
        assert result == "Description content"
        
        # Test with empty entry
        empty_entry = {}
        result = extract_content_from_entry(empty_entry)
        assert result == ""
        
        # Test with multiple content items
        entry_multiple_content = {
            "content": [
                {"value": "First content"},
                {"value": "Second content"}
            ]
        }
        result = extract_content_from_entry(entry_multiple_content)
        assert "First content Second content" == result
    
    def test_extract_media_info(self):
        """Test media information extraction."""
        # Test with media content
        entry_with_media = {
            "media_content": [{"url": "https://example.com/image.jpg", "type": "image/jpeg"}],
            "enclosures": [{"href": "https://example.com/audio.mp3", "type": "audio/mpeg"}]
        }
        result = extract_media_info(entry_with_media)
        assert result is not None
        assert "media" in result
        assert "enclosures" in result
        
        # Test with no media
        entry_no_media = {
            "title": "Just a title"
        }
        result = extract_media_info(entry_no_media)
        assert result is None
        
        # Test with thumbnail
        entry_with_thumbnail = {
            "media_thumbnail": [{"url": "https://example.com/thumb.jpg"}]
        }
        result = extract_media_info(entry_with_thumbnail)
        assert result is not None
        assert "thumbnail" in result


class TestDateUtils:
    """Test date utility functions."""
    
    def test_parse_date_string(self):
        """Test date string parsing."""
        # Test RFC 822 format
        rfc822_date = "Mon, 01 Jan 2024 12:00:00 +0000"
        result = parse_date_string(rfc822_date)
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        
        # Test ISO 8601 format
        iso_date = "2024-01-01T12:00:00Z"
        result = parse_date_string(iso_date)
        assert result is not None
        assert result.year == 2024
        
        # Test SQL format
        sql_date = "2024-01-01 12:00:00"
        result = parse_date_string(sql_date)
        assert result is not None
        assert result.year == 2024
        
        # Test invalid date
        invalid_date = "not a date"
        result = parse_date_string(invalid_date)
        assert result is None
        
        # Test empty date
        result = parse_date_string("")
        assert result is None
        
        result = parse_date_string(None)
        assert result is None
    
    def test_parse_date_enhanced(self):
        """Test enhanced date parsing from feed entries."""
        # Mock entry with published_parsed
        entry_with_parsed = Mock()
        entry_with_parsed.published_parsed = Mock()
        entry_with_parsed.published_parsed.tm_year = 2024
        entry_with_parsed.published_parsed.tm_mon = 1
        entry_with_parsed.published_parsed.tm_mday = 1
        entry_with_parsed.published_parsed.tm_hour = 12
        entry_with_parsed.published_parsed.tm_min = 0
        entry_with_parsed.published_parsed.tm_sec = 0
        entry_with_parsed.published_parsed.tm_wday = 0
        entry_with_parsed.published_parsed.tm_yday = 1
        entry_with_parsed.published_parsed.tm_isdst = 0
        
        # Mock other attributes as None
        for attr in ['updated_parsed', 'created_parsed', 'published', 'updated', 'date', 'dc_date', 'pubDate']:
            setattr(entry_with_parsed, attr, None)
        
        result = parse_date_enhanced(entry_with_parsed)
        assert result is not None
        assert "2024" in result
        
        # Mock entry with string date
        entry_with_string = Mock()
        entry_with_string.published = "Mon, 01 Jan 2024 12:00:00 +0000"
        
        # Mock other attributes as None
        for attr in ['published_parsed', 'updated_parsed', 'created_parsed', 'updated', 'date', 'dc_date', 'pubDate']:
            setattr(entry_with_string, attr, None)
        
        result = parse_date_enhanced(entry_with_string)
        assert result is not None
        assert "2024" in result
        
        # Mock entry with no date fields
        entry_no_date = Mock()
        for attr in ['published_parsed', 'updated_parsed', 'created_parsed', 'published', 'updated', 'date', 'dc_date', 'pubDate']:
            setattr(entry_no_date, attr, None)
        
        result = parse_date_enhanced(entry_no_date)
        assert result is not None  # Should return current time as fallback
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Test with specific datetime
        test_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = format_timestamp(test_date)
        assert "2024-01-01T12:00:00" in result
        
        # Test with None (should use current time)
        result = format_timestamp(None)
        assert result is not None
        assert len(result) > 0
    
    def test_is_recent(self):
        """Test recent date checking."""
        # Test with recent date
        recent_date = datetime.now(timezone.utc)
        recent_iso = recent_date.isoformat()
        assert is_recent(recent_iso, days=7) is True
        
        # Test with old date
        old_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        old_iso = old_date.isoformat()
        assert is_recent(old_iso, days=7) is False
        
        # Test with invalid date
        assert is_recent("invalid-date", days=7) is False
        assert is_recent(None, days=7) is False
        
        # Test with different day thresholds
        week_old = datetime.now(timezone.utc).replace(day=datetime.now().day - 5)
        week_old_iso = week_old.isoformat()
        assert is_recent(week_old_iso, days=7) is True
        assert is_recent(week_old_iso, days=3) is False


class TestUtilsIntegration:
    """Integration tests for utility functions."""
    
    def test_content_and_date_processing_pipeline(self):
        """Test the complete content and date processing pipeline."""
        # Mock a complete feed entry
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.published = "Mon, 01 Jan 2024 12:00:00 +0000"
        mock_entry.description = "<p>This is a <strong>test</strong> description.</p>"
        mock_entry.content = [{"value": "<div>This is the <em>main content</em>.</div>"}]
        
        # Set other attributes to None
        for attr in ['published_parsed', 'updated_parsed', 'created_parsed', 'updated', 'date', 'dc_date', 'pubDate']:
            setattr(mock_entry, attr, None)
        
        # Process the entry
        content = extract_content_from_entry({"content": [{"value": mock_entry.content[0]["value"]}]})
        clean_content = clean_html_content(content)
        date_result = parse_date_enhanced(mock_entry)
        
        assert clean_content == "This is the main content."
        assert "2024" in date_result
        
        # Test that the date is considered old
        assert is_recent(date_result, days=7) is False


if __name__ == "__main__":
    pytest.main([__file__])
