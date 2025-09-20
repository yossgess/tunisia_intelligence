"""
Business News RSS extractor

Parses https://www.businessnews.com.tn/rss and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
import requests
import ssl
from urllib3.exceptions import InsecureRequestWarning
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .utils import extract_standard_fields

# Suppress only the single InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Configure logging
logger = logging.getLogger(__name__)

BUSINESSNEWS_FEED_URL = "https://www.businessnews.com.tn/rss"

def fetch_feed_content(url: str) -> Optional[bytes]:
    """Fetch feed content with SSL verification disabled.
    
    Args:
        url: The URL to fetch
        
    Returns:
        The response content or None if the request failed
    """
    try:
        # First try with SSL verification
        response = requests.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/xml, text/xml, */*',
            },
            verify=True,  # First try with SSL verification
            timeout=30
        )
        return response.content
    except (requests.exceptions.SSLError, requests.exceptions.RequestException) as e:
        logger.warning(f"SSL error with {url}, trying without verification: {e}")
        try:
            # If SSL verification fails, try without it
            response = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/xml, text/xml, */*',
                },
                verify=False,  # Disable SSL verification
                timeout=30
            )
            return response.content
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

def extract(url: str = BUSINESSNEWS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Business News RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Business News feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    results: List[Dict[str, str]] = []
    
    try:
        # First try with feedparser
        feed = feedparser.parse(url)
        
        # If no entries, try with direct requests
        if not feed.entries:
            content = fetch_feed_content(url)
            if content:
                feed = feedparser.parse(content)
        
        # If still no entries, try with BeautifulSoup
        if not feed.entries and 'content' in locals():
            try:
                soup = BeautifulSoup(content, 'xml')
                feed = feedparser.parse(str(soup))
            except Exception as e:
                logger.error(f"Error parsing with BeautifulSoup: {e}")
        
        # Process entries
        for entry in feed.entries:
            try:
                # Extract standard fields using the utility function
                item = extract_standard_fields(entry)
                
                # Ensure all string fields are properly encoded
                for key, value in item.items():
                    if isinstance(value, str):
                        item[key] = value.encode('utf-8', 'ignore').decode('utf-8')
                
                results.append(item)
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in Business News extractor: {e}")
    
    return results
