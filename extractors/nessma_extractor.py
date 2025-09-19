"""
Nessma RSS extractor

Parses https://www.nessma.tv/feed and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from .utils import extract_standard_fields

NESSMA_FEED_URL = "https://www.nessma.tv/feed"

def extract(url: str = NESSMA_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Nessma RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Nessma feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    feed = feedparser.parse(url)

    results: List[Dict[str, str]] = []
    for entry in feed.entries:
        # Extract standard fields using the utility function
        item = extract_standard_fields(entry)
        results.append(item)

    return results
