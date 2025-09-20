"""
RTCI RSS extractor

Parses https://www.rtci.tn/articles/rss and returns a normalized list of entries with fields:
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

RTCI_FEED_URL = "https://www.rtci.tn/articles/rss"


def extract(url: str = RTCI_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the RTCI RSS feed.

    Args:
        url: The RSS feed URL. Defaults to RTCI feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract fields with fallbacks for missing data
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Extract content from multiple possible sources
        content_text = ''
        
        # First try to get description
        description = clean_html_content(entry.get('description', ''))
        if description:
            content_text = description
        
        # If no description or it's empty, try other content fields
        if not content_text:
            if hasattr(entry, 'content'):
                content_text = clean_html_content(entry.content[0].value if entry.content else '')
            elif hasattr(entry, 'summary'):
                content_text = clean_html_content(entry.summary)
        
        # If still no content, use title as fallback
        if not content_text:
            content_text = title
        
        # Ensure both description and content have the same text
        description = content_text
        
        # Create dictionary with extracted data
        item_data = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "content": content_text
        }
        
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and clean unwanted content using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace and clean up
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

 
