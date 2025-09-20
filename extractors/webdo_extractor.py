"""
Webdo RSS extractor

Parses https://www.webdo.tn/fr/feed/ and returns a normalized list of entries with fields:
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

WEBDO_FEED_URL = "https://www.webdo.tn/fr/feed/"

def extract(url: str = WEBDO_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Webdo RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Webdo feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        
        # Handle description (could be in different fields)
        description = ''
        if hasattr(entry, 'description'):
            description = clean_html_content(entry.description)
        elif hasattr(entry, 'summary'):
            description = clean_html_content(entry.summary)
        
        # Handle publication date
        pub_date = entry.get('published', '') or entry.get('pubDate', '') or entry.get('updated', '')
        
        # Handle content (could be in different fields)
        content = ''
        if hasattr(entry, 'content'):
            # If multiple content entries, take the first one
            if entry.content:
                content = clean_html_content(entry.content[0].value)
        elif hasattr(entry, 'content:encoded'):
            content = clean_html_content(entry.get('content:encoded', ''))
        elif hasattr(entry, 'summary_detail'):
            content = clean_html_content(entry.summary_detail.value)
        
        # If content is empty but description exists, use description
        if not content and description:
            content = description
        
        results.append({
            'title': title,
            'link': link,
            'description': description,
            'pub_date': pub_date,
            'content': content
        })
    
    return results


def clean_html_content(text):
    """Remove HTML tags and clean the text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse HTML content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove unwanted elements (social media buttons, scripts, styles, etc.)
    for element in soup.find_all(['script', 'style', 'a', 'div', 'span', 'class']):
        if 'a2a_button' in str(element.get('class', [])):
            element.decompose()
    
    # Get clean text
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities
    clean_text = html.unescape(clean_text)
    
    # Remove extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text
