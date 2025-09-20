"""
Radio Med Tunisie RSS extractor

Parses https://radiomedtunisie.com/feed/ and returns a normalized list of entries with fields:
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

RADIOMED_FEED_URL = "https://radiomedtunisie.com/feed/"

def extract(url: str = RADIOMED_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Med Tunisie RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Med Tunisie feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    # List to store extracted items
    extracted_items = []
    
    # Process each item in the feed
    for entry in feed.entries:
        item_data = {}
        
        # Extract title
        item_data['title'] = clean_html_content(entry.get('title', ''))
        
        # Extract link
        item_data['link'] = entry.get('link', '')
        
        # Extract description
        description = entry.get('description', '')
        if not description and hasattr(entry, 'summary'):
            description = entry.summary
        item_data['description'] = clean_html_content(description)
        
        # Extract publication date
        item_data['pub_date'] = entry.get('published', entry.get('pubDate', ''))
        
        # Extract content - try multiple possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'content_encoded'):
            content = entry.content_encoded
        elif hasattr(entry, 'summary_detail'):
            content = entry.summary_detail.value
        
        item_data['content'] = clean_html_content(content)
        
        extracted_items.append(item_data)
    
    return extracted_items


def clean_html_content(text):
    """
    Clean HTML content using BeautifulSoup and return plain text
    """
    if not text:
        return ""
    
    # Decode HTML entities first
    decoded_text = html.unescape(text)
    
    # Parse with BeautifulSoup to extract text only
    soup = BeautifulSoup(decoded_text, 'html.parser')
    
    # Get clean text without HTML tags
    clean_text = soup.get_text(separator=' ', strip=False)
    
    # Clean up extra whitespace but preserve meaningful spacing
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
