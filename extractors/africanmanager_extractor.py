"""
AfricanManager RSS extractor

Parses https://africanmanager.com/feed/ and returns a normalized list of entries with fields:
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
import re

def extract(url: str = "https://africanmanager.com/feed/") -> List[Dict[str, str]]:
    """
    Extract news from African Manager RSS feed.
    
    Args:
        url: URL of the RSS feed
        
    Returns:
        List of dictionaries containing news items with title, link, description, pub_date, and content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    # Check if feed was parsed successfully
    if feed.bozo:
        print(f"Error parsing feed: {feed.bozo_exception}")
        return []
    
    extracted_data = []
    
    # Extract data from each item
    for entry in feed.entries:
        # Get description content
        description_content = clean_html_content(entry.get('description', ''))
        
        # Get main content (if available)
        main_content = ''
        if entry.get('content'):
            main_content = clean_html_content(entry.get('content', [{}])[0].get('value', ''))
        
        # Combine description with main content if both exist
        full_content = description_content
        if main_content and main_content != description_content:
            full_content = f"{description_content} {main_content}"
        
        item_data = {
            "title": clean_html_content(entry.get('title', '')),
            "link": entry.get('link', ''),
            "description": description_content,
            "pub_date": entry.get('published', entry.get('pubDate', '')),
            "content": full_content
        }
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and clean the text content"""
    if text is None:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Clean up any remaining HTML entities and special characters
    clean_text = re.sub(r'\s+', ' ', clean_text)  # Replace multiple spaces with single space
    clean_text = clean_text.replace('&#8217;', "'")  # Replace HTML apostrophe
    clean_text = clean_text.replace('&amp;', '&')  # Replace HTML ampersand
    clean_text = clean_text.replace('&lt;', '<')  # Replace HTML less than
    clean_text = clean_text.replace('&gt;', '>')  # Replace HTML greater than
    clean_text = clean_text.replace('&quot;', '"')  # Replace HTML quotes
    clean_text = clean_text.replace('&#8230;', '...')  # Replace HTML ellipsis
    
    return clean_text.strip()
