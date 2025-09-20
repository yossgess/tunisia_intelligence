"""
Leaders RSS extractor

Parses https://www.leaders.com.tn/rss and returns a normalized list of entries with fields:
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
import re

LEADERS_FEED_URL = "https://www.leaders.com.tn/rss"

def extract(url: str = LEADERS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Leaders RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Leaders feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    # Process each item in the feed
    for entry in feed.entries:
        # Get description content
        description = clean_html_content(entry.get('description', ''))
        
        # Get content - if not available, use description as fallback
        content = ''
        if entry.get('content'):
            content = clean_html_content(entry.get('content', [{}])[0].get('value', ''))
        else:
            content = description  # Use description as content
        
        item_data = {
            "title": clean_html_content(entry.get('title', '')),
            "link": entry.get('link', ''),
            "description": description,
            "pub_date": entry.get('published', entry.get('pubDate', '')),
            "content": content
        }
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and clean the text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Get clean text
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace and normalize
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text
