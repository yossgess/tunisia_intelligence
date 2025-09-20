"""
Nessma RSS extractor

Parses https://www.nessma.tv/fr/rss/news/7 and returns a normalized list of entries with fields:
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

NESSMA_FEED_URL = "https://www.nessma.tv/fr/rss/news/7"

def extract(url: str = NESSMA_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Nessma RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Nessma feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract fields
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        description = clean_html_content(entry.get('description', ''))
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Try to get content from different possible fields
        content = ''
        if hasattr(entry, 'content'):
            content = clean_html_content(entry.content[0].value if entry.content else '')
        elif hasattr(entry, 'summary'):
            content = clean_html_content(entry.summary)
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


def clean_html_content(text):
    """Remove HTML tags and clean the text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup and get clean text
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Clean up any remaining HTML entities and extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean_text = clean_text.replace('&quot;', '"').replace('&#039;', "'")
    
    return clean_text.strip()
