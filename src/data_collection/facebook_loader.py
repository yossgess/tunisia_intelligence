"""
Ultra-Minimal Facebook Loader

Works with the ultra-minimal extractor to achieve maximum efficiency:
- Only 3-4 API calls per source regardless of engagement
- Stores essential intelligence data only
- Optimized for high-frequency runs without hitting rate limits

Perfect for Tunisia Intelligence continuous monitoring.
"""

import logging
import logging
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from pathlib import Path
import hashlib

# Import database configuration
from config.database import DatabaseManager
from config.secrets import SecretManager
from config.facebook_config import get_facebook_config
from extractors.facebook_extractor import UltraMinimalFacebookExtractor

logger = logging.getLogger(__name__)


class UltraMinimalFacebookLoader:
    """Ultra-minimal Facebook loader for maximum efficiency"""
    
    def __init__(self):
        """Initialize the ultra-minimal Facebook loader"""
        self.db_manager = DatabaseManager()
        self.client = self.db_manager.client
        
        # Use file-based secret storage
        secret_manager = SecretManager(backend="file")
        
        # Get Facebook app token - auto-setup if missing
        self.app_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
        if not self.app_token:
            logger.info("Facebook token not found, setting up automatically...")
            self._setup_facebook_token_automatically(secret_manager)
            self.app_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
            if not self.app_token:
                raise ValueError("Failed to setup FACEBOOK_APP_TOKEN automatically")
        
        # Get Facebook configuration
        self.config = get_facebook_config()
        
        # Initialize ultra-minimal extractor with configuration
        api_version = secret_manager.get_secret("FACEBOOK_API_VERSION", self.config.extraction.api_version)
        self.facebook_extractor = UltraMinimalFacebookExtractor(self.app_token, api_version, self.config)
        
        # Configuration for ultra-minimal processing (use config values)
        self.max_pages_per_run = self.config.extraction.max_pages_per_run
        self.priority_file = Path("facebook_page_priorities.json")
        self.page_priorities = self._load_page_priorities()
    
    def _setup_facebook_token_automatically(self, secret_manager):
        """Automatically setup Facebook token if missing"""
        try:
            # Facebook app token (same as in setup_facebook_token.py)
            app_token = "5857679854344905|ll5MIrsnV0lBA4SxwsI83Ujc4YQ"
            
            # Store the token securely
            success = secret_manager.set_secret("FACEBOOK_APP_TOKEN", app_token)
            if success:
                logger.info("✅ Facebook app token stored successfully")
                
                # Also set API version
                secret_manager.set_secret("FACEBOOK_API_VERSION", "v18.0")
                logger.info("✅ Facebook API version set to v18.0")
                
                # Set environment variable to use file backend
                import os
                os.environ["SECRETS_BACKEND"] = "file"
                logger.info("✅ Secret backend configured for file storage")
            else:
                logger.error("❌ Failed to store Facebook app token")
                
        except Exception as e:
            logger.error(f"Error setting up Facebook token automatically: {e}")
    
    def reload_configuration(self):
        """Reload Facebook configuration from the config system"""
        try:
            logger.info("🔄 Reloading Facebook configuration...")
            
            # Store old values for comparison
            old_max_pages = getattr(self, 'max_pages_per_run', None)
            old_config = getattr(self, 'config', None)
            
            # Reload configuration
            self.config = get_facebook_config()
            self.max_pages_per_run = self.config.extraction.max_pages_per_run
            
            # Update extractor configuration if needed
            if hasattr(self.facebook_extractor, 'update_config'):
                self.facebook_extractor.update_config(self.config)
            
            # Log changes
            changes = []
            if old_max_pages != self.max_pages_per_run:
                changes.append(f"max_pages_per_run: {old_max_pages} → {self.max_pages_per_run}")
            
            if old_config and hasattr(old_config, 'extraction'):
                if old_config.extraction.min_api_delay != self.config.extraction.min_api_delay:
                    changes.append(f"min_api_delay: {old_config.extraction.min_api_delay} → {self.config.extraction.min_api_delay}")
                if old_config.extraction.max_api_calls_per_run != self.config.extraction.max_api_calls_per_run:
                    changes.append(f"max_api_calls: {old_config.extraction.max_api_calls_per_run} → {self.config.extraction.max_api_calls_per_run}")
            
            if changes:
                logger.info(f"✅ Configuration reloaded with changes: {', '.join(changes)}")
            else:
                logger.info("✅ Configuration reloaded (no changes detected)")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error reloading configuration: {e}")
            return False
    
    def _check_reload_signal(self):
        """Check if configuration reload has been requested"""
        try:
            reload_signal_file = Path("facebook_config_reload.signal")
            if reload_signal_file.exists():
                # Get file modification time
                signal_time = reload_signal_file.stat().st_mtime
                current_time = time.time()
                
                # If signal is recent (within last 60 seconds), reload config
                if current_time - signal_time < 60:
                    logger.info("Configuration reload signal detected")
                    self.reload_configuration()
                    
                    # Remove the signal file
                    reload_signal_file.unlink()
                    return True
        except Exception as e:
            logger.debug(f"Error checking reload signal: {e}")
        return False
    
    def _load_page_priorities(self) -> Dict[str, int]:
        """Load page priorities based on historical activity"""
        if self.priority_file.exists():
            try:
                with open(self.priority_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load page priorities: {e}")
        
        # Default priorities for key Tunisian government institutions
        return {
            "271178572940207": 10,  # Présidence de la République
            "213636118651883": 10,  # Présidence du Gouvernement
            "1515094915436499": 9,  # Parlement
            "292899070774121": 8,   # Ministère de la Justice
            "516083015235303": 8,   # Ministère de la Défense
            "192600677433983": 8,   # Ministère de l'Intérieur
            "171454396234624": 7,   # Ministère des Affaires étrangères
        }
    
    def _save_page_priorities(self):
        """Save updated page priorities"""
        try:
            with open(self.priority_file, 'w') as f:
                json.dump(self.page_priorities, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save page priorities: {e}")
    
    def _update_page_priority(self, page_id: str, posts_found: int):
        """Update page priority based on activity"""
        current_priority = self.page_priorities.get(page_id, 5)
        
        if posts_found > 0:
            # Increase priority for active pages
            self.page_priorities[page_id] = min(current_priority + 1, 10)
        else:
            # Slightly decrease priority for inactive pages
            self.page_priorities[page_id] = max(current_priority - 0.1, 1)
    
    def load_facebook_sources_prioritized(self) -> List[Dict[str, Any]]:
        """Get Facebook sources sorted by priority"""
        try:
            response = self.client.table("sources") \
                .select("*") \
                .eq("source_type", "facebook") \
                .eq("is_active", True) \
                .execute()
            
            sources = response.data
            
            # Sort by priority (highest first)
            def get_priority(source):
                page_id = source.get('page_id', '')
                return self.page_priorities.get(page_id, 5)
            
            sources.sort(key=get_priority, reverse=True)
            
            logger.info(f"Loaded {len(sources)} Facebook sources, sorted by priority")
            return sources
            
        except Exception as e:
            logger.error(f"Error fetching Facebook sources: {e}")
            return []
    
    def extract_and_load_posts_ultra_minimal(self, hours_back: int = 168) -> Dict[str, Any]:
        """
        Ultra-minimal extraction and loading with maximum efficiency
        """
        start_time = datetime.now()
        
        try:
            # Get prioritized sources
            sources = self.load_facebook_sources_prioritized()
            if not sources:
                return {"status": "no_sources", "message": "No active Facebook sources found"}
            
            logger.info(f"Found {len(sources)} Facebook sources")
            
            # Can handle more pages with ultra-minimal approach
            sources_to_process = sources[:self.max_pages_per_run]
            page_ids = [source.get('page_id') for source in sources_to_process if source.get('page_id')]
            
            logger.info(f"Processing top {len(page_ids)} priority pages for ultra-minimal extraction")
            
            # Create source mapping
            source_mapping = {source.get('page_id'): source for source in sources_to_process}
            
            # Extract posts using ultra-minimal extractor
            extraction_results = self.facebook_extractor.extract_posts_ultra_minimal(
                page_ids, hours_back, self.max_pages_per_run
            )
            
            # Process results
            total_posts_loaded = 0
            total_reactions_loaded = 0
            total_comments_loaded = 0
            errors = []
            
            results = extraction_results.get('results', {})
            
            for page_id, page_result in results.items():
                try:
                    # Check for configuration reload signal
                    self._check_reload_signal()
                    
                    if "error" in page_result:
                        errors.append(f"Page {page_id}: {page_result['error']}")
                        continue
                    
                    source_info = source_mapping.get(page_id)
                    if not source_info:
                        continue
                    
                    posts = page_result.get('posts', [])
                    
                    # Update priority based on activity
                    self._update_page_priority(page_id, len(posts))
                    
                    # Load posts for this page with duplicate checking
                    if posts:
                        page_stats = self._load_page_posts_with_state_tracking(page_result, source_info)
                        total_posts_loaded += page_stats.get('posts_loaded', 0)
                        total_reactions_loaded += page_stats.get('reactions_loaded', 0)
                        total_comments_loaded += page_stats.get('comments_loaded', 0)
                    
                    # Update parsing state for this source
                    self._update_parsing_state(source_info, posts)
                    
                except Exception as e:
                    error_msg = f"Error processing page {page_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Save updated priorities
            self._save_page_priorities()
            
            # Calculate efficiency
            api_calls = extraction_results.get('api_calls_made', 0)
            sources_processed = len(page_ids)
            efficiency = api_calls / sources_processed if sources_processed > 0 else 0
            
            # Log parsing results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self._log_parsing_results(
                sources_processed=sources_processed,
                posts_loaded=total_posts_loaded,
                reactions_loaded=total_reactions_loaded,
                comments_loaded=total_comments_loaded,
                api_calls=api_calls,
                processing_time=processing_time,
                errors=len(errors)
            )
            
            # Return summary
            summary = {
                "status": "completed",
                "total_sources_available": len(sources),
                "sources_processed": sources_processed,
                "total_posts_loaded": total_posts_loaded,
                "total_reactions_loaded": total_reactions_loaded,
                "total_comments_loaded": total_comments_loaded,
                "api_calls_made": api_calls,
                "efficiency": efficiency,
                "errors": errors,
                "processing_time": end_time.isoformat(),
                "processing_duration": processing_time,
                "optimization_notes": [
                    f"Ultra-minimal extraction: processed {sources_processed} of {len(sources)} sources",
                    f"Maximum efficiency: {api_calls} API calls total ({efficiency:.1f} calls/source)",
                    "Single API call gets posts + reactions + comments per source",
                    "Perfect for high-frequency monitoring without rate limits",
                    "Page priorities updated based on activity",
                    "Duplicate detection and parsing state tracking enabled"
                ]
            }
            
            logger.info(f"Ultra-minimal loading completed: {total_posts_loaded} posts, "
                       f"{api_calls} API calls ({efficiency:.1f} calls/source)")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in ultra-minimal extract_and_load_posts: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_parsing_state(self, source_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the last parsing state for a source"""
        try:
            source_id = source_info.get('id')
            if not source_id:
                return None
            
            response = self.client.table("parsing_state") \
                .select("*") \
                .eq("source_id", source_id) \
                .limit(1) \
                .execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting parsing state: {e}")
            return None
    
    def _update_parsing_state(self, source_info: Dict[str, Any], posts: List[Dict[str, Any]]):
        """Update parsing state for a source"""
        try:
            source_id = source_info.get('id')
            if not source_id or not posts:
                return
            
            # Get the most recent post
            latest_post = max(posts, key=lambda p: p.get('created_time', ''))
            
            # Prepare state data
            state_data = {
                'source_id': source_id,
                'last_parsed_at': datetime.now().isoformat(),
                'last_article_link': latest_post.get('permalink_url', ''),
                'last_article_guid': latest_post.get('id', '')
            }
            
            # Check if parsing state exists for this source
            existing = self.client.table("parsing_state") \
                .select("id") \
                .eq("source_id", source_id) \
                .limit(1) \
                .execute()
            
            if existing.data:
                # Update existing parsing state
                self.client.table("parsing_state") \
                    .update(state_data) \
                    .eq("source_id", source_id) \
                    .execute()
            else:
                # Insert new parsing state
                self.client.table("parsing_state") \
                    .insert(state_data) \
                    .execute()
            
            logger.debug(f"Updated parsing state for source {source_id}")
            
        except Exception as e:
            logger.error(f"Error updating parsing state: {e}")
    
    def _generate_content_hash(self, post: Dict[str, Any]) -> str:
        """Generate a hash for post content to detect duplicates"""
        try:
            # Create hash from post ID + message + created_time
            content_parts = [
                post.get('id', ''),
                post.get('message', ''),
                post.get('created_time', '')
            ]
            content_string = '|'.join(content_parts)
            return hashlib.md5(content_string.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error generating content hash: {e}")
            return ""
    
    def _is_duplicate_post(self, post: Dict[str, Any], source_info: Dict[str, Any]) -> bool:
        """Check if a post is a duplicate based on parsing state"""
        try:
            parsing_state = self._get_parsing_state(source_info)
            if not parsing_state:
                return False  # No previous state, not a duplicate
            
            # Check by post ID first
            last_parsed_id = parsing_state.get('last_article_guid')
            if last_parsed_id and post.get('id') == last_parsed_id:
                return True
            
            # Check by content hash
            last_content_hash = parsing_state.get('last_content_hash')
            if last_content_hash:
                current_hash = self._generate_content_hash(post)
                if current_hash == last_content_hash:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate post: {e}")
            return False
    
    def _log_parsing_results(self, sources_processed: int, posts_loaded: int, 
                           reactions_loaded: int, comments_loaded: int, 
                           api_calls: int, processing_time: float, errors: int):
        """Log parsing results to database - use correct table name"""
        try:
            log_data = {
                'source_id': None,  # This is a batch operation
                'started_at': datetime.now().isoformat(),
                'finished_at': datetime.now().isoformat(),
                'articles_fetched': posts_loaded,
                'status': 'success' if errors == 0 else 'partial',
                'error_message': f"{errors} errors encountered" if errors > 0 else None
            }
            
            self.client.table("parsing_log") \
                .insert(log_data) \
                .execute()
            
            logger.debug("Logged parsing results to parsing_log table")
            
        except Exception as e:
            logger.error(f"Error logging parsing results: {e}")
    
    def _load_page_posts_with_state_tracking(self, page_result: Dict[str, Any], source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Load posts with duplicate detection and state tracking"""
        posts_loaded = 0
        reactions_loaded = 0
        comments_loaded = 0
        
        try:
            page_info = page_result.get('page_info', {})
            posts = page_result.get('posts', [])
            
            account_name = page_info.get('name', source_info.get('name', 'Unknown'))
            
            logger.info(f"Loading {len(posts)} posts for account: {account_name}")
            
            # Filter out duplicate posts
            new_posts = []
            for post in posts:
                if not self._is_duplicate_post(post, source_info):
                    new_posts.append(post)
                else:
                    logger.debug(f"Skipping duplicate post: {post.get('id')}")
            
            if not new_posts:
                logger.info(f"No new posts found for {account_name} (all were duplicates)")
                return {
                    "posts_loaded": 0,
                    "reactions_loaded": 0,
                    "comments_loaded": 0
                }
            
            logger.info(f"Found {len(new_posts)} new posts (filtered {len(posts) - len(new_posts)} duplicates)")
            
            # Batch insert new posts
            post_data_batch = []
            
            for post in new_posts:
                try:
                    # Prepare ultra-minimal post data
                    post_data = self._prepare_post_data_ultra_minimal(post, account_name, source_info.get('id'))
                    if post_data:
                        post_data_batch.append(post_data)
                
                except Exception as e:
                    logger.error(f"Error preparing post {post.get('id', 'unknown')}: {e}")
            
            # Batch insert posts
            if post_data_batch:
                posts_loaded = self._batch_insert_posts(post_data_batch)
                
                # Insert reactions and comments for successfully inserted posts
                for i, post in enumerate(new_posts[:posts_loaded]):
                    try:
                        post_id = self._get_post_id_by_url(post.get('permalink_url'))
                        if post_id:
                            reactions_loaded += self._insert_post_reactions_ultra_minimal(post_id, post)
                            comments_loaded += self._insert_post_comments_ultra_minimal(post_id, post.get('comments', {}))
                    except Exception as e:
                        logger.error(f"Error loading reactions/comments: {e}")
            
        except Exception as e:
            logger.error(f"Error loading page posts with state tracking: {e}")
        
        return {
            "posts_loaded": posts_loaded,
            "reactions_loaded": reactions_loaded,
            "comments_loaded": comments_loaded
        }

    def _load_page_posts_ultra_minimal(self, page_result: Dict[str, Any], source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Load posts with ultra-minimal database operations"""
        posts_loaded = 0
        reactions_loaded = 0
        comments_loaded = 0
        
        try:
            page_info = page_result.get('page_info', {})
            posts = page_result.get('posts', [])
            
            account_name = page_info.get('name', source_info.get('name', 'Unknown'))
            
            logger.info(f"Loading {len(posts)} posts for account: {account_name}")
            
            # Batch insert posts for better performance
            post_data_batch = []
            
            for post in posts:
                try:
                    # Prepare ultra-minimal post data
                    post_data = self._prepare_post_data_ultra_minimal(post, account_name, source_info.get('id'))
                    if post_data:
                        post_data_batch.append(post_data)
                
                except Exception as e:
                    logger.error(f"Error preparing post {post.get('id', 'unknown')}: {e}")
            
            # Batch insert posts
            if post_data_batch:
                posts_loaded = self._batch_insert_posts(post_data_batch)
                
                # Insert reactions and comments for successfully inserted posts
                for i, post in enumerate(posts[:posts_loaded]):
                    try:
                        post_id = self._get_post_id_by_url(post.get('permalink_url'))
                        if post_id:
                            reactions_loaded += self._insert_post_reactions_ultra_minimal(post_id, post)
                            comments_loaded += self._insert_post_comments_ultra_minimal(post_id, post.get('comments', {}))
                    except Exception as e:
                        logger.error(f"Error loading reactions/comments: {e}")
            
        except Exception as e:
            logger.error(f"Error loading page posts: {e}")
        
        return {
            "posts_loaded": posts_loaded,
            "reactions_loaded": reactions_loaded,
            "comments_loaded": comments_loaded
        }
    
    def _prepare_post_data_ultra_minimal(self, post: Dict[str, Any], account_name: str, source_id: int = None) -> Optional[Dict[str, Any]]:
        """Prepare ultra-minimal post data for database insertion"""
        try:
            # Parse publish date
            publish_date = None
            if post.get('created_time'):
                try:
                    publish_date = date_parser.parse(post['created_time'])
                except Exception as e:
                    logger.warning(f"Could not parse date {post['created_time']}: {e}")
            
            # Get message content
            content = post.get('message', '').strip()
            
            if not content and not post.get('permalink_url'):
                return None  # Skip posts with no content or URL
            
            return {
                "source_id": source_id,
                "social_media": "facebook",
                "account": account_name,
                "content": content,
                "publish_date": publish_date.isoformat() if publish_date else None,
                "url": post.get('permalink_url'),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error preparing post data: {e}")
            return None
    
    def _batch_insert_posts(self, post_data_batch: List[Dict[str, Any]]) -> int:
        """Batch insert posts for better performance"""
        try:
            if not post_data_batch:
                return 0
            
            # Insert posts individually to handle duplicates properly
            inserted_count = 0
            for post_data in post_data_batch:
                # Check if post already exists by url
                existing = self.client.table("social_media_posts") \
                    .select("id") \
                    .eq("url", post_data['url']) \
                    .limit(1) \
                    .execute()
                
                if existing.data:
                    # Post exists, update it
                    self.client.table("social_media_posts") \
                        .update(post_data) \
                        .eq("url", post_data['url']) \
                        .execute()
                else:
                    # Post doesn't exist, insert it
                    self.client.table("social_media_posts") \
                        .insert(post_data) \
                        .execute()
                inserted_count += 1
            
            logger.info(f"Processed {inserted_count} posts")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error batch inserting posts: {e}")
            return 0
    
    def _get_post_id_by_url(self, url: str) -> Optional[int]:
        """Get post ID by URL for foreign key relationships"""
        try:
            if not url:
                return None
            
            response = self.client.table("social_media_posts") \
                .select("id") \
                .eq("url", url) \
                .limit(1) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting post ID by URL: {e}")
            return None
    
    def _insert_post_reactions_ultra_minimal(self, post_id: int, post: Dict[str, Any]) -> int:
        """Insert reactions from ultra-minimal extraction format"""
        try:
            reaction_data_batch = []
            
            # Process each reaction type from the ultra-minimal format
            reaction_types = ['like', 'love', 'wow', 'haha', 'sad', 'angry']
            
            for reaction_type in reaction_types:
                reaction_data = post.get(reaction_type, {})
                summary = reaction_data.get('summary', {})
                count = summary.get('total_count', 0)
                
                if count > 0:
                    reaction_data_batch.append({
                        "post_id": post_id,
                        "reaction_type": reaction_type,
                        "count": count
                    })
            
            if reaction_data_batch:
                # Delete existing and insert new
                self.client.table("social_media_post_reactions") \
                    .delete() \
                    .eq("post_id", post_id) \
                    .execute()
                
                response = self.client.table("social_media_post_reactions") \
                    .insert(reaction_data_batch) \
                    .execute()
                
                return len(response.data) if response.data else 0
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting reactions: {e}")
            return 0
    
    def _insert_post_comments_ultra_minimal(self, post_id: int, comments_data: Dict[str, Any]) -> int:
        """Insert comments from ultra-minimal extraction format"""
        try:
            comments = comments_data.get('data', [])
            if not comments:
                return 0
            
            comment_data_batch = []
            
            for comment in comments:
                comment_date = None
                if comment.get('created_time'):
                    try:
                        comment_date = date_parser.parse(comment['created_time'])
                    except Exception:
                        pass
                
                content = comment.get('message', '').strip()
                if content:
                    comment_data_batch.append({
                        "post_id": post_id,
                        "content": content,
                        "comment_date": comment_date.isoformat() if comment_date else datetime.now().isoformat()
                    })
            
            if comment_data_batch:
                response = self.client.table("social_media_comments") \
                    .insert(comment_data_batch) \
                    .execute()
                
                return len(response.data) if response.data else 0
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting comments: {e}")
            return 0


def main():
    """Main function for ultra-minimal Facebook loading"""
    try:
        loader = UltraMinimalFacebookLoader()
        
        # Load posts with ultra-minimal extraction (last 7 days)
        result = loader.extract_and_load_posts_ultra_minimal(hours_back=168)
        
        print("Ultra-Minimal Facebook Loading Results:")
        print(f"Status: {result.get('status')}")
        print(f"Sources processed: {result.get('sources_processed', 0)} of {result.get('total_sources_available', 0)}")
        print(f"Posts loaded: {result.get('total_posts_loaded', 0)}")
        print(f"API calls made: {result.get('api_calls_made', 0)}")
        print(f"Efficiency: {result.get('efficiency', 0):.1f} calls/source")
        
        if result.get('optimization_notes'):
            print("\nOptimization Notes:")
            for note in result['optimization_notes']:
                print(f"  - {note}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in ultra-minimal main: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    main()
