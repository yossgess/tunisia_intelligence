"""
Unified extractor that routes to the appropriate extractor based on the feed URL.
"""
from __future__ import annotations

from typing import List, Dict, Optional, Callable
from urllib.parse import urlparse
import logging
import feedparser
import traceback

# Import all extractors
from . import EXTRACTOR_REGISTRY, DOMAIN_REGISTRY

logger = logging.getLogger(__name__)

class UnifiedExtractor:
    """
    A unified extractor that routes to the appropriate extractor based on the feed URL.
    """
    
    def __init__(self):
        self.extractor_registry = EXTRACTOR_REGISTRY
        self.domain_registry = DOMAIN_REGISTRY
    
    def get_extractor(self, url: str) -> Optional[Callable]:
        """
        Get the appropriate extractor for the given URL.
        
        Args:
            url: The URL of the RSS feed
            
        Returns:
            The extractor function or None if no matching extractor is found
        """
        if not url or not isinstance(url, str):
            logger.warning(f"Invalid URL provided: {url}")
            return None
            
        logger.debug(f"Looking for extractor for URL: {url}")
        
        # Try exact match first
        if url in self.extractor_registry:
            extractor = self.extractor_registry[url]
            logger.debug(f"Found exact match in extractor registry: {extractor.__name__ if hasattr(extractor, '__name__') else str(extractor)}")
            return extractor
        
        # Try domain match
        try:
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                logger.warning(f"Could not parse domain from URL: {url}")
                return None
                
            domain = parsed_url.netloc.lower()
            # Normalize: drop leading www.
            domain = domain[4:] if domain.startswith("www.") else domain
            
            logger.debug(f"Looking for domain match for: {domain}")
            
            # Try direct domain match
            if domain in self.domain_registry:
                extractor = self.domain_registry[domain]
                logger.debug(f"Found domain match in registry: {extractor.__name__ if hasattr(extractor, '__name__') else str(extractor)}")
                return extractor
                
            # Try partial domain match (for subdomains)
            for dom, extractor in self.domain_registry.items():
                if domain.endswith(dom) and domain != dom:
                    logger.debug(f"Found partial domain match for {domain} with {dom}")
                    return extractor
                    
        except Exception as e:
            logger.error(f"Error finding extractor for URL {url}: {str(e)}", exc_info=True)
        
        logger.warning(f"No extractor found for URL: {url}")
        return None
    
    def extract(self, url: str, max_retries: int = 2, initial_timeout: int = 60) -> List[Dict[str, str]]:
        """
        Extract entries from the given RSS feed URL with retry logic.
        
        Args:
            url: The URL of the RSS feed
            max_retries: Maximum number of retry attempts (default: 2)
            initial_timeout: Initial timeout in seconds (default: 60)
            
        Returns:
            List of dictionaries containing the extracted entries
            
        Raises:
            ValueError: If no extractor is found or all retry attempts fail
        """
        logger.debug(f"Looking up extractor for URL: {url}")
        extractor = self.get_extractor(url)
        
        if not extractor:
            error_msg = f"No extractor found for URL: {url}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"Found extractor: {extractor.__name__ if hasattr(extractor, '__name__') else str(extractor)}")
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                # Calculate timeout with exponential backoff
                timeout = initial_timeout * (2 ** attempt)  # 60s, 120s, 240s, etc.
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} with {timeout}s timeout for {url}")
                
                # Use a threading-based timeout solution that works on Windows
                from threading import Thread, Event
                from queue import Queue, Empty
                import traceback
                
                def run_with_timeout(timeout_sec, func, *args, **kwargs):
                    """Run a function with a timeout using threads."""
                    result_queue = Queue()
                    stop_event = Event()
                    
                    def wrapper():
                        try:
                            if stop_event.is_set():
                                return
                            result = func(*args, **kwargs)
                            if not stop_event.is_set():
                                result_queue.put((True, result))
                        except Exception as e:
                            if not stop_event.is_set():
                                result_queue.put((False, e))
                    
                    thread = Thread(target=wrapper, daemon=True)
                    thread.start()
                    
                    try:
                        # Wait for the result with timeout
                        success, result = result_queue.get(timeout=timeout_sec)
                        stop_event.set()  # Signal thread to stop
                        if not success:
                            raise result
                        return result
                    except Empty:
                        stop_event.set()  # Signal thread to stop
                        thread.join(1)  # Give thread a moment to finish
                        raise TimeoutError(f"Extraction timed out after {timeout_sec} seconds")
                    finally:
                        if thread.is_alive():
                            thread.join(1)  # Give thread a moment to finish
                
                # Run the extractor with timeout
                entries = run_with_timeout(timeout, extractor, url)
                
                if not isinstance(entries, list):
                    logger.warning(f"Extractor did not return a list of entries for {url}")
                    return []
                    
                logger.info(f"Successfully extracted {len(entries)} entries from {url}")
                return entries
                
            except TimeoutError as te:
                last_exception = te
                logger.warning(f"Attempt {attempt + 1} failed: {str(te)}")
                if attempt < max_retries:
                    logger.info(f"Retrying {url} (attempt {attempt + 2}/{max_retries + 1})...")
                continue
                
            except Exception as e:
                last_exception = e
                logger.error(f"Error extracting from {url} (attempt {attempt + 1}): {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                if attempt < max_retries:
                    logger.info(f"Retrying {url} (attempt {attempt + 2}/{max_retries + 1})...")
                continue
        
        # If we get here, all attempts failed
        error_msg = f"Failed to extract from {url} after {max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)} (last error)"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Create a singleton instance for easy import
unified_extractor = UnifiedExtractor()

def extract(url: str) -> List[Dict[str, str]]:
    """
    Extract entries from the given RSS feed URL using the unified extractor.
    
    This is a convenience function that uses the singleton instance.
    
    Args:
        url: The URL of the RSS feed
        
    Returns:
        List of dictionaries containing the extracted entries
    """
    return unified_extractor.extract(url)
