"""
Radio Express FM RSS extractor

Parses https://radioexpressfm.com/fr/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped; tries to extract the post line if present)
- pub_date (published/pubDate when available)
- content (main text, attempts to capture text before the WordPress "[...]" truncation)
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import feedparser
from bs4 import BeautifulSoup
import re
from .utils import extract_standard_fields

RADIOEXPRESS_FEED_URL = "https://radioexpressfm.com/fr/feed/"

def _extract_wp_metadata(description: str) -> Tuple[str, str]:
    """Extract WordPress-specific metadata from the description.
    
    Returns:
        Tuple of (description, content) where both are cleaned text versions
    """
    if not description:
        return "", ""
        
    soup = BeautifulSoup(description, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True)
    
    # Extract content before WordPress truncation
    content_match = re.search(r"^(.*?)\s*\[\.\.\.\]", full_text)
    content = content_match.group(1).strip() if content_match else full_text
    
    # Try to find a meaningful description
    desc_match = re.search(r"The post\s+(.*?)\s+appeared first", full_text, flags=re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        # Fallback to first 12 words of content
        words = content.split()
        description = " ".join(words[:12]) + ("..." if len(words) > 12 else "")
    
    return description, content

def extract(url: str = RADIOEXPRESS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Express FM RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Express FM feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    
    for entry in feed.entries:
        # First try to use the standard extractor
        item = extract_standard_fields(entry)
        
        # For WordPress-specific handling, process the description
        if 'description' in item and 'content' in item and item['content'] == item['description']:
            wp_desc, wp_content = _extract_wp_metadata(entry.get('description', ''))
            if wp_desc and wp_content:
                item['description'] = wp_desc
                item['content'] = wp_content
        
        results.append(item)
    
    return results

 
