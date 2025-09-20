"""
Integration example with RSS scraping system.

This module shows how to integrate AI enrichment with the existing
RSS scraping workflow.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ai_enrichment.services.enrichment_service import EnrichmentService
from config.database import DatabaseManager, Article

logger = logging.getLogger(__name__)

class EnrichedRSSLoader:
    """
    Enhanced RSS loader with AI enrichment capabilities.
    
    This class extends the existing RSS loading functionality
    to automatically enrich articles with AI analysis.
    """
    
    def __init__(
        self,
        enrichment_service: Optional[EnrichmentService] = None,
        db_manager: Optional[DatabaseManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enriched RSS loader.
        
        Args:
            enrichment_service: AI enrichment service
            db_manager: Database manager
            config: Configuration options
        """
        self.enrichment_service = enrichment_service or EnrichmentService()
        self.db_manager = db_manager or DatabaseManager()
        
        # Configuration
        self.default_config = {
            'enrich_on_insert': True,  # Enrich articles when inserting
            'enrich_existing': False,  # Enrich existing articles
            'min_content_length': 50,  # Minimum content length to enrich
            'max_retries': 2,  # Retry failed enrichments
            'skip_on_error': True,  # Skip enrichment if it fails
            'batch_size': 10  # Process in batches
        }
        
        self.config = {**self.default_config, **(config or {})}
    
    def insert_article_with_enrichment(self, article: Article) -> Optional[Article]:
        """
        Insert article and enrich it with AI analysis.
        
        Args:
            article: Article to insert and enrich
            
        Returns:
            Inserted article with enrichment data
        """
        try:
            # First, insert the article using existing method
            inserted_article = self.db_manager.insert_article(article)
            
            if not inserted_article:
                logger.error("Failed to insert article")
                return None
            
            # Enrich the article if enabled
            if self.config['enrich_on_insert']:
                self._enrich_article(inserted_article)
            
            return inserted_article
            
        except Exception as e:
            logger.error(f"Failed to insert and enrich article: {e}")
            if self.config['skip_on_error']:
                # Try to insert without enrichment
                return self.db_manager.insert_article(article)
            return None
    
    def _enrich_article(self, article: Article) -> bool:
        """
        Enrich a single article with AI analysis.
        
        Args:
            article: Article to enrich
            
        Returns:
            True if enrichment succeeded, False otherwise
        """
        try:
            # Get content for enrichment
            content = self._get_article_content(article)
            
            if not content or len(content) < self.config['min_content_length']:
                logger.debug(f"Skipping enrichment for article {article.id}: insufficient content")
                return False
            
            logger.info(f"Enriching article {article.id}: {article.title[:50]}...")
            
            # Perform AI enrichment
            result = self.enrichment_service.enrich_content(
                content=content,
                content_type="article",
                content_id=article.id
            )
            
            if result.status.value == 'success':
                logger.info(f"Successfully enriched article {article.id} (confidence: {result.confidence:.2f})")
                return True
            else:
                logger.warning(f"Enrichment failed for article {article.id}: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching article {article.id}: {e}")
            return False
    
    def _get_article_content(self, article: Article) -> str:
        """
        Extract content from article for enrichment.
        
        Args:
            article: Article object
            
        Returns:
            Combined content string
        """
        content_parts = []
        
        # Add title
        if article.title:
            content_parts.append(article.title)
        
        # Add description
        if article.description:
            content_parts.append(article.description)
        
        # Add main content
        if article.content:
            content_parts.append(article.content)
        
        return " ".join(content_parts).strip()
    
    def enrich_existing_articles(
        self,
        limit: Optional[int] = None,
        source_ids: Optional[list] = None,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich existing articles that haven't been processed yet.
        
        Args:
            limit: Maximum number of articles to process
            source_ids: Filter by specific source IDs
            days_back: Process articles from N days back
            
        Returns:
            Processing statistics
        """
        from ai_enrichment.services.batch_processor import BatchProcessor
        
        logger.info("Starting enrichment of existing articles")
        
        # Use batch processor for existing articles
        batch_processor = BatchProcessor(enrichment_service=self.enrichment_service)
        
        # Calculate date filter
        date_from = None
        if days_back:
            from datetime import timedelta
            date_from = datetime.now() - timedelta(days=days_back)
        
        # Process articles
        result = batch_processor.process_articles(
            limit=limit,
            source_ids=source_ids,
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

def create_enriched_rss_workflow():
    """
    Example of creating an enriched RSS workflow.
    
    This function demonstrates how to integrate AI enrichment
    into the existing RSS scraping workflow.
    """
    print("🔄 Creating Enriched RSS Workflow")
    print("=" * 40)
    
    # Initialize enriched loader
    enriched_loader = EnrichedRSSLoader(
        config={
            'enrich_on_insert': True,
            'min_content_length': 100,
            'skip_on_error': True
        }
    )
    
    # Example: Process a sample article
    sample_article = Article(
        title="الحكومة التونسية تعلن عن إجراءات اقتصادية جديدة",
        description="أعلنت الحكومة التونسية اليوم عن مجموعة من الإجراءات الاقتصادية الجديدة",
        content="في إطار الجهود المبذولة لتحسين الوضع الاقتصادي، أعلنت الحكومة التونسية عن خطة شاملة تتضمن إجراءات متنوعة لدعم الاستثمار وتحفيز النمو الاقتصادي في البلاد.",
        link="https://example.com/article/123",
        source_id=1
    )
    
    print(f"📰 Processing article: {sample_article.title}")
    
    # Insert and enrich article
    result = enriched_loader.insert_article_with_enrichment(sample_article)
    
    if result:
        print("✅ Article inserted and enriched successfully")
    else:
        print("❌ Failed to process article")
    
    # Example: Enrich existing articles
    print("\n🔄 Enriching existing articles...")
    stats = enriched_loader.enrich_existing_articles(limit=5, days_back=7)
    
    print(f"📊 Processing Statistics:")
    print(f"   Total Processed: {stats['total_processed']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")

def integrate_with_existing_rss_loader():
    """
    Example of integrating with existing RSS loader.
    
    This shows how to modify existing RSS loading code
    to include AI enrichment.
    """
    print("\n🔗 Integration with Existing RSS Loader")
    print("=" * 45)
    
    # This is how you would modify existing RSS loading code
    print("📝 Example integration code:")
    
    integration_code = '''
# In your existing RSS loader (e.g., rss_loader.py):

from ai_enrichment.services.enrichment_service import EnrichmentService

class RSSLoader:
    def __init__(self):
        # ... existing initialization ...
        
        # Add AI enrichment service
        self.enrichment_service = EnrichmentService()
        self.enable_enrichment = True  # Configuration flag
    
    def process_article(self, article_data):
        # ... existing article processing ...
        
        # Insert article as usual (uses news_articles table)
        article = self.db_manager.insert_article(article)
        
        # Add AI enrichment
        if self.enable_enrichment and article:
            try:
                content = f"{article.title} {article.description or ''} {article.content or ''}"
                
                enrichment_result = self.enrichment_service.enrich_content(
                    content=content,
                    content_type="article",
                    content_id=article.id
                )
                
                if enrichment_result.status.value == 'success':
                    logger.info(f"Article {article.id} enriched successfully")
                else:
                    logger.warning(f"Enrichment failed for article {article.id}")
                    
            except Exception as e:
                logger.error(f"Enrichment error for article {article.id}: {e}")
        
        return article
    '''
    
    print(integration_code)

def main():
    """Run RSS integration examples."""
    print("🔗 RSS Integration Examples")
    print("=" * 35)
    
    try:
        create_enriched_rss_workflow()
        integrate_with_existing_rss_loader()
        
        print("\n✅ RSS integration examples completed!")
        print("\n📚 Integration Steps:")
        print("   1. Import EnrichmentService in your RSS loader")
        print("   2. Initialize the service in your loader class")
        print("   3. Call enrich_content() after inserting articles")
        print("   4. Handle enrichment errors gracefully")
        print("   5. Use batch processing for existing articles")
        
    except Exception as e:
        print(f"\n❌ RSS integration example failed: {e}")
        print("   Make sure your database is configured and Ollama is running")

if __name__ == "__main__":
    main()
