"""
FTDES RSS extractor

Parses https://ftdes.net/feed/ and returns a normalized list of entries with fields:
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

FTDES_FEED_URL = "https://ftdes.net/feed/"


def extract(url: str = FTDES_FEED_URL) -> List[Dict[str, str]]:
    """Extract and clean entries from the FTDES RSS feed.

    Args:
        url: The RSS feed URL. Defaults to FTDES feed.
    Returns:
        A list of dictionaries with keys: title, link, description, pub_date, content
    """
    try:
        # Simple, direct approach - just try to get whatever we can
        import requests
        
        print("FTDES: Using simple direct approach")
        
        # Try to get the raw content first
        try:
            response = requests.get(url, timeout=30, verify=False)
            raw_content = response.text
            print(f"FTDES: Got raw content, length: {len(raw_content)}")
            
            # Try to extract entries manually using BeautifulSoup
            from bs4 import BeautifulSoup
            
            # Parse as HTML (more forgiving than XML)
            soup = BeautifulSoup(raw_content, 'html.parser')
            
            # Look for RSS items
            items = soup.find_all('item')
            print(f"FTDES: Found {len(items)} items in raw content")
            
            if len(items) > 0:
                # Manually create feed-like entries
                manual_entries = []
                for item in items:
                    entry = {}
                    
                    # Extract basic fields
                    title_tag = item.find('title')
                    entry['title'] = title_tag.get_text() if title_tag else ''
                    
                    link_tag = item.find('link')
                    entry['link'] = link_tag.get_text() if link_tag else ''
                    
                    desc_tag = item.find('description')
                    entry['description'] = desc_tag.get_text() if desc_tag else ''
                    
                    pub_tag = item.find('pubdate') or item.find('pubDate')
                    entry['published'] = pub_tag.get_text() if pub_tag else ''
                    
                    # Look for content
                    content_tag = item.find('content:encoded') or item.find('content')
                    entry['content'] = content_tag.get_text() if content_tag else entry['description']
                    
                    manual_entries.append(entry)
                
                print(f"FTDES: Manually extracted {len(manual_entries)} entries")
                
                # Convert to our expected format
                results = []
                for entry in manual_entries:
                    result = {
                        "title": clean_html_content(entry.get('title', '')),
                        "link": entry.get('link', ''),
                        "description": clean_html_content(entry.get('description', '')),
                        "pub_date": entry.get('published', ''),
                        "content": clean_html_content(entry.get('content', ''))
                    }
                    
                    # Only add if we have a link
                    if result['link']:
                        results.append(result)
                
                print(f"FTDES: Successfully extracted {len(results)} valid entries")
                return results
            
        except Exception as e:
            print(f"FTDES: Manual extraction failed: {e}")
        
        # Fallback to feedparser if manual extraction fails
        print("FTDES: Falling back to feedparser")
        feed = feedparser.parse(url)
        
        if hasattr(feed, 'entries') and len(feed.entries) > 0:
            print(f"FTDES: Feedparser found {len(feed.entries)} entries")
        else:
            print("FTDES: No entries found with any method")
            return []
        
    except Exception as e:
        print(f"FTDES: All methods failed: {e}")
        return []
    
    results = []
    
    for entry in feed.entries:
        try:
            # Extract basic fields
            title = clean_html_content(entry.get('title', ''))
            link = entry.get('link', '')
            
            # Skip entries without links
            if not link:
                continue
            
            # Handle description (may contain HTML)
            description = clean_html_content(entry.get('description', ''))
            
            # Handle publication date
            pub_date = entry.get('published', entry.get('pubDate', ''))
            
            # Handle content - try different possible content fields
            content = ''
            if hasattr(entry, 'content'):
                content = clean_html_content(entry.content[0].value)
            elif hasattr(entry, 'summary'):
                content = clean_html_content(entry.summary)
            elif hasattr(entry, 'description'):
                content = clean_html_content(entry.description)
            
            # For some feeds, content might be in other fields
            if not content:
                for key in entry.keys():
                    if 'content' in key.lower() and isinstance(entry[key], str):
                        content = clean_html_content(entry[key])
                        break
            
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
            print(f"FTDES: Error processing entry: {e}")
            continue
    
    print(f"FTDES: Successfully extracted {len(results)} entries")
    return results


def clean_html_content(text):
    """Remove HTML tags and clean up whitespace"""
    if not text:
        return ""
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
