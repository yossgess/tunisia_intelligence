"""
Realites RSS extractor

Parses https://realites.com.tn/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import html

REALITES_FEED_URL = "https://realites.com.tn/feed/"

def extract(url: str = REALITES_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Realites RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Realites feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        pub_date = getattr(entry, 'published', getattr(entry, 'pubDate', ''))
        
        # Extract and clean description
        description = getattr(entry, 'description', '')
        description = clean_html_content(description)
        
        # Extract and clean content (try multiple possible fields)
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'content_encoded'):
            content = entry.content_encoded
        elif hasattr(entry, 'summary'):
            content = entry.summary
        
        content = clean_html_content(content)
        
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
    """
    Clean HTML content using BeautifulSoup and handle HTML entities
    """
    if not text:
        return ""
    
    # Decode HTML entities first
    text = html.unescape(text)
    
    # Use BeautifulSoup to extract text content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Get clean text without HTML tags
    clean_text = soup.get_text(separator=' ', strip=False)
    
    # Remove extra whitespace but preserve paragraph structure
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
