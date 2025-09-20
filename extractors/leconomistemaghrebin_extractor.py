"""
Leconomiste Maghrebin RSS extractor

Parses https://www.leconomistemaghrebin.com/feed/ and returns a normalized list of entries with fields:
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

LECONOMISTE_MAGHREBIN_FEED_URL = "https://www.leconomistemaghrebin.com/feed/"

def extract(url: str = LECONOMISTE_MAGHREBIN_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Leconomiste Maghrebin RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Leconomiste Maghrebin feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract the required fields
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        
        # Handle description (could be in different fields)
        description = clean_html_content(entry.get('description', ''))
        if not description:
            description = clean_html_content(entry.get('summary', ''))
        
        # Handle publication date
        pub_date = entry.get('published', '')
        if not pub_date:
            pub_date = entry.get('pubDate', '')
        
        # Handle content (could be in different fields)
        content = ''
        if hasattr(entry, 'content'):
            content = clean_html_content(entry.content[0].value)
        elif hasattr(entry, 'content_encoded'):
            content = clean_html_content(entry.content_encoded)
        elif hasattr(entry, 'description'):
            # Fallback to description if no specific content field
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
    """Remove HTML tags and clean the text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Get clean text
    clean_text = soup.get_text(separator=' ', strip=False)
    
    # Clean up any remaining HTML entities and extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)  # Replace multiple spaces with single space
    clean_text = clean_text.strip()
    
    return clean_text

 
