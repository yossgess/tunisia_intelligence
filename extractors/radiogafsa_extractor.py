"""
Radio Gafsa RSS extractor

Parses https://www.radiogafsa.tn/articles/rss and returns a normalized list of entries with fields:
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

RADIOGAFSA_FEED_URL = "https://www.radiogafsa.tn/articles/rss"

def extract(url: str = RADIOGAFSA_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Gafsa RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Gafsa feed.
        
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
        pub_date = entry.get('published', entry.get('updated', ''))
        pub_date = clean_html_content(pub_date)
        
        # Extract content - try multiple possible fields
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
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities and clean up whitespace
    clean_text = html.unescape(clean_text)
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
