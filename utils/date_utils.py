from datetime import datetime, timezone, date
from typing import Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

def parse_date_enhanced(entry: Any) -> str:
    """
    Enhanced date parsing with multiple fallbacks.
    
    Args:
        entry: Feed entry object with potential date fields
        
    Returns:
        ISO 8601 formatted date string in UTC
    """
    date_fields = [
        ('published_parsed', 'Published parsed'),
        ('updated_parsed', 'Updated parsed'),
        ('created_parsed', 'Created parsed'),
        ('published', 'Published string'),
        ('updated', 'Updated string'),
        ('date', 'Date string'),
        ('dc_date', 'Dublin Core date'),
        ('pubDate', 'pubDate string')
    ]
    
    for field, description in date_fields:
        if not hasattr(entry, field):
            continue
            
        field_value = getattr(entry, field)
        if not field_value:
            continue
            
        try:
            # Handle parsed time tuples (time.struct_time)
            if field.endswith('_parsed') and hasattr(field_value, 'tm_year'):
                dt = datetime.fromtimestamp(mktime(field_value))
                return dt.replace(tzinfo=timezone.utc).isoformat()
                
            # Handle string dates
            elif isinstance(field_value, str):
                dt = parse_date_string(field_value)
                if dt:
                    return dt.isoformat()
                    
        except Exception as e:
            logger.debug(f"Date parsing failed for {field} ({description}): {e}")
            continue
    
    # Fallback: current time in UTC
    logger.warning("No valid date found, using current time")
    return datetime.now(timezone.utc).isoformat()

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in various formats into a datetime object.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats to try
    date_formats = [
        # RSS/Atom formats
        '%a, %d %b %Y %H:%M:%S %z',  # RFC 822
        '%Y-%m-%dT%H:%M:%S%z',        # ISO 8601 with timezone
        '%Y-%m-%dT%H:%M:%S.%f%z',     # ISO 8601 with microseconds and timezone
        '%Y-%m-%d %H:%M:%S',           # SQL format
        '%Y-%m-%d',                    # Just date
        
        # Common web formats
        '%d %b %Y %H:%M:%S %Z',
        '%d %B %Y %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
    ]
    
    # Try each format
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # If timezone is not set, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    # Try to clean and parse with dateutil as last resort
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except (ImportError, ValueError):
        pass
    
    return None

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format a datetime object to ISO format string.
    
    Args:
        timestamp: Datetime object (defaults to now)
        
    Returns:
        ISO formatted string
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return timestamp.isoformat()

def is_recent(timestamp: str, days: int = 7) -> bool:
    """
    Check if a timestamp is within the last N days.
    
    Args:
        timestamp: ISO formatted timestamp string
        days: Number of days to check against
        
    Returns:
        True if the timestamp is within the last N days
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        delta = datetime.now(timezone.utc) - dt
        return delta.days <= days
    except (ValueError, TypeError):
        return False
