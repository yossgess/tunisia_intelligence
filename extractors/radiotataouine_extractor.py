"""
Radio Tataouine RSS extractor

Parses https://www.radiotataouine.tn/articles/rss and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import html

RADIOTATAOUINE_FEED_URL = "https://www.radiotataouine.tn/articles/rss"


def extract(url: str = RADIOTATAOUINE_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Tataouine RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Radio Tataouine feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract and clean each field
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        description = clean_html_content(entry.get('description', ''))
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Try to get content from different possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = clean_html_content(entry.content[0].value if entry.content else '')
        elif hasattr(entry, 'summary'):
            content = clean_html_content(entry.summary)
        elif hasattr(entry, 'description'):
            content = clean_html_content(entry.description)
        
        # Create result dictionary
        result = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "content": content
        }
        
        results.append(result)
    
    return results


def clean_html_content(text):
    """Remove HTML tags and clean the text content"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities and clean up whitespace
    cleaned_text = html.unescape(cleaned_text)
    cleaned_text = ' '.join(cleaned_text.split())
    
    return cleaned_text

 
