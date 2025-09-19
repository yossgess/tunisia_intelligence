import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import html
import logging

logger = logging.getLogger(__name__)

def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content by removing unwanted tags and normalizing whitespace.
    
    Args:
        html_content: Raw HTML content as string
        
    Returns:
        Cleaned text content
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        
        # Normalize whitespace and clean up
        text = ' '.join(text.split())
        text = html.unescape(text)
        
        return text
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {e}")
        # Fallback to simple cleaning
        text = re.sub(r'<[^>]+>', ' ', str(html_content))
        text = ' '.join(text.split())
        return text

def extract_content_from_entry(entry: Dict[str, Any]) -> str:
    """
    Extract content from a feed entry with multiple fallbacks.
    
    Args:
        entry: Dictionary containing feed entry data
        
    Returns:
        Extracted content as string
    """
    content_fields = [
        'content',
        'summary',
        'description',
        'subtitle',
        'summary_detail',
        'content:encoded',
    ]
    
    for field in content_fields:
        if field in entry and entry[field]:
            if isinstance(entry[field], list):
                # Handle case where field contains multiple content items
                return ' '.join([str(item.get('value', '')) for item in entry[field] if item])
            else:
                return str(entry[field])
    
    return ""

def extract_media_info(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract media information from a feed entry.
    
    Args:
        entry: Dictionary containing feed entry data
        
    Returns:
        Dictionary with media information or None if no media found
    """
    media_info = {}
    
    # Check for media:content (RSS 2.0)
    if 'media_content' in entry and entry['media_content']:
        media_info['media'] = entry['media_content']
    
    # Check for enclosures
    if 'enclosures' in entry and entry['enclosures']:
        media_info['enclosures'] = entry['enclosures']
    
    # Check for media:thumbnail (Yahoo Media RSS)
    if 'media_thumbnail' in entry and entry['media_thumbnail']:
        media_info['thumbnail'] = entry['media_thumbnail']
    
    # Check for itunes:image (iTunes Podcast)
    if 'itunes_image' in entry and entry['itunes_image']:
        media_info['itunes_image'] = entry['itunes_image']
    
    return media_info if media_info else None
