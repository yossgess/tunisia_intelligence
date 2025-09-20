"""
Al Chourouk RSS extractor

Parses https://www.alchourouk.com/rss and returns a normalized list of entries with fields:
- title
- link
- description (tries to extract the main text; avoids author/date boilerplate)
- pub_date (published/pubDate when available)
- content (uses cleaned description as content if no richer content is present)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import html
import re

ALCHOUROUK_FEED_URL = "https://www.alchourouk.com/rss"

def extract(url: str = ALCHOUROUK_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Al Chourouk RSS feed.
    
    Args:
        url: URL of the RSS feed. Defaults to Al Chourouk's main feed.
        
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
        
        # Extract and clean description - remove author and date information
        description = getattr(entry, 'description', '')
        description = clean_description(description)
        
        # For content, use the cleaned description (since content field may not be available)
        content = description
        
        # Create result dictionary
        result = {
            "title": clean_text(title),
            "link": clean_text(link),
            "description": description,
            "pub_date": clean_text(pub_date),
            "content": content
        }
        
        results.append(result)
    
    return results


def clean_description(description):
    """
    Clean description by extracting only the main text content
    and removing author and date information
    """
    if not description:
        return ""
    
    try:
        # Parse HTML content
        soup = BeautifulSoup(description, 'html.parser')
        
        # Find the span with property="schema:name" which contains the main title
        title_span = soup.find('span', {'property': 'schema:name'})
        
        if title_span:
            # Extract text from the title span
            main_text = title_span.get_text(strip=True)
            return clean_text(main_text)
        else:
            # Fallback: get all text and try to extract the main content
            all_text = soup.get_text(separator=' ', strip=True)
            # Remove author and date information (simple pattern matching)
            # This regex removes everything after the main title text
            cleaned_text = re.sub(r'(\s+\w+_\w+\s+.*|\s+ven\s+\d{2}/\d{2}/\d{4}.*)', '', all_text)
            return clean_text(cleaned_text)
            
    except Exception as e:
        print(f"Error cleaning description: {e}")
        return clean_text(description)


def clean_text(text):
    """
    Clean plain text by unescaping HTML entities and normalizing whitespace
    """
    if not text:
        return ""
    
    try:
        # Unescape HTML entities
        text = html.unescape(text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    except Exception as e:
        print(f"Error cleaning text: {e}")
        return str(text)
