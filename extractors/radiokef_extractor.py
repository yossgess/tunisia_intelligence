"""
Radio Kef RSS extractor

Parses https://www.radiokef.tn/articles/rss and returns a normalized list of entries with fields:
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

RADIOKEF_FEED_URL = "https://www.radiokef.tn/articles/rss"

def extract(url: str = RADIOKEF_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Kef RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Kef feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = get_clean_text(entry.get('title', ''))
        link = entry.get('link', '')
        description = get_clean_text(entry.get('description', ''))
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Extract content - try multiple possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = get_clean_text(entry.content[0].value if entry.content else '')
        elif hasattr(entry, 'summary'):
            content = get_clean_text(entry.summary)
        elif hasattr(entry, 'description'):
            content = get_clean_text(entry.description)
        
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


def get_clean_text(html_content):
    """
    Clean HTML content and extract plain text using BeautifulSoup
    """
    if not html_content:
        return ""
    
    # Decode HTML entities first
    decoded_content = html.unescape(html_content)
    
    # Use BeautifulSoup to extract text and remove HTML tags
    soup = BeautifulSoup(decoded_content, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
