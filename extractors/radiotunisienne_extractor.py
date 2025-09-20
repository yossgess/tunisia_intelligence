"""
Radio Tunisienne RSS extractor

Parses https://www.radiotunisienne.tn/articles/rss and returns a normalized list of entries with fields:
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

RADIOTUNISIENNE_FEED_URL = "https://www.radiotunisienne.tn/articles/rss"

def extract(url: str = RADIOTUNISIENNE_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Tunisienne RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Tunisienne feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    # Extract information from each item
    for entry in feed.entries:
        # Get the raw values before cleaning
        raw_title = entry.get('title', '')
        raw_description = entry.get('description', '')
        
        # Clean the content
        clean_title = clean_html_content(raw_title)
        clean_description = clean_html_content(raw_description)
        
        # For content field, try multiple sources and use description if content is empty or same as title
        content_candidates = []
        
        # Try content field first
        if entry.get('content'):
            content_value = clean_html_content(entry.get('content', [{}])[0].get('value', ''))
            if content_value and content_value != clean_title:
                content_candidates.append(content_value)
        
        # Try description as content (if it's different from title)
        if clean_description and clean_description != clean_title:
            content_candidates.append(clean_description)
        
        # Try summary field
        if entry.get('summary'):
            summary_value = clean_html_content(entry.get('summary', ''))
            if summary_value and summary_value != clean_title:
                content_candidates.append(summary_value)
        
        # Use the first available content candidate, or fallback to description
        final_content = content_candidates[0] if content_candidates else clean_description
        
        # For description, use title if content was taken from description
        final_description = clean_title if final_content == clean_description else clean_description
        
        item_data = {
            "title": clean_title,
            "link": entry.get('link', ''),
            "description": final_description,
            "pub_date": entry.get('published', entry.get('pubDate', '')),
            "content": final_content
        }
        results.append(item_data)
    
    return results


def clean_html_content(text):
    """Remove HTML tags and clean the text content"""
    if not text:
        return ""
    
    # Parse HTML content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Get clean text without HTML tags
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities
    clean_text = html.unescape(clean_text)
    
    return clean_text

 
