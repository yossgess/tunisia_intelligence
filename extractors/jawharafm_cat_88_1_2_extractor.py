"""
Jawhara FM (category 88/1/2) RSS extractor

Parses https://www.jawharafm.net/ar/rss/showRss/88/1/2 and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from .utils import extract_standard_fields

JAWHARAFM_CAT_88_1_2_FEED_URL = "https://www.jawharafm.net/ar/rss/showRss/88/1/2"

def extract(url: str = JAWHARAFM_CAT_88_1_2_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Jawhara FM category RSS feed.
    
    Args:
        url: URL of the RSS feed. Defaults to Jawhara FM category 88/1/2 feed.
        
    Returns:
        List of dictionaries containing article data with standardized fields.
    """
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    
    for entry in feed.entries:
        # Extract standard fields using the utility function
        item = extract_standard_fields(entry)
        results.append(item)
    
    return results

 
