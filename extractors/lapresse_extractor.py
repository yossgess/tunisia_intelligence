"""
La Presse RSS extractor

Parses https://lapresse.tn/feed/ and returns a normalized list of entries with fields:
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

LAPRESSE_FEED_URL = "https://lapresse.tn/feed/"


def extract(url: str = LAPRESSE_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the La Presse RSS feed.

    Args:
        url: The RSS feed URL. Defaults to La Presse feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract and clean each field
        item_data = {
            "title": clean_html_content(entry.get('title', '')),
            "link": entry.get('link', ''),
            "description": clean_html_content(entry.get('description', '')),
            "pub_date": entry.get('published', entry.get('pubDate', '')),
            "content": clean_html_content(entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '')
        }
        
        # If content is empty, try alternative content fields
        if not item_data['content']:
            item_data['content'] = clean_html_content(entry.get('summary', ''))
        
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and decode HTML entities"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities
    cleaned_text = html.unescape(cleaned_text)
    
    return cleaned_text
