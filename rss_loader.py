import logging
import time
from typing import List, Dict, Any, Optional
import feedparser
from datetime import datetime, timezone

from config.database import DatabaseManager, Source, Article, ParsingState, ParsingLog
from utils.date_utils import parse_date_enhanced
from utils.content_utils import extract_content_from_entry, clean_html_content, extract_media_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rss_loader.log')
    ]
)
logger = logging.getLogger(__name__)

class RSSLoader:
    """
    RSS feed loader that handles fetching, parsing and storing RSS feed data.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def fetch_feed(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed from the given URL.
        
        Args:
            url: URL of the RSS feed
            
        Returns:
            Parsed feed data or None if fetch/parse failed
        """
        try:
            logger.info(f"Fetching feed from {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing error: {feed.bozo_exception}")
                return None
                
            return feed
            
        except Exception as e:
            logger.error(f"Error fetching feed from {url}: {e}")
            return None
    
    def process_source(self, source: Source) -> Dict[str, Any]:
        """
        Process a single RSS source.
        
        Args:
            source: Source object containing feed URL and metadata
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        result = {
            'source_id': source.id,
            'source_name': source.name,
            'articles_processed': 0,
            'status': 'success',
            'error': None,
            'processing_time': 0
        }
        
        # Start a new parsing log
        log = ParsingLog(
            source_id=source.id,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),  # Will be updated later
            articles_fetched=0,
            status='in_progress'
        )
        
        try:
            # Get the last parsing state
            last_state = self.db.get_parsing_state(source.id)
            last_link = last_state.last_article_link if last_state else None
            logger.info(f"Processing source: {source.name} (Last processed: {last_link or 'None'})")
            
            # Fetch the feed
            feed = self.fetch_feed(source.url)
            if not feed or not hasattr(feed, 'entries') or not feed.entries:
                raise ValueError("No entries found in feed")
            
            logger.info(f"Found {len(feed.entries)} entries in feed")
            
            # Process entries (newest first)
            new_articles = []
            for entry in feed.entries:
                link = getattr(entry, 'link', None)
                if not link:
                    continue
                    
                # Stop if we've reached the last processed article
                if last_link and link == last_link:
                    logger.info(f"Reached last processed article: {link}")
                    break
                    
                new_articles.append(entry)
            
            # Process new articles (oldest first to maintain order)
            new_articles_count = len(new_articles)
            logger.info(f"Found {new_articles_count} new articles to process")
            
            for entry in reversed(new_articles):
                try:
                    self.process_entry(source.id, entry)
                    result['articles_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing entry: {e}", exc_info=True)
            
            # Update parsing state if we have new articles
            if new_articles:
                latest_article = new_articles[0]  # Newest article is first
                self.db.update_parsing_state(ParsingState(
                    source_id=source.id,
                    last_article_link=getattr(latest_article, 'link', None),
                    last_parsed_at=datetime.now(timezone.utc)
                ))
            
            result['status'] = 'success'
            
        except Exception as e:
            logger.error(f"Error processing source {source.name}: {e}", exc_info=True)
            result['status'] = 'error'
            result['error'] = str(e)
        
        # Update processing time and log
        result['processing_time'] = time.time() - start_time
        log.finished_at = datetime.now(timezone.utc)
        log.status = result['status']
        log.articles_fetched = result['articles_processed']
        log.error_message = result.get('error')
        
        # Save the log
        self.db.create_parsing_log(log)
        
        logger.info(f"Finished processing {source.name}: {result}")
        return result
    
    def process_entry(self, source_id: str, entry: Any) -> Article:
        """
        Process a single feed entry and save it to the database.
        
        Args:
            source_id: ID of the source
            entry: Feed entry object
            
        Returns:
            Saved Article object
        """
        # Extract basic information
        link = getattr(entry, 'link', None)
        if not link:
            raise ValueError("Entry has no link")
        
        title = getattr(entry, 'title', 'No Title')
        logger.info(f"Processing article: {title[:50]}...")
        
        # Extract and clean content
        raw_content = extract_content_from_entry(entry)
        clean_content = clean_html_content(raw_content)
        
        # Create a description (first 300 chars of clean content)
        description = clean_content[:300] + "..." if len(clean_content) > 300 else clean_content
        
        # Parse publication date
        pub_date = parse_date_enhanced(entry)
        
        # Extract media information
        media_info = extract_media_info(entry)
        
        # Create article object
        article = Article(
            source_id=source_id,
            title=title,
            link=link,
            description=description,
            content=clean_content,
            pub_date=pub_date,
            media_info=media_info
        )
        
        # Save to database
        saved_article = self.db.insert_article(article)
        logger.info(f"Saved article: {saved_article.title[:50]}...")
        
        return saved_article
    
    def run(self):
        """
        Main execution method to process all RSS sources.
        """
        logger.info("Starting RSS loader")
        
        try:
            # Get all active RSS sources
            sources = self.db.get_sources()
            if not sources:
                logger.warning("No RSS sources found in the database")
                return
            
            logger.info(f"Found {len(sources)} sources to process")
            
            # Process each source
            for source in sources:
                self.process_source(source)
                
        except Exception as e:
            logger.error(f"Fatal error in RSS loader: {e}", exc_info=True)
        finally:
            logger.info("RSS loader finished")

if __name__ == "__main__":
    loader = RSSLoader()
    loader.run()
