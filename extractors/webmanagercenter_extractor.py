"""
Webmanagercenter RSS extractor

Parses https://www.webmanagercenter.com/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped, boilerplate removed)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description; boilerplate removed)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import re

WMC_FEED_URL = "https://www.webmanagercenter.com/feed/"

def extract(url: str = WMC_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Webmanagercenter RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Webmanagercenter's feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = entry.get('title', '')
        link = entry.get('link', '')
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Clean description using BeautifulSoup
        description_html = entry.get('description', '')
        description_clean = clean_html(description_html)
        description_clean = remove_boilerplate(description_clean, title)
        
        # Extract content (try multiple possible fields)
        content_html = entry.get('content', [{}])[0].get('value', '') if 'content' in entry else ''
        if not content_html:
            content_html = entry.get('content:encoded', '')
        
        content_clean = clean_html(content_html)
        content_clean = remove_boilerplate(content_clean, title)
        
        # Create data dictionary
        item_data = {
            "title": title,
            "link": link,
            "description": description_clean,
            "pub_date": pub_date,
            "content": content_clean
        }
        
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html(html_content):
    """
    Clean HTML content using BeautifulSoup to extract text only
    """
    if not html_content:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags (script, style, etc.)
    for unwanted_tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        unwanted_tag.decompose()
    
    # Get clean text
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Clean up extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text


def remove_boilerplate(text, title):
    """
    Remove repetitive boilerplate text from the content
    """
    if not text:
        return ""
    
    # Pattern to match the repetitive boilerplate text
    patterns = [
        r"L'article.*est apparu en premier sur WMC\..*$",
        r"L'article.*est apparu en premier sur WMC.*$",
        r"est apparu en premier sur WMC\..*$",
        r"est apparu en premier sur WMC.*$"
    ]
    
    # Try each pattern to remove boilerplate
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Also remove any trailing "L'article" references that might be left
    text = re.sub(r"L'article.*$", '', text)
    
    # Clean up any extra whitespace created by the removal
    text = text.strip()
    
    # Remove any trailing ellipsis or incomplete sentences
    text = re.sub(r'\[…\]$|\.\.\.$|…$', '', text).strip()
    text = re.sub(r'\[\…\]$', '', text).strip()
    
    return text

 
