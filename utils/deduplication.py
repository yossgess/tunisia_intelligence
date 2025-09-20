"""
Content deduplication utilities for Tunisia Intelligence RSS scraper.

This module provides functionality to detect and prevent duplicate content
from being stored in the database.
"""
import hashlib
import logging
from typing import Optional, Set, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """Handles content deduplication using various strategies."""
    
    def __init__(self):
        self._seen_hashes: Set[str] = set()
        self._seen_urls: Set[str] = set()
        self._seen_titles: Set[str] = set()
    
    def generate_content_hash(self, title: str, content: str) -> str:
        """
        Generate a hash for content deduplication.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            SHA256 hash of normalized content
        """
        # Normalize content for hashing
        normalized_title = title.strip().lower()
        normalized_content = content.strip().lower()
        
        # Combine title and content
        combined = f"{normalized_title}|{normalized_content}"
        
        # Generate hash
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def generate_url_hash(self, url: str) -> str:
        """
        Generate a hash for URL deduplication.
        
        Args:
            url: Article URL
            
        Returns:
            SHA256 hash of normalized URL
        """
        # Normalize URL (remove query parameters, fragments, etc.)
        normalized_url = url.split('?')[0].split('#')[0].strip().lower()
        return hashlib.sha256(normalized_url.encode('utf-8')).hexdigest()
    
    def generate_title_hash(self, title: str) -> str:
        """
        Generate a hash for title deduplication.
        
        Args:
            title: Article title
            
        Returns:
            SHA256 hash of normalized title
        """
        normalized_title = title.strip().lower()
        return hashlib.sha256(normalized_title.encode('utf-8')).hexdigest()
    
    def is_duplicate_content(self, title: str, content: str) -> bool:
        """
        Check if content is a duplicate based on title and content.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            True if content is duplicate, False otherwise
        """
        content_hash = self.generate_content_hash(title, content)
        
        if content_hash in self._seen_hashes:
            logger.debug(f"Duplicate content detected: {title[:50]}...")
            return True
        
        self._seen_hashes.add(content_hash)
        return False
    
    def is_duplicate_url(self, url: str) -> bool:
        """
        Check if URL is a duplicate.
        
        Args:
            url: Article URL
            
        Returns:
            True if URL is duplicate, False otherwise
        """
        url_hash = self.generate_url_hash(url)
        
        if url_hash in self._seen_urls:
            logger.debug(f"Duplicate URL detected: {url}")
            return True
        
        self._seen_urls.add(url_hash)
        return False
    
    def is_duplicate_title(self, title: str) -> bool:
        """
        Check if title is a duplicate.
        
        Args:
            title: Article title
            
        Returns:
            True if title is duplicate, False otherwise
        """
        title_hash = self.generate_title_hash(title)
        
        if title_hash in self._seen_titles:
            logger.debug(f"Duplicate title detected: {title}")
            return True
        
        self._seen_titles.add(title_hash)
        return False
    
    def is_duplicate(self, article_data: Dict[str, Any], 
                    check_content: bool = True, 
                    check_url: bool = True, 
                    check_title: bool = False) -> bool:
        """
        Comprehensive duplicate check using multiple strategies.
        
        Args:
            article_data: Dictionary containing article data
            check_content: Whether to check content duplication
            check_url: Whether to check URL duplication
            check_title: Whether to check title duplication
            
        Returns:
            True if article is duplicate, False otherwise
        """
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        url = article_data.get('link', article_data.get('url', ''))
        
        # Check URL duplication (most reliable)
        if check_url and url and self.is_duplicate_url(url):
            return True
        
        # Check content duplication
        if check_content and title and content and self.is_duplicate_content(title, content):
            return True
        
        # Check title duplication (least reliable, use with caution)
        if check_title and title and self.is_duplicate_title(title):
            return True
        
        return False
    
    def clear_cache(self):
        """Clear the deduplication cache."""
        self._seen_hashes.clear()
        self._seen_urls.clear()
        self._seen_titles.clear()
        logger.info("Deduplication cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the deduplication cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'content_hashes': len(self._seen_hashes),
            'url_hashes': len(self._seen_urls),
            'title_hashes': len(self._seen_titles),
            'total_items': len(self._seen_hashes) + len(self._seen_urls) + len(self._seen_titles)
        }


class DatabaseDeduplicator:
    """Handles deduplication against database records."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._url_cache: Set[str] = set()
        self._cache_loaded = False
    
    def _load_existing_urls(self):
        """Load existing URLs from database into cache."""
        if self._cache_loaded:
            return
        
        try:
            # This would require a method to get existing URLs from database
            # For now, we'll implement a basic version
            logger.info("Loading existing URLs from database...")
            # TODO: Implement database query to get existing URLs
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._url_cache)} existing URLs")
        except Exception as e:
            logger.error(f"Error loading existing URLs: {e}")
    
    def is_duplicate_in_database(self, url: str) -> bool:
        """
        Check if URL already exists in database.
        
        Args:
            url: Article URL to check
            
        Returns:
            True if URL exists in database, False otherwise
        """
        self._load_existing_urls()
        
        normalized_url = url.split('?')[0].split('#')[0].strip().lower()
        return normalized_url in self._url_cache
    
    def add_to_cache(self, url: str):
        """Add URL to the cache after successful insertion."""
        normalized_url = url.split('?')[0].split('#')[0].strip().lower()
        self._url_cache.add(normalized_url)


# Global deduplicator instances
_content_deduplicator: Optional[ContentDeduplicator] = None
_database_deduplicator: Optional[DatabaseDeduplicator] = None


def get_content_deduplicator() -> ContentDeduplicator:
    """Get the global content deduplicator instance."""
    global _content_deduplicator
    if _content_deduplicator is None:
        _content_deduplicator = ContentDeduplicator()
    return _content_deduplicator


def get_database_deduplicator(db_manager) -> DatabaseDeduplicator:
    """Get the global database deduplicator instance."""
    global _database_deduplicator
    if _database_deduplicator is None:
        _database_deduplicator = DatabaseDeduplicator(db_manager)
    return _database_deduplicator


def is_duplicate_article(article_data: Dict[str, Any], 
                        db_manager=None,
                        check_content: bool = True,
                        check_url: bool = True,
                        check_database: bool = True) -> bool:
    """
    Convenience function to check if an article is duplicate.
    
    Args:
        article_data: Dictionary containing article data
        db_manager: Database manager instance (optional)
        check_content: Whether to check content duplication
        check_url: Whether to check URL duplication
        check_database: Whether to check against database
        
    Returns:
        True if article is duplicate, False otherwise
    """
    # Check in-memory deduplication
    content_dup = get_content_deduplicator()
    if content_dup.is_duplicate(article_data, check_content=check_content, check_url=check_url):
        return True
    
    # Check database deduplication
    if check_database and db_manager:
        db_dup = get_database_deduplicator(db_manager)
        url = article_data.get('link', article_data.get('url', ''))
        if url and db_dup.is_duplicate_in_database(url):
            return True
    
    return False


def clear_deduplication_cache():
    """Clear all deduplication caches."""
    global _content_deduplicator, _database_deduplicator
    
    if _content_deduplicator:
        _content_deduplicator.clear_cache()
    
    if _database_deduplicator:
        _database_deduplicator._url_cache.clear()
        _database_deduplicator._cache_loaded = False
    
    logger.info("All deduplication caches cleared")
