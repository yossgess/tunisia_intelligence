"""
Radio Monastir RSS extractor

Parses https://www.radiomonastir.tn/articles/rss and returns a normalized list of entries with fields:
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

RADIOMONASTIR_FEED_URL = "https://www.radiomonastir.tn/articles/rss"

def extract(url: str = RADIOMONASTIR_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Monastir RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Monastir feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = get_clean_text(entry.get('title', ''))
        link = entry.get('link', '')
        description = get_clean_text(entry.get('description', ''))
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Extract content - combine all available content sources
        content_parts = []
        
        # Add description content first
        if description and description != title:
            content_parts.append(description)
        
        # Add other content sources if available
        if hasattr(entry, 'content'):
            content_text = get_clean_text(entry.content[0].value)
            if content_text and content_text != description and content_text != title:
                content_parts.append(content_text)
        
        elif hasattr(entry, 'content_encoded'):
            content_text = get_clean_text(entry.content_encoded)
            if content_text and content_text != description and content_text != title:
                content_parts.append(content_text)
        
        elif hasattr(entry, 'summary_detail') and hasattr(entry.summary_detail, 'value'):
            content_text = get_clean_text(entry.summary_detail.value)
            if content_text and content_text != description and content_text != title:
                content_parts.append(content_text)
        
        elif hasattr(entry, 'summary'):
            content_text = get_clean_text(entry.summary)
            if content_text and content_text != description and content_text != title:
                content_parts.append(content_text)
        
        # Combine all content parts
        if content_parts:
            content = ' '.join(content_parts)
        else:
            content = description  # Fallback to description
        
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


def get_clean_text(html_content):
    """
    Clean HTML content and extract plain text using BeautifulSoup
    """
    if not html_content:
        return ""
    
    # Decode HTML entities first
    decoded_content = html.unescape(str(html_content))
    
    # Parse with BeautifulSoup and get text
    soup = BeautifulSoup(decoded_content, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

 
