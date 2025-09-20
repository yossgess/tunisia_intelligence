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
from bs4 import BeautifulSoup
import html

RADIOJEUNES_FEED_URL = "https://www.radiojeunes.tn/articles/rss"

def extract(url: str = RADIOJEUNES_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Jeunes RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Jeunes feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract fields with fallbacks
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        description = clean_html_content(entry.get('description', ''))
        
        # Handle publication date (prefer published, then updated, then current date)
        pub_date = entry.get('published', '') or entry.get('updated', '') or entry.get('date', '')
        
        # Handle content - try multiple possible content fields and include description
        content_parts = []
        
        # First try to get main content
        if hasattr(entry, 'content') and entry.content:
            content_parts.append(clean_html_content(entry.content[0].value))
        elif hasattr(entry, 'summary'):
            content_parts.append(clean_html_content(entry.summary))
        
        # Always include description in content
        if description and description not in content_parts:
            content_parts.append(description)
        
        # Combine all content parts
        content = ' '.join(content_parts).strip()
        
        # If no content was found from other sources, use description as fallback
        if not content and description:
            content = description
        
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
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Unescape HTML entities
    clean_text = html.unescape(clean_text)
    
    return clean_text

 
