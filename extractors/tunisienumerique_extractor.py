"""
Tunisie Numerique RSS extractor

Parses https://www.tunisienumerique.com/feed-actualites-tunisie.xml and returns a normalized list of entries with fields:
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

TUNISIE_NUMERIQUE_FEED_URL = "https://www.tunisienumerique.com/feed-actualites-tunisie.xml"


def extract(url: str = TUNISIE_NUMERIQUE_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Tunisie Numerique RSS feed.

    Args:
        url: The RSS feed URL. Defaults to Tunisie Numerique feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    # Parse the RSS feed
    feed = feedparser.parse(url)
    
    results = []
    
    for entry in feed.entries:
        # Extract fields with proper handling for lists and dictionaries
        title = clean_html_content(get_field_value(entry, ['title']))
        link = get_field_value(entry, ['link'])
        
        # Get description from multiple possible fields
        description = clean_html_content(get_field_value(entry, ['description', 'summary', 'subtitle']))
        
        # Get content from multiple possible fields - handle content:encoded specifically
        content = ""
        if 'content' in entry:
            content = clean_html_content(entry['content'])
        elif 'content:encoded' in entry:
            content = clean_html_content(entry['content:encoded'])
        else:
            content = description  # Fallback
        
        # Get publication date from multiple possible fields
        pub_date = get_field_value(entry, ['published', 'pubDate', 'dc:date', 'updated'])
        
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
    """Remove HTML tags and clean the text content"""
    if not text:
        return ""
    
    # Handle case where text might be a list
    if isinstance(text, list):
        # If it's a list, take the first element or join them
        if text and isinstance(text[0], dict) and 'value' in text[0]:
            text = text[0]['value']
        else:
            text = ' '.join([str(item) for item in text])
    
    # Handle case where text might be a dictionary
    if isinstance(text, dict):
        if 'value' in text:
            text = text['value']
        else:
            text = str(text)
    
    # Parse with BeautifulSoup and get text
    soup = BeautifulSoup(str(text), 'html.parser')
    cleaned_text = soup.get_text(separator=' ', strip=True)
    
    # Clean up any remaining HTML entities and extra whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def get_field_value(entry, field_names):
    """Safely get field value from entry, handling lists, dicts and multiple field names"""
    for field_name in field_names:
        if field_name in entry:
            value = entry[field_name]
            
            # Handle lists
            if isinstance(value, list):
                if value:
                    # If list contains dictionaries with 'value' key
                    if isinstance(value[0], dict) and 'value' in value[0]:
                        return value[0]['value']
                    else:
                        return ' '.join([str(item) for item in value])
                else:
                    return ""
            
            # Handle dictionaries
            elif isinstance(value, dict):
                if 'value' in value:
                    return value['value']
                else:
                    return str(value)
            
            # Handle strings and other types
            else:
                return value
    return ""
