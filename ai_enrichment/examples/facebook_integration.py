"""
Integration example with Facebook scraping system.

This module shows how to integrate AI enrichment with the existing
Facebook scraping workflow for social media posts and comments.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ai_enrichment.services.enrichment_service import EnrichmentService
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

class EnrichedFacebookLoader:
    """
    Enhanced Facebook loader with AI enrichment capabilities.
    
    This class extends the existing Facebook loading functionality
    to automatically enrich social media posts and comments with AI analysis.
    """
    
    def __init__(
        self,
        enrichment_service: Optional[EnrichmentService] = None,
        db_manager: Optional[DatabaseManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enriched Facebook loader.
        
        Args:
            enrichment_service: AI enrichment service
            db_manager: Database manager
            config: Configuration options
        """
        self.enrichment_service = enrichment_service or EnrichmentService()
        self.db_manager = db_manager or DatabaseManager()
        
        # Configuration
        self.default_config = {
            'enrich_posts': True,  # Enrich social media posts
            'enrich_comments': True,  # Enrich comments
            'min_content_length': 20,  # Minimum content length to enrich
            'max_retries': 2,  # Retry failed enrichments
            'skip_on_error': True,  # Skip enrichment if it fails
            'batch_size': 20,  # Process in batches
            'enrich_high_engagement_only': False,  # Only enrich posts with high engagement
            'min_engagement_threshold': 10  # Minimum reactions/comments for high engagement
        }
        
        self.config = {**self.default_config, **(config or {})}
    
    def insert_post_with_enrichment(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert social media post and enrich it with AI analysis.
        
        Args:
            post_data: Post data dictionary
            
        Returns:
            Inserted post with enrichment data
        """
        try:
            # First, insert the post using existing method
            response = self.db_manager.client.table("social_media_posts") \
                .insert(post_data) \
                .execute()
            
            if not response.data:
                logger.error("Failed to insert social media post")
                return None
            
            inserted_post = response.data[0]
            
            # Enrich the post if enabled
            if self.config['enrich_posts']:
                self._enrich_post(inserted_post)
            
            return inserted_post
            
        except Exception as e:
            logger.error(f"Failed to insert and enrich post: {e}")
            if self.config['skip_on_error']:
                # Try to insert without enrichment
                try:
                    response = self.db_manager.client.table("social_media_posts") \
                        .insert(post_data) \
                        .execute()
                    return response.data[0] if response.data else None
                except:
                    return None
            return None
    
    def insert_comment_with_enrichment(self, comment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert comment and enrich it with AI analysis.
        
        Args:
            comment_data: Comment data dictionary
            
        Returns:
            Inserted comment with enrichment data
        """
        try:
            # First, insert the comment
            response = self.db_manager.client.table("social_media_comments") \
                .insert(comment_data) \
                .execute()
            
            if not response.data:
                logger.error("Failed to insert comment")
                return None
            
            inserted_comment = response.data[0]
            
            # Enrich the comment if enabled
            if self.config['enrich_comments']:
                self._enrich_comment(inserted_comment)
            
            return inserted_comment
            
        except Exception as e:
            logger.error(f"Failed to insert and enrich comment: {e}")
            if self.config['skip_on_error']:
                # Try to insert without enrichment
                try:
                    response = self.db_manager.client.table("social_media_comments") \
                        .insert(comment_data) \
                        .execute()
                    return response.data[0] if response.data else None
                except:
                    return None
            return None
    
    def _enrich_post(self, post: Dict[str, Any]) -> bool:
        """
        Enrich a single social media post with AI analysis.
        
        Args:
            post: Post dictionary
            
        Returns:
            True if enrichment succeeded, False otherwise
        """
        try:
            content = post.get('content', '')
            
            if not content or len(content) < self.config['min_content_length']:
                logger.debug(f"Skipping enrichment for post {post.get('id')}: insufficient content")
                return False
            
            # Check engagement threshold if enabled
            if self.config['enrich_high_engagement_only']:
                if not self._meets_engagement_threshold(post):
                    logger.debug(f"Skipping enrichment for post {post.get('id')}: low engagement")
                    return False
            
            logger.info(f"Enriching post {post.get('id')}: {content[:50]}...")
            
            # Perform AI enrichment
            result = self.enrichment_service.enrich_content(
                content=content,
                content_type="social_media_post",
                content_id=post.get('id')
            )
            
            if result.status.value == 'success':
                logger.info(f"Successfully enriched post {post.get('id')} (confidence: {result.confidence:.2f})")
                return True
            else:
                logger.warning(f"Enrichment failed for post {post.get('id')}: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching post {post.get('id')}: {e}")
            return False
    
    def _enrich_comment(self, comment: Dict[str, Any]) -> bool:
        """
        Enrich a single comment with AI analysis.
        
        Args:
            comment: Comment dictionary
            
        Returns:
            True if enrichment succeeded, False otherwise
        """
        try:
            content = comment.get('content', '')
            
            if not content or len(content) < self.config['min_content_length']:
                logger.debug(f"Skipping enrichment for comment {comment.get('id')}: insufficient content")
                return False
            
            logger.info(f"Enriching comment {comment.get('id')}: {content[:30]}...")
            
            # Perform AI enrichment (mainly sentiment for comments)
            result = self.enrichment_service.enrich_content(
                content=content,
                content_type="comment",
                content_id=comment.get('id'),
                options={
                    'enable_sentiment': True,
                    'enable_entities': False,  # Usually not needed for comments
                    'enable_keywords': False,  # Usually not needed for comments
                    'enable_categories': False  # Usually not needed for comments
                }
            )
            
            if result.status.value == 'success':
                logger.info(f"Successfully enriched comment {comment.get('id')} (confidence: {result.confidence:.2f})")
                return True
            else:
                logger.warning(f"Enrichment failed for comment {comment.get('id')}: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching comment {comment.get('id')}: {e}")
            return False
    
    def _meets_engagement_threshold(self, post: Dict[str, Any]) -> bool:
        """
        Check if post meets engagement threshold for enrichment.
        
        Args:
            post: Post dictionary
            
        Returns:
            True if meets threshold, False otherwise
        """
        try:
            post_id = post.get('id')
            
            # Get reaction counts
            reaction_response = self.db_manager.client.table("social_media_post_reactions") \
                .select("count") \
                .eq("post_id", post_id) \
                .execute()
            
            total_reactions = sum(r.get('count', 0) for r in reaction_response.data or [])
            
            # Get comment count
            comment_response = self.db_manager.client.table("social_media_comments") \
                .select("id", count="exact") \
                .eq("post_id", post_id) \
                .execute()
            
            comment_count = comment_response.count or 0
            
            total_engagement = total_reactions + comment_count
            
            return total_engagement >= self.config['min_engagement_threshold']
            
        except Exception as e:
            logger.error(f"Error checking engagement for post {post.get('id')}: {e}")
            return True  # Default to enriching if we can't check engagement
    
    def enrich_existing_posts(
        self,
        limit: Optional[int] = None,
        account_filter: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich existing social media posts that haven't been processed yet.
        
        Args:
            limit: Maximum number of posts to process
            account_filter: Filter by specific account
            days_back: Process posts from N days back
            
        Returns:
            Processing statistics
        """
        from ai_enrichment.services.batch_processor import BatchProcessor
        
        logger.info("Starting enrichment of existing social media posts")
        
        # Use batch processor for existing posts
        batch_processor = BatchProcessor(enrichment_service=self.enrichment_service)
        
        # Calculate date filter
        date_from = None
        if days_back:
            from datetime import timedelta
            date_from = datetime.now() - timedelta(days=days_back)
        
        # Process posts
        result = batch_processor.process_social_media_posts(
            limit=limit,
            account_filter=account_filter,
            date_from=date_from,
            force_reprocess=False
        )
        
        return {
            'total_processed': result.total_items,
            'successful': result.successful_items,
            'failed': result.failed_items,
            'success_rate': result.success_rate,
            'processing_time': result.total_processing_time
        }
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about enriched social media content.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get total posts
            total_posts_response = self.db_manager.client.table("social_media_posts") \
                .select("id", count="exact") \
                .execute()
            total_posts = total_posts_response.count or 0
            
            # Get enriched posts (those with sentiment_score)
            enriched_posts_response = self.db_manager.client.table("social_media_posts") \
                .select("id", count="exact") \
                .not_.is_("sentiment_score", "null") \
                .execute()
            enriched_posts = enriched_posts_response.count or 0
            
            # Get total comments
            total_comments_response = self.db_manager.client.table("social_media_comments") \
                .select("id", count="exact") \
                .execute()
            total_comments = total_comments_response.count or 0
            
            # Get enriched comments
            enriched_comments_response = self.db_manager.client.table("social_media_comments") \
                .select("id", count="exact") \
                .not_.is_("sentiment_score", "null") \
                .execute()
            enriched_comments = enriched_comments_response.count or 0
            
            return {
                'posts': {
                    'total': total_posts,
                    'enriched': enriched_posts,
                    'pending': total_posts - enriched_posts,
                    'enrichment_rate': (enriched_posts / total_posts * 100) if total_posts > 0 else 0
                },
                'comments': {
                    'total': total_comments,
                    'enriched': enriched_comments,
                    'pending': total_comments - enriched_comments,
                    'enrichment_rate': (enriched_comments / total_comments * 100) if total_comments > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting enrichment statistics: {e}")
            return {'error': str(e)}

def create_enriched_facebook_workflow():
    """
    Example of creating an enriched Facebook workflow.
    
    This function demonstrates how to integrate AI enrichment
    into the existing Facebook scraping workflow.
    """
    print("📘 Creating Enriched Facebook Workflow")
    print("=" * 45)
    
    # Initialize enriched loader
    enriched_loader = EnrichedFacebookLoader(
        config={
            'enrich_posts': True,
            'enrich_comments': True,
            'min_content_length': 30,
            'enrich_high_engagement_only': True,
            'min_engagement_threshold': 5
        }
    )
    
    # Example: Process a sample post
    sample_post = {
        'social_media': 'facebook',
        'account': 'TunisianGovernment',
        'content': 'الحكومة التونسية تعلن عن برنامج جديد لدعم الشباب والمشاريع الصغيرة في إطار تحفيز الاقتصاد المحلي',
        'publish_date': datetime.now().isoformat(),
        'url': 'https://facebook.com/post/123'
    }
    
    print(f"📱 Processing Facebook post: {sample_post['content'][:50]}...")
    
    # Insert and enrich post
    result = enriched_loader.insert_post_with_enrichment(sample_post)
    
    if result:
        print("✅ Post inserted and enriched successfully")
    else:
        print("❌ Failed to process post")
    
    # Example: Process a sample comment
    sample_comment = {
        'post_id': result.get('id') if result else 1,
        'content': 'هذا إجراء ممتاز ونتمنى أن يكون له تأثير إيجابي على الشباب',
        'comment_date': datetime.now().isoformat(),
        'relevance': True
    }
    
    print(f"💬 Processing comment: {sample_comment['content'][:30]}...")
    
    # Insert and enrich comment
    comment_result = enriched_loader.insert_comment_with_enrichment(sample_comment)
    
    if comment_result:
        print("✅ Comment inserted and enriched successfully")
    else:
        print("❌ Failed to process comment")
    
    # Get enrichment statistics
    print("\n📊 Getting enrichment statistics...")
    stats = enriched_loader.get_enrichment_statistics()
    
    if 'error' not in stats:
        print(f"📱 Posts: {stats['posts']['enriched']}/{stats['posts']['total']} enriched ({stats['posts']['enrichment_rate']:.1f}%)")
        print(f"💬 Comments: {stats['comments']['enriched']}/{stats['comments']['total']} enriched ({stats['comments']['enrichment_rate']:.1f}%)")

def integrate_with_existing_facebook_loader():
    """
    Example of integrating with existing Facebook loader.
    
    This shows how to modify existing Facebook loading code
    to include AI enrichment.
    """
    print("\n🔗 Integration with Existing Facebook Loader")
    print("=" * 50)
    
    # This is how you would modify existing Facebook loading code
    print("📝 Example integration code:")
    
    integration_code = '''
# In your existing Facebook loader (e.g., facebook_loader.py):

from ai_enrichment.services.enrichment_service import EnrichmentService

class FacebookLoader:
    def __init__(self):
        # ... existing initialization ...
        
        # Add AI enrichment service
        self.enrichment_service = EnrichmentService()
        self.enable_enrichment = True  # Configuration flag
    
    def process_post(self, post_data):
        # ... existing post processing ...
        
        # Insert post as usual
        response = self.db_manager.client.table("social_media_posts") \\
            .insert(post_data) \\
            .execute()
        
        post = response.data[0] if response.data else None
        
        # Add AI enrichment
        if self.enable_enrichment and post and post.get('content'):
            try:
                enrichment_result = self.enrichment_service.enrich_content(
                    content=post['content'],
                    content_type="social_media_post",
                    content_id=post['id']
                )
                
                if enrichment_result.status.value == 'success':
                    logger.info(f"Post {post['id']} enriched successfully")
                else:
                    logger.warning(f"Enrichment failed for post {post['id']}")
                    
            except Exception as e:
                logger.error(f"Enrichment error for post {post['id']}: {e}")
        
        return post
    
    def process_comment(self, comment_data):
        # ... existing comment processing ...
        
        # Insert comment as usual
        response = self.db_manager.client.table("social_media_comments") \\
            .insert(comment_data) \\
            .execute()
        
        comment = response.data[0] if response.data else None
        
        # Add AI enrichment (mainly sentiment for comments)
        if self.enable_enrichment and comment and comment.get('content'):
            try:
                enrichment_result = self.enrichment_service.enrich_content(
                    content=comment['content'],
                    content_type="comment",
                    content_id=comment['id'],
                    options={
                        'enable_sentiment': True,
                        'enable_entities': False,
                        'enable_keywords': False,
                        'enable_categories': False
                    }
                )
                
                if enrichment_result.status.value == 'success':
                    logger.info(f"Comment {comment['id']} enriched successfully")
                    
            except Exception as e:
                logger.error(f"Enrichment error for comment {comment['id']}: {e}")
        
        return comment
    '''
    
    print(integration_code)

def main():
    """Run Facebook integration examples."""
    print("📘 Facebook Integration Examples")
    print("=" * 40)
    
    try:
        create_enriched_facebook_workflow()
        integrate_with_existing_facebook_loader()
        
        print("\n✅ Facebook integration examples completed!")
        print("\n📚 Integration Steps:")
        print("   1. Import EnrichmentService in your Facebook loader")
        print("   2. Initialize the service in your loader class")
        print("   3. Call enrich_content() after inserting posts/comments")
        print("   4. Use different options for posts vs comments")
        print("   5. Handle enrichment errors gracefully")
        print("   6. Consider engagement thresholds for efficiency")
        
    except Exception as e:
        print(f"\n❌ Facebook integration example failed: {e}")
        print("   Make sure your database is configured and Ollama is running")

if __name__ == "__main__":
    main()
