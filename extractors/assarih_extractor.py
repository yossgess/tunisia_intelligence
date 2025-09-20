"""
Assarih RSS extractor

Parses http://assarih.com/feed/ and returns a normalized list of entries with fields:
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

ASSARIH_FEED_URL = "http://assarih.com/feed/"

def extract(url: str = ASSARIH_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Assarih RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Assarih feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        pub_date = getattr(entry, 'published', getattr(entry, 'pubDate', ''))
        
        # Extract and clean description
        description = getattr(entry, 'description', '')
        description = clean_html_content(description)
        
        # Extract content (try multiple possible fields)
        content = getattr(entry, 'content', [{}])[0].get('value', '') if hasattr(entry, 'content') else ''
        if not content:
            content = getattr(entry, 'summary', '')
        content = clean_html_content(content)
        
        # Create entry dictionary
        entry_data = {
            "title": clean_text(title),
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "content": content
        }
        
        extracted_data.append(entry_data)
    
    return extracted_data


def clean_html_content(html_content):
    """
    Clean HTML content using BeautifulSoup to extract plain text
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted tags but keep text content
        for element in soup(['script', 'style', 'img', 'iframe', 'form', 'input', 'button']):
            element.decompose()
        
        # Get clean text
        clean_text = soup.get_text(separator=' ', strip=True)
        
        # Decode HTML entities and clean up whitespace
        clean_text = html.unescape(clean_text)
        clean_text = ' '.join(clean_text.split())
        
        return clean_text
        
    except Exception as e:
        print(f"Error cleaning HTML content: {e}")
        # Fallback: return original content with basic cleaning
        return clean_text(html_content)


def clean_text(text):
    """
    Basic text cleaning for non-HTML fields
    """
    if not text:
        return ""
    
    text = html.unescape(text)
    text = ' '.join(text.split())
    return text

 
