"""
Al Chourouk RSS extractor

Parses https://www.alchourouk.com/rss and returns a normalized list of entries with fields:
- title
- link
- description (tries to extract the main text; avoids author/date boilerplate)
- pub_date (published/pubDate when available)
- content (uses cleaned description as content if no richer content is present)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from .utils import extract_standard_fields

ALCHOUROUK_FEED_URL = "https://www.alchourouk.com/rss"

def extract(url: str = ALCHOUROUK_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Al Chourouk RSS feed.
    
    Args:
        url: URL of the RSS feed. Defaults to Al Chourouk's main feed.
        
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
