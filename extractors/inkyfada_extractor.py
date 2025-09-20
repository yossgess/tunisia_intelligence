"""
Inkyfada RSS extractor

Parses https://inkyfada.com/en/feed/ and returns a normalized list of entries with fields:
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

INKYFADA_FEED_URL = "https://inkyfada.com/en/feed/"


def extract(url: str = INKYFADA_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Inkyfada RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Inkyfada feed.
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
        
        # Handle description (could be in different fields)
        description = clean_html_content(entry.get('description', ''))
        if not description:
            description = clean_html_content(entry.get('summary', ''))
        
        # Handle publication date
        pub_date = entry.get('published', '')
        if not pub_date:
            pub_date = entry.get('updated', '')
        if not pub_date:
            pub_date = entry.get('dc_date', '')
        
        # Handle content (could be in different fields)
        content = ''
        if hasattr(entry, 'content'):
            content = clean_html_content(entry.content[0].value if entry.content else '')
        elif hasattr(entry, 'content_encoded'):
            content = clean_html_content(entry.content_encoded)
        elif hasattr(entry, 'summary'):
            content = clean_html_content(entry.summary)
        
        # Create data dictionary
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
    """Remove HTML tags and clean the text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()
    
    # Get text and clean it
    text = soup.get_text()
    
    # Clean up whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
