"""
Webmanagercenter RSS extractor

Parses https://www.webmanagercenter.com/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped, boilerplate removed)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description; boilerplate removed)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import re
import feedparser
from bs4 import BeautifulSoup
from .utils import clean_html_to_text, extract_standard_fields

WMC_FEED_URL = "https://www.webmanagercenter.com/feed/"

def _remove_boilerplate(text: str) -> str:
    """Remove recurring footer boilerplate seen on WMC articles."""
    if not text:
        return ""

    patterns = [
        r"L'article.*est apparu en premier sur WMC\..*$",
        r"L'article.*est apparu en premier sur WMC.*$",
        r"est apparu en premier sur WMC\..*$",
        r"est apparu en premier sur WMC.*$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove trailing leftover French quote markers or ellipsis that sometimes remain
    text = re.sub(r"\[…\]$|\.\.\.$|…$", "", text).strip()
    text = re.sub(r"\[\…\]$", "", text).strip()
    return text

def _get_best_content(entry: Any) -> str:
    """Get the best content from the entry, with boilerplate removed."""
    # Try to get content from various fields in order of preference
    content_sources = [
        lambda: getattr(entry, "content", [{}])[0].get("value", "") if hasattr(entry, "content") and entry.content else "",
        lambda: getattr(entry, "summary", ""),
        lambda: getattr(entry, "content_encoded", ""),
        lambda: getattr(entry, "description", "")
    ]
    
    for source in content_sources:
        try:
            content = source()
            if content:
                cleaned_content = clean_html_to_text(content)
                if cleaned_content:
                    return _remove_boilerplate(cleaned_content)
        except Exception:
            continue
    
    return ""

def extract(url: str = WMC_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Webmanagercenter RSS feed.
    
    This extractor handles special cases for Webmanagercenter's feed format,
    including removing their standard footer boilerplate text.
    
    Args:
        url: The RSS feed URL. Defaults to Webmanagercenter's feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    feed = feedparser.parse(url)
    results: List[Dict[str, str]] = []
    
    for entry in feed.entries:
        # First get standard fields
        item = extract_standard_fields(entry)
        
        # Get the best content with boilerplate removed
        best_content = _get_best_content(entry)
        if best_content:
            item["content"] = best_content
            
            # If the content is the same as description after cleaning, use title as description
            if item.get("content") == item.get("description"):
                item["description"] = item["title"]
        
        # Clean up the description as well
        if "description" in item:
            item["description"] = _remove_boilerplate(item["description"])
        
        results.append(item)
    
    return results

 
