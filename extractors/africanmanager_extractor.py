"""
AfricanManager RSS extractor

Parses https://africanmanager.com/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description)
"""
from __future__ import annotations

from typing import List, Dict
from .utils import extract_standard_fields

def extract(url: str = "https://africanmanager.com/feed/") -> List[Dict[str, str]]:
    """
    Extract news from African Manager RSS feed.
    
    Args:
        url: URL of the RSS feed
        
    Returns:
        List of dictionaries containing news items with title, link, description, pub_date, and content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    for entry in feed.entries:
        # Extract standard fields using the utility function
        item = extract_standard_fields(entry)
        results.append(item)
    
    return results
