"""
Essahafa RSS extractor

Parses https://essahafa.tn/feed/ and returns a normalized list of entries with fields:
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

ESSAHAFA_FEED_URL = "https://essahafa.tn/feed/"

def extract(url: str = ESSAHAFA_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Essahafa RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Essahafa feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        
        # Extract description and clean it
        description = clean_html_content(entry.get('description', ''))
        
        # Extract publication date
        pub_date = entry.get('published', '') or entry.get('pubDate', '')
        
        # Extract content - try different possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = clean_html_content(entry.content[0].value if entry.content else '')
        elif hasattr(entry, 'summary'):
            content = clean_html_content(entry.summary)
        elif hasattr(entry, 'description'):
            content = clean_html_content(entry.description)
        
        # For some feeds, content might be in different namespaces
        if not content and hasattr(entry, 'content_encoded'):
            content = clean_html_content(entry.content_encoded)
        
        item_data = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "content": content
        }
        
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and clean the text content"""
    if not text:
        return ""
    
    # Parse HTML content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean it
    clean_text = soup.get_text()
    
    # Clean up whitespace and special characters
    clean_text = ' '.join(clean_text.split())
    clean_text = html.unescape(clean_text)
    
    return clean_text
