"""
Radio Nationale RSS extractor

Parses https://www.radionationale.tn/articles/rss and returns a normalized list of entries with fields:
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

RADIONATIONALE_FEED_URL = "https://www.radionationale.tn/articles/rss"


def extract(url: str = RADIONATIONALE_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Nationale RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Radio Nationale feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        description = getattr(entry, 'description', '')
        pub_date = getattr(entry, 'published', getattr(entry, 'pubDate', ''))
        
        # Extract content - try multiple possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'summary'):
            content = entry.summary
        
        # Combine content with description if both exist
        if content and description:
            combined_content = f"{description} {content}"
        elif content:
            combined_content = content
        else:
            combined_content = description
        
        # Clean HTML and unwanted strings using BeautifulSoup
        title_clean = clean_html_content(title)
        description_clean = clean_html_content(description)
        content_clean = clean_html_content(combined_content)
        
        # Create result dictionary
        result = {
            "title": title_clean,
            "link": link,
            "description": description_clean,
            "pub_date": pub_date,
            "content": content_clean
        }
        
        results.append(result)
    
    return results


def clean_html_content(text):
    """
    Clean HTML content and extract plain text using BeautifulSoup
    """
    if not text:
        return ""
    
    # Decode HTML entities first
    text = html.unescape(text)
    
    # Use BeautifulSoup to extract text and clean HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get clean text
    clean_text = soup.get_text()
    
    # Clean up whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
