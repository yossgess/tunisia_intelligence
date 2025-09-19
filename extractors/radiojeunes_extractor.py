"""
Radio Jeunes RSS extractor

Parses https://www.radiojeunes.tn/articles/rss and returns a normalized list of entries with fields:
- title
- link
- description (tries to avoid duplicating the content; falls back to cleaned description)
- pub_date (published/pubDate when available)
- content (prefers entry.content; else summary/description; avoids using exact title)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from .utils import clean_html_to_text, extract_standard_fields

RADIOJEUNES_FEED_URL = "https://www.radiojeunes.tn/articles/rss"

def _get_best_content(entry: dict, title: str) -> str:
    """Determine the best content for the entry, avoiding duplicates of the title.
    
    Args:
        entry: The RSS entry dictionary
        title: The cleaned title of the entry
        
    Returns:
        The best available content string
    """
    # 1) Try to get content from the content module
    if entry.get("content"):
        try:
            value = entry.get("content", [{}])[0].get("value", "")
            if value:
                content_val = clean_html_to_text(value)
                if content_val and content_val != title:
                    return content_val
        except Exception:
            pass
    
    # 2) Try to get content from summary
    if entry.get("summary"):
        summary_val = clean_html_to_text(entry.get("summary", ""))
        if summary_val and summary_val != title:
            return summary_val
    
    # 3) Fall back to description if different from title
    description = clean_html_to_text(entry.get("description", ""))
    return description if description != title else ""

def extract(url: str = RADIOJEUNES_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Jeunes RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Jeunes feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    
    for entry in feed.entries:
        # First get standard fields
        item = extract_standard_fields(entry)
        
        # Get the best content, avoiding duplicates of the title
        best_content = _get_best_content(entry, item["title"])
        
        # If we found better content, update the item
        if best_content and best_content != item["description"]:
            item["content"] = best_content
        
        # If content is same as description, set description to title to avoid duplication
        if item.get("content") == item.get("description"):
            item["description"] = item["title"]
        
        results.append(item)
    
    return results

 
