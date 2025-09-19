"""
Utility functions shared across RSS feed extractors.
"""
import re
import html
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime

def clean_html_to_text(html_content: str) -> str:
    """
    Clean HTML content by removing tags, normalizing whitespace, and unescaping HTML entities.
    
    Args:
        html_content: Raw HTML content as string
        
    Returns:
        Cleaned plain text content
    """
    if not html_content:
        return ""
        
    # Unescape HTML entities first
    text = html.unescape(html_content)
    
    # Parse with BeautifulSoup to handle HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()
    
    # Get text and normalize whitespace
    text = soup.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    
    return text

def extract_content(entry: Dict[str, Any]) -> str:
    """
    Extract content from a feed entry, trying multiple possible content fields.
    
    Args:
        entry: Feed entry dictionary from feedparser
        
    Returns:
        Extracted content as plain text
    """
    # Try different possible content fields in order of preference
    content = None
    
    # Try content[0].value (common in Atom feeds)
    if hasattr(entry, 'content') and entry.content:
        content = entry.content[0].value
    # Try description (common in RSS)
    elif hasattr(entry, 'description') and entry.description:
        content = entry.description
    # Try summary (common in Atom)
    elif hasattr(entry, 'summary') and entry.summary:
        content = entry.summary
    
    return clean_html_to_text(content) if content else ""

def format_date(date_str: str) -> str:
    """
    Format a date string to a consistent format.
    
    Args:
        date_str: Date string in various possible formats
        
    Returns:
        Formatted date string in ISO 8601 format (YYYY-MM-DD HH:MM:SS)
    """
    if not date_str:
        return ""
        
    try:
        # Try parsing with dateutil.parser if available
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ImportError:
            # Fallback to datetime's strptime with common formats
            for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                       "%a, %d %b %Y %H:%M:%S %Z",
                       "%Y-%m-%dT%H:%M:%S%z",
                       "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        return date_str
    except Exception:
        return date_str

def extract_standard_fields(entry: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract standard fields from a feed entry with consistent formatting.
    
    Args:
        entry: Feed entry dictionary from feedparser
        
    Returns:
        Dictionary with standardized fields (title, link, description, pub_date, content)
    """
    # Extract and clean title
    title_raw = getattr(entry, 'title', '')
    title = ' '.join(html.unescape(title_raw).split()) if title_raw else ""
    
    # Extract link
    link = getattr(entry, 'link', '')
    
    # Extract and clean description
    description_raw = getattr(entry, 'description', '')
    description = clean_html_to_text(description_raw)
    
    # Extract and format publication date
    pub_date_raw = getattr(entry, 'published', getattr(entry, 'updated', ''))
    pub_date = format_date(pub_date_raw)
    
    # Extract and clean content
    content = extract_content(entry)
    
    return {
        "title": title,
        "link": link,
        "description": description,
        "pub_date": pub_date,
        "content": content
    }
