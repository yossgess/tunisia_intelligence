"""
Nawaat RSS extractor

Parses https://nawaat.org/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
import re
from bs4 import BeautifulSoup

NAWAAT_FEED_URL = "https://nawaat.org/feed/"


def extract(url: str = NAWAAT_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Nawaat RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Nawaat feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    feed = feedparser.parse(url)

    results: List[Dict[str, str]] = []
    for entry in feed.entries:
        # Extract fields exactly as in legacy code
        item_data = {
            "title": clean_text(entry.get('title', '')),
            "link": entry.get('link', ''),
            "description": clean_html(entry.get('description', '')),
            "pub_date": entry.get('published', ''),
            "content": clean_html(get_content(entry))
        }
        results.append(item_data)

    return results


def get_content(entry):
    """
    Extract content from RSS entry, prioritizing content module if available.
    
    Args:
        entry: A feedparser entry object
        
    Returns:
        str: The content text
    """
    # Try to get content from content module first
    if hasattr(entry, 'content'):
        for content in entry.content:
            if hasattr(content, 'value'):
                return content.value
    
    # Fallback to description if content is not available
    return entry.get('description', '')


def clean_html(html_text):
    """
    Remove HTML tags and clean the text.
    
    Args:
        html_text (str): Text containing HTML tags
        
    Returns:
        str: Clean text without HTML tags
    """
    if not html_text:
        return ""
    
    # Use BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(html_text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace and clean up
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text


def clean_text(text):
    """
    Basic text cleaning (remove extra whitespace, etc.)
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    return re.sub(r'\s+', ' ', text).strip()
