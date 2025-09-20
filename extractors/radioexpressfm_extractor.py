"""
Radio Express FM RSS extractor

Parses https://radioexpressfm.com/fr/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped; tries to extract the post line if present)
- pub_date (published/pubDate when available)
- content (main text, attempts to capture text before the WordPress "[...]" truncation)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import html
import re

RADIOEXPRESS_FEED_URL = "https://radioexpressfm.com/fr/feed/"

def extract(url: str = RADIOEXPRESS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Radio Express FM RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Radio Express FM feed.
        
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    extracted_data = []
    
    for entry in feed.entries:
        # Extract basic fields
        title = clean_html_content(entry.get('title', ''))
        link = entry.get('link', '')
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Get the raw description (HTML content)
        raw_description = entry.get('description', '')
        
        # Extract description and content from the HTML description field
        description, content = extract_description_and_content(raw_description)
        
        # Create result dictionary
        result = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "content": content
        }
        
        extracted_data.append(result)
    
    return extracted_data


def clean_html_content(text):
    """
    Remove HTML tags and clean text content using BeautifulSoup
    """
    if not text:
        return ""
    
    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities and clean up whitespace
    clean_text = html.unescape(clean_text)
    clean_text = ' '.join(clean_text.split())
    
    return clean_text


def extract_description_and_content(text):
    """
    Extract description (after "The post") and content (before "[...]") from HTML text
    """
    # Parse the HTML content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Extract all text content
    full_text = soup.get_text(separator=' ', strip=True)
    
    # Extract content before "[...]" - look for the main content
    content_match = re.search(r'^(.*?)\s*\[\.\.\.\]', full_text)
    content = content_match.group(1).strip() if content_match else full_text
    
    # Extract description from the "The post" line
    description_match = re.search(r'The post\s+(.*?)\s+appeared first', full_text)
    if description_match:
        description = description_match.group(1).strip()
    else:
        # Fallback: if no "The post" pattern found, try to get the title from the link
        post_link = soup.find('a', rel='nofollow')
        if post_link:
            description = post_link.get_text(strip=True)
        else:
            # Final fallback: use first part of content
            words = content.split()
            description = ' '.join(words[:min(10, len(words))]) + ('...' if len(words) > 10 else '')
    
    return description, content

 
