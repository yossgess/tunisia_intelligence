"""
Jawhara FM (category 88/1/4) RSS extractor

Parses https://www.jawharafm.net/ar/rss/showRss/88/1/4 and returns a normalized list of entries with fields:
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

JAWHARAFM_CAT_88_1_4_FEED_URL = "https://www.jawharafm.net/ar/rss/showRss/88/1/4"

def extract(url: str = JAWHARAFM_CAT_88_1_4_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Jawhara FM category 88/1/4 RSS feed.
    
    Args:
        url: URL of the RSS feed. Defaults to Jawhara FM category 88/1/4 feed.
        
    Returns:
        List of dictionaries containing article data with standardized fields.
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        pub_date = getattr(entry, 'published', getattr(entry, 'pubDate', ''))
        
        # Extract and clean description
        description = getattr(entry, 'description', '')
        description_clean = clean_html_content(description)
        
        # Extract and clean content (try multiple possible fields)
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'summary'):
            content = entry.summary
        content_clean = clean_html_content(content)
        
        # If content is empty but description has content, use description
        if not content_clean.strip() and description_clean.strip():
            content_clean = description_clean
        
        result = {
            "title": clean_text(title),
            "link": clean_text(link),
            "description": description_clean,
            "pub_date": clean_text(pub_date),
            "content": content_clean
        }
        
        results.append(result)
    
    return results


def clean_html_content(html_content):
    """
    Clean HTML content using BeautifulSoup to remove all HTML tags
    while preserving the text content
    """
    if not html_content:
        return ""
    
    # Unescape HTML entities first
    unescaped_content = html.unescape(html_content)
    
    # Parse with BeautifulSoup and extract text
    soup = BeautifulSoup(unescaped_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "head", "title", "meta", "[document]"]):
        script.decompose()
    
    # Get text and clean up
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def clean_text(text):
    """
    Basic text cleaning (remove extra whitespace, unescape HTML entities)
    """
    if not text:
        return ""
    
    cleaned = html.unescape(text).strip()
    return cleaned
