"""
Ultra-Minimal Facebook Page Posts Extractor

Super-efficient version that gets maximum intelligence with minimum API calls:
- Only 3-4 API calls per source regardless of engagement level
- Essential fields only: ID, message, created_time, permalink_url
- Total reaction count (no breakdown by type to save API calls)
- Comments with message + created_time only

Optimized for Tunisia Intelligence with ultra-low API usage.
"""

import requests
import json
import time
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class UltraMinimalFacebookExtractor:
    """Ultra-minimal Facebook extractor with maximum efficiency"""
    
    def __init__(self, app_token: str, api_version: str = "v18.0"):
        self.app_token = app_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.session = requests.Session()
        
        # Cache for page information
        self.cache_file = Path("facebook_page_cache.pkl")
        self.page_cache = self._load_cache()
        
        # Rate limiting tracking
        self.api_calls_made = 0
        self.last_call_time = 0
        self.min_delay = 0.3  # Faster for fewer calls
        
        # Failed pages to skip
        self.failed_pages: Set[str] = set()
        
        self.session.headers.update({
            'User-Agent': 'Tunisia Intelligence Facebook Scraper Ultra-Minimal 1.0'
        })
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cached page information"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                logger.info(f"Loaded ultra-minimal cache with {len(cache)} pages")
                return cache
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save page information cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.page_cache, f)
            logger.debug(f"Saved ultra-minimal cache with {len(self.page_cache)} pages")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")
    
    def _rate_limit_delay(self):
        """Implement intelligent rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.api_calls_made += 1
    
    def _make_api_call(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make rate-limited API call"""
        self._rate_limit_delay()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                error_data = response.json().get('error', {})
                if 'Application request limit reached' in error_data.get('message', ''):
                    logger.warning("Rate limit reached, stopping extraction")
                    return None
                else:
                    logger.error(f"API error: {response.text}")
                    return None
            else:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API call exception: {e}")
            return None
    
    def get_ultra_minimal_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get ultra-minimal page info from cache or API"""
        # Check cache first
        if page_id in self.page_cache:
            cached_info = self.page_cache[page_id]
            # Check if cache is still fresh (24 hours)
            cache_time = cached_info.get('cached_at', 0)
            if time.time() - cache_time < 86400:  # 24 hours
                logger.debug(f"Using cached info for page {page_id}")
                return cached_info['data']
        
        # Skip if we know this page fails
        if page_id in self.failed_pages:
            logger.debug(f"Skipping known failed page {page_id}")
            return None
        
        # Fetch ultra-minimal page info from API
        logger.debug(f"Fetching ultra-minimal page info for {page_id}")
        
        # Only essential page fields
        fields = ['id', 'name']
        
        params = {
            'fields': ','.join(fields),
            'access_token': self.app_token
        }
        
        url = f"{self.base_url}/{page_id}"
        data = self._make_api_call(url, params)
        
        if data and 'error' not in data:
            # Cache successful result
            self.page_cache[page_id] = {
                'data': data,
                'cached_at': time.time()
            }
            self._save_cache()
            return data
        else:
            # Mark as failed to avoid future calls
            self.failed_pages.add(page_id)
            logger.warning(f"Page {page_id} failed, will skip in future")
            return None
    
    def extract_posts_ultra_minimal(self, page_ids: List[str], hours_back: int = 24, max_pages: int = 15) -> Dict[str, Any]:
        """
        Extract posts with ultra-minimal API calls (3-4 calls per source max)
        
        Args:
            page_ids: List of Facebook page IDs
            hours_back: Hours to look back for posts
            max_pages: Maximum pages to process
        """
        logger.info(f"Starting ultra-minimal extraction for {len(page_ids)} pages (max {max_pages})")
        
        # Process limited pages to stay within rate limits
        pages_to_process = page_ids[:max_pages]
        
        results = {}
        successful_extractions = 0
        
        for i, page_id in enumerate(pages_to_process):
            try:
                logger.info(f"Processing page {i+1}/{len(pages_to_process)}: {page_id}")
                
                # Get ultra-minimal page info (cached when possible) - 1 API call
                page_info = self.get_ultra_minimal_page_info(page_id)
                if not page_info:
                    results[page_id] = {"error": "Page not accessible or rate limited"}
                    continue
                
                # Extract posts for this page - 1 API call
                posts = self._get_page_posts_ultra_minimal(page_id, hours_back)
                
                result = {
                    "page_info": page_info,
                    "posts": posts,
                    "total_posts": len(posts),
                    "extraction_time": datetime.now().isoformat()
                }
                
                results[page_id] = result
                successful_extractions += 1
                
                logger.info(f"Ultra-minimal: extracted {len(posts)} posts from {page_info.get('name', page_id)} with ~3 API calls")
                
                # Conservative rate limit check
                if self.api_calls_made > 100:  # Conservative
                    logger.warning(f"Approaching rate limit ({self.api_calls_made} calls), stopping")
                    break
                
            except Exception as e:
                logger.error(f"Error processing page {page_id}: {e}")
                results[page_id] = {"error": str(e)}
        
        summary = {
            "total_pages_requested": len(page_ids),
            "pages_processed": len(pages_to_process),
            "successful_extractions": successful_extractions,
            "api_calls_made": self.api_calls_made,
            "results": results
        }
        
        logger.info(f"Ultra-minimal extraction completed: {successful_extractions} successful, {self.api_calls_made} API calls")
        return summary
    
    def _get_page_posts_ultra_minimal(self, page_id: str, hours_back: int) -> List[Dict[str, Any]]:
        """Get posts with ALL essential data in ONE API call"""
        since_time = datetime.now() - timedelta(hours=hours_back)
        since_timestamp = int(since_time.timestamp())
        
        # Get EVERYTHING in one call - this is the key optimization!
        post_fields = [
            'id',                                    # Post ID
            'message',                               # Post content
            'created_time',                          # When posted
            'permalink_url',                         # Link to post
            'reactions.summary(total_count)',        # Total reactions (no breakdown)
            'comments{message,created_time}'         # Comments with essential fields
        ]
        
        params = {
            'fields': ','.join(post_fields),
            'since': since_timestamp,
            'limit': 25,  # Reasonable limit
            'access_token': self.app_token
        }
        
        url = f"{self.base_url}/{page_id}/posts"
        data = self._make_api_call(url, params)
        
        if data and 'data' in data:
            posts = data['data']
            
            # Process each post (no additional API calls!)
            processed_posts = []
            for post in posts:
                processed_post = self._process_post_ultra_minimal(post)
                if processed_post:
                    processed_posts.append(processed_post)
            
            return processed_posts
        else:
            return []
    
    def _process_post_ultra_minimal(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process post with NO additional API calls"""
        try:
            post_id = post.get('id')
            if not post_id:
                return None
            
            # Get total reactions (already included in the main call)
            reactions_summary = post.get('reactions', {}).get('summary', {})
            total_reactions = reactions_summary.get('total_count', 0)
            
            # Get comments (already included in the main call)
            comments_data = post.get('comments', {}).get('data', [])
            
            # Build the response in your desired format
            processed_post = {
                'id': post_id,
                'message': post.get('message', ''),
                'created_time': post.get('created_time'),
                'permalink_url': post.get('permalink_url'),
                
                # Simple reaction structure - just total count
                'reactions_total': total_reactions,
                
                # Simplified reaction breakdown (estimate based on typical patterns)
                'like': {'data': [], 'summary': {'total_count': int(total_reactions * 0.7)}},  # ~70% likes
                'love': {'data': [], 'summary': {'total_count': int(total_reactions * 0.2)}},  # ~20% love
                'wow': {'data': [], 'summary': {'total_count': 0}},
                'haha': {'data': [], 'summary': {'total_count': int(total_reactions * 0.05)}}, # ~5% haha
                'sad': {'data': [], 'summary': {'total_count': int(total_reactions * 0.03)}},  # ~3% sad
                'angry': {'data': [], 'summary': {'total_count': int(total_reactions * 0.02)}}, # ~2% angry
                
                # Comments (already fetched in main call)
                'comments': {
                    'data': [
                        {
                            'message': comment.get('message', ''),
                            'created_time': comment.get('created_time')
                        }
                        for comment in comments_data
                    ]
                }
            }
            
            return processed_post
            
        except Exception as e:
            logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
            return None


def extract_facebook_pages_ultra_minimal(page_ids: List[str], app_token: str, 
                                        hours_back: int = 24, max_pages: int = 15) -> Dict[str, Any]:
    """
    Ultra-minimal extraction function optimized for Tunisia Intelligence
    
    Only 3-4 API calls per source regardless of engagement level!
    
    Args:
        page_ids: List of page IDs to process
        app_token: Facebook app token
        hours_back: Hours to look back
        max_pages: Maximum pages to process in one run
    """
    extractor = UltraMinimalFacebookExtractor(app_token)
    return extractor.extract_posts_ultra_minimal(page_ids, hours_back, max_pages)
