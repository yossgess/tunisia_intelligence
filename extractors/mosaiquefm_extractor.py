"""
MosaiqueFM RSS extractor

Parses https://www.mosaiquefm.net/ar/rss and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description)
"""
from __future__ import annotations

from typing import List, Dict
from .utils import extract_standard_fields

def extract(url: str = "https://www.mosaiquefm.net/ar/rss") -> List[Dict[str, str]]:
    """
    Extract news from MosaiqueFM Arabic RSS feed.
    
    Args:
        url: URL of the RSS feed (default: https://www.mosaiquefm.net/ar/rss)
        
    Returns:
        List of dictionaries containing news items with title, link, description, pub_date, and content
    """
    import feedparser
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # First try with feedparser's built-in handling
        feed = feedparser.parse(url)
        
        # If no entries found, try with direct requests and force UTF-8
        if not feed.entries:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/xml, text/xml, */*',
                'Accept-Charset': 'utf-8',
                'Accept-Encoding': 'gzip, deflate',
            })
            response.encoding = 'utf-8'
            feed = feedparser.parse(response.content)
        
        # If still no entries, try with BeautifulSoup
        if not feed.entries:
            response = requests.get(url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'xml')
            
            # Convert the soup back to string and parse with feedparser
            feed = feedparser.parse(str(soup))
        
        results = []
        for entry in feed.entries:
            try:
                # Extract standard fields using the utility function
                item = extract_standard_fields(entry)
                
                # Ensure all string fields are properly encoded
                for key, value in item.items():
                    if isinstance(value, str):
                        # Remove any problematic characters
                        item[key] = value.encode('utf-8', 'ignore').decode('utf-8')
                
                results.append(item)
            except Exception as e:
                print(f"Error processing entry: {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"Error in MosaiqueFM extractor: {e}")
        return []
