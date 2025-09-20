"""
Business News RSS extractor

Parses http://www.businessnews.com.tn/rss.xml and returns a normalized list of entries with fields:
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

BUSINESSNEWS_FEED_URL = "http://www.businessnews.com.tn/rss.xml"

def extract(url: str = BUSINESSNEWS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Business News RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Business News feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    try:
        # Handle HTTPS/HTTP URL issues using requests for better control
        import requests
        import ssl
        from urllib3.exceptions import InsecureRequestWarning
        import urllib3
        
        # Disable SSL warnings
        urllib3.disable_warnings(InsecureRequestWarning)
        
        original_url = url
        feed = None
        
        # Try different approaches in order
        methods = []
        
        if url.startswith('https://'):
            # Method 1: Try HTTP variant
            http_url = url.replace('https://', 'http://', 1)
            methods.append(('HTTP', http_url, {'verify': False}))
            
            # Method 2: Try HTTPS with SSL verification disabled
            methods.append(('HTTPS (no SSL verify)', url, {'verify': False}))
            
            # Method 3: Try original HTTPS
            methods.append(('HTTPS (default)', url, {}))
        else:
            # For HTTP URLs, just try normally
            methods.append(('HTTP', url, {}))
        
        for method_name, test_url, kwargs in methods:
            try:
                print(f"Business News: Trying {method_name}: {test_url}")
                
                # Use requests to fetch the content first
                response = requests.get(test_url, timeout=30, **kwargs)
                response.raise_for_status()
                
                # Parse the content with feedparser
                feed = feedparser.parse(response.content)
                url = test_url  # Use the working URL
                
                print(f"Business News: {method_name} successful - got {len(feed.entries) if hasattr(feed, 'entries') else 0} entries")
                break
                
            except Exception as e:
                print(f"Business News: {method_name} failed: {e}")
                continue
        
        if feed is None:
            print("Business News: All connection methods failed")
            return []
        
        # Handle parsing errors gracefully
        if feed.bozo:
            print(f"Business News feed parsing warning: {feed.bozo_exception}")
            # Continue processing if we have entries despite warnings
            if not feed.entries:
                print("Business News: No entries found due to parsing errors, returning empty list")
                return []
        
        if not hasattr(feed, 'entries') or not feed.entries:
            print("Business News: No entries found in feed")
            return []
        
        print(f"Business News: Successfully parsed {len(feed.entries)} entries from {url}")
        
    except Exception as e:
        print(f"Business News: Error parsing feed: {e}")
        return []
    
    results = []
    
    for entry in feed.entries:
        try:
            # Extract and clean each field
            title = clean_html_content(entry.get('title', ''))
            link = entry.get('link', '')
            
            # Skip entries without links
            if not link:
                continue
                
            description = clean_html_content(entry.get('description', ''))
            pub_date = entry.get('published', entry.get('pubDate', ''))
            
            # Handle content - try different possible content fields
            content = ''
            if hasattr(entry, 'content'):
                content = clean_html_content(entry.content[0].value if entry.content else '')
            elif hasattr(entry, 'summary'):
                content = clean_html_content(entry.summary)
            elif hasattr(entry, 'description'):
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
            
        except Exception as e:
            print(f"Business News: Error processing entry: {e}")
            continue
    
    print(f"Business News: Successfully extracted {len(results)} entries")
    return results


def clean_html_content(text):
    """Remove HTML tags and clean text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespace and normalize
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text
