"""
Oasis FM RSS extractor

Parses https://oasis-fm.net/feed/ and returns a normalized list of entries with fields:
- title
- link
- description (HTML stripped)
- pub_date (published/pubDate when available)
- content (prefers entry.content HTML if present; falls back to summary/description)
"""
from __future__ import annotations

from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
import re

OASIS_FEED_URL = "https://oasis-fm.net/feed/"

def extract(url: str = OASIS_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the Oasis FM RSS feed.
    
    Args:
        url: The RSS feed URL. Defaults to Oasis FM feed.
        
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
        
        # Handle description - clean HTML content and remove boilerplate
        description = entry.get('description', '')
        cleaned_description = clean_html_content(description)
        cleaned_description = remove_boilerplate_text(cleaned_description)
        
        # Handle publication date
        pub_date = entry.get('published', entry.get('pubDate', ''))
        
        # Handle content - try different possible content fields
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'content_encoded'):
            content = entry.content_encoded
        elif hasattr(entry, 'summary'):
            content = entry.summary
        else:
            # Fallback to description if no content field found
            content = description
        
        # Extract actual article content by removing boilerplate
        cleaned_content = extract_article_content(content)
        
        # If content extraction failed, fall back to cleaned description
        if not cleaned_content or len(cleaned_content) < 20:
            cleaned_content = cleaned_description
        
        # Create data dictionary
        item_data = {
            "title": title,
            "link": link,
            "description": cleaned_description,
            "pub_date": pub_date,
            "content": cleaned_content
        }
        
        extracted_data.append(item_data)
    
    return extracted_data


def clean_html_content(text):
    """Remove HTML tags and clean unwanted content using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script, style, and other non-content elements
    for element in soup(["script", "style", "aside", "div", "span"]):
        element.decompose()
    
    # Get text and clean up
    clean_text = soup.get_text()
    
    # Remove extra whitespace and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text


def remove_boilerplate_text(text):
    """Remove WordPress boilerplate text from the content"""
    if not text:
        return ""
    
    # Patterns to remove WordPress boilerplate
    patterns = [
        r'The post.*?appeared first on.*?\.?$',
        r'ظهر أولاً على.*?\.?$',
        r'المصدر:.*?\.?$',
        r'Source:.*?\.?$',
        r'أوازيس أف أم\.?$',
        r'The post.*?first on.*?\.?$'
    ]
    
    # Remove each pattern
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up any trailing punctuation or whitespace
    text = re.sub(r'[\.\s]+$', '', text)
    text = text.strip()
    
    return text


def extract_article_content(content):
    """Extract the main article content by removing WordPress boilerplate"""
    if not content:
        return ""
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove common WordPress boilerplate patterns
    for element in soup.find_all(['p', 'div']):
        text = element.get_text().strip()
        # Remove elements that contain boilerplate text
        if any(phrase in text for phrase in ['The post', 'appeared first on', 'first on', 'Source:']):
            element.decompose()
        if any(phrase in text for phrase in ['أوازيس أف أم', 'المصدر:', 'ظهر أولاً على']):
            element.decompose()
    
    # Get clean text
    clean_content = soup.get_text()
    
    # Remove any remaining boilerplate
    clean_content = remove_boilerplate_text(clean_content)
    
    return clean_content

 
