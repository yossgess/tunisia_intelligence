import logging
import sys
import time
from typing import List, Dict, Any, Optional
import feedparser
from extractors.unified_extractor import UnifiedExtractor
from datetime import datetime, timezone

from config.database import DatabaseManager, Source, Article, ParsingState, ParsingLog
from config.settings import get_settings
from utils.date_utils import parse_date_enhanced
from utils.content_utils import extract_content_from_entry, clean_html_content, extract_media_info
from utils.deduplication import is_duplicate_article, get_content_deduplicator
from monitoring import start_session, end_session, record_source_start, record_source_end, get_metrics_collector

# Get application settings
settings = get_settings()

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.logging.level),
    format=settings.logging.format,
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler(settings.logging.file_path, encoding='utf-8')
    ]
)

# Configure console handler to handle UTF-8
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.stream.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

class RSSLoader:
    """
    RSS feed loader that handles fetching, parsing and storing RSS feed data.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.extractor = UnifiedExtractor()
        self.settings = get_settings()
        self.force_process_all = False  # Flag to force process all articles
        
        # Track extraction method statistics
        self.extraction_stats = {
            'unified_extractor_success': 0,
            'unified_extractor_failed': 0,
            'feedparser_fallback_success': 0,
            'feedparser_fallback_failed': 0,
            'total_failed': 0
        }
        
        # Set log level for httpx to WARNING to reduce noise
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        
        # Enable debug logging for our extractors if in debug mode
        if self.settings.debug:
            logging.getLogger('extractors').setLevel(logging.DEBUG)
        
        logger.info(f"RSS Loader initialized with environment: {self.settings.environment}")
        logger.info(f"Configuration: max_retries={self.settings.scraping.max_retries}, "
                   f"timeout={self.settings.scraping.initial_timeout}s, "
                   f"rate_limit={self.settings.scraping.rate_limit_delay}s")
    
    def fetch_feed(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed from the given URL using the UnifiedExtractor.
        
        Args:
            url: URL of the RSS feed
            
        Returns:
            Parsed feed data or None if fetch/parse failed
        """
        logger.info(f"Fetching feed from {url}")
        
        # First try with the unified extractor
        try:
            logger.info(f"🔍 TRYING: UnifiedExtractor for {url}")
            entries = self.extractor.extract(url)
            if entries:
                logger.info(f"✅ SUCCESS: UnifiedExtractor extracted {len(entries)} entries from {url}")
                self.extraction_stats['unified_extractor_success'] += 1
                # Convert dictionary entries to feedparser-like entry objects for backward compatibility
                feedparser_entries = []
                for entry_dict in entries:
                    # Create an object that supports both attribute access and dictionary operations
                    class FeedEntry:
                        def __init__(self, data):
                            self.__dict__.update(data)
                            self._data = data
                        
                        def __contains__(self, key):
                            return key in self._data
                        
                        def __getitem__(self, key):
                            return self._data[key]
                        
                        def get(self, key, default=None):
                            return self._data.get(key, default)
                    
                    entry_obj = FeedEntry(entry_dict)
                    feedparser_entries.append(entry_obj)
                
                return type('Feed', (), {'entries': feedparser_entries, 'bozo': False, 'bozo_exception': None, '_extraction_method': 'unified_extractor'})
        except Exception as e:
            logger.warning(f"❌ FAILED: UnifiedExtractor for {url}: {str(e)}")
            self.extraction_stats['unified_extractor_failed'] += 1
        
        # If unified extractor fails, try with direct feedparser
        try:
            logger.info(f"🔄 FALLBACK: Using direct feedparser for {url}")
            
            # Handle SSL issues for HTTPS URLs
            import ssl
            import urllib.request
            
            # Create a more lenient SSL context for problematic certificates
            if url.startswith('https://'):
                try:
                    # First try with default SSL verification
                    feed = feedparser.parse(url)
                except Exception as ssl_error:
                    if 'ssl' in str(ssl_error).lower() or 'certificate' in str(ssl_error).lower():
                        logger.warning(f"SSL error detected, trying with relaxed SSL verification: {ssl_error}")
                        # Create unverified SSL context as fallback
                        ssl_context = ssl.create_default_context()
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                        
                        # Try with custom SSL context
                        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
                        urllib.request.install_opener(opener)
                        feed = feedparser.parse(url)
                    else:
                        raise ssl_error
            else:
                feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing error: {feed.bozo_exception}")
                # Only fail if there are truly no entries AND it's a critical error
                if not feed.entries:
                    # Check if it's a recoverable error (like SSL or minor XML issues)
                    error_str = str(feed.bozo_exception).lower()
                    if any(recoverable in error_str for recoverable in ['ssl', 'certificate', 'mismatched tag', 'xml']):
                        logger.warning(f"Recoverable error detected, but no entries found: {feed.bozo_exception}")
                    else:
                        logger.error("No entries found in feed with critical error")
                    self.extraction_stats['feedparser_fallback_failed'] += 1
                    self.extraction_stats['total_failed'] += 1
                    return None
                else:
                    logger.info(f"Feed has parsing warnings but contains {len(feed.entries)} entries, proceeding...")
            
            if feed.entries:
                logger.info(f"✅ SUCCESS: Feedparser fallback extracted {len(feed.entries)} entries from {url}")
                self.extraction_stats['feedparser_fallback_success'] += 1
                feed._extraction_method = 'feedparser_fallback'
                return feed
                
        except Exception as e:
            logger.error(f"❌ FAILED: Feedparser fallback for {url}: {str(e)}")
            self.extraction_stats['feedparser_fallback_failed'] += 1
        
        logger.error(f"💥 ALL METHODS FAILED for {url}")
        self.extraction_stats['total_failed'] += 1
        return None
    
    def process_source(self, source: Source) -> Dict[str, Any]:
        """
        Process a single RSS source with detailed logging and error handling.
        
        Args:
            source: The source to process
            
        Returns:
            Dict containing processing results with the following structure:
            {
                'source_id': int,
                'source_name': str,
                'articles_processed': int,
                'status': str ('success' or 'failed'),
                'error': Optional[str],
                'processing_time': float,
                'start_time': datetime,
                'end_time': datetime,
                'new_articles': int,
                'skipped_articles': int,
                'duplicate_articles': int,
                'error_count': int
            }
        """
        # Start monitoring for this source
        source_metrics = record_source_start(source.id, source.name, source.url)
        
        # Initialize result dict with comprehensive tracking
        start_time = datetime.now(timezone.utc)
        result = {
            'source_id': source.id,
            'source_name': source.name,
            'articles_processed': 0,
            'new_articles': 0,
            'saved_articles': 0,
            'failed_saves': 0,
            'skipped_articles': 0,
            'duplicate_articles': 0,
            'error_count': 0,
            'status': 'failed',
            'error': None,
            'processing_time': 0.0,
            'start_time': start_time,
            'end_time': None,
            'last_processed_article': None,
            'feed_entries_found': 0,
            'extraction_method': 'unknown'
        }
        
        # Log source processing start
        logger.info(f"\n{'=' * 40}")
        logger.info(f"PROCESSING SOURCE: {source.name} (ID: {source.id})")
        logger.info(f"URL: {source.url}")
        logger.info(f"Started at: {result['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("-" * 40)
        
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
            last_link = last_state.last_article_link if last_state and not self.force_process_all else None
            
            # Debug logging
            if last_state:
                logger.debug(f"Found parsing state for source {source.id}: {last_state}")
                if self.force_process_all:
                    logger.debug(f"FORCE MODE: Ignoring last processed state")
            else:
                logger.debug(f"No parsing state found for source {source.id}")
            
            if self.force_process_all:
                logger.info(f"Processing source: {source.name} (FORCE MODE: Processing all articles)")
            else:
                logger.info(f"Processing source: {source.name} (Last processed: {last_link or 'None'})")
            
            # Fetch the feed
            logger.info(f"Processing source: {source.name} (ID: {source.id})")
            feed = self.fetch_feed(source.url)
            
            if not feed:
                error_msg = "Failed to fetch or parse feed"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning("No entries found in feed")
                result['status'] = 'success'  # Not an error, just no new content
                return result
            
            logger.info(f"Found {len(feed.entries)} entries in feed")
            result['feed_entries_found'] = len(feed.entries)
            result['extraction_method'] = getattr(feed, '_extraction_method', 'unknown')
            
            # Record articles found for monitoring
            metrics_collector = get_metrics_collector()
            metrics_collector.record_articles_found(source.id, len(feed.entries))
            
            # Process entries (newest first) - optimized for performance
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
            
            # Only process if there are new articles
            if new_articles_count > 0:
                # Batch process articles for better performance
                batch_size = min(10, len(new_articles))  # Process in batches of 10
                
                for i in range(0, len(new_articles), batch_size):
                    batch = list(reversed(new_articles[i:i+batch_size]))
                    
                    for entry in batch:
                        try:
                            # Quick duplicate check (skip expensive content extraction for duplicates)
                            if self.settings.content.enable_deduplication:
                                link = getattr(entry, 'link', '')
                                if link and self._is_duplicate_link(link):
                                    result['duplicate_articles'] += 1
                                    metrics_collector.record_duplicate_article(source.id)
                                    continue
                            
                            # Process the article (use fast mode if enabled)
                            if self.settings.scraping.fast_mode:
                                saved_article = self.process_entry_fast(source.id, entry)
                            else:
                                saved_article = self.process_entry(source.id, entry)
                            result['articles_processed'] += 1
                            
                            if saved_article:
                                result['new_articles'] += 1
                                result['saved_articles'] += 1
                                metrics_collector.record_article_processed(source.id, saved=True)
                            else:
                                result['skipped_articles'] += 1
                                result['failed_saves'] += 1
                                metrics_collector.record_article_processed(source.id, saved=False, skipped=True)
                                
                        except Exception as e:
                            logger.error(f"Error processing entry: {e}")
                            result['error_count'] += 1
                            metrics_collector.record_error(source.id, "processing", str(e))
            
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
            result['status'] = 'failed'
            result['error'] = str(e)
            # Record error in monitoring
            get_metrics_collector().record_error(source.id, "source_processing", str(e))
        
        # Calculate processing time
        result['end_time'] = datetime.now(timezone.utc)
        result['processing_time'] = (result['end_time'] - result['start_time']).total_seconds()
        
        # End monitoring for this source
        record_source_end(source.id, result['status'], result.get('error'))
        
        # Create parsing log
        log = ParsingLog(
            source_id=source.id,
            started_at=result['start_time'],
            finished_at=result['end_time'],
            articles_fetched=result['articles_processed'],
            status=result['status'],
            error_message=result['error']
        )
        
        # Save the log
        self.db.create_parsing_log(log)
        
        # Generate source summary
        self._log_source_summary(result)
        
        return result
    
    def _log_source_summary(self, result: Dict[str, Any]) -> None:
        """Log a comprehensive summary of source processing results."""
        logger.info("-" * 50)
        logger.info(f"PROCESSING SUMMARY - {result['source_name']} (ID: {result['source_id']})")
        logger.info("-" * 50)
        
        # Status and performance
        logger.info(f"Status:               {result['status'].upper()}")
        logger.info(f"Processing time:      {result['processing_time']:.2f} seconds")
        logger.info(f"Extraction method:    {result.get('extraction_method', 'unknown')}")
        
        # Feed statistics
        logger.info(f"Feed entries found:   {result.get('feed_entries_found', 0)}")
        logger.info(f"New articles:         {result.get('new_articles', 0)}")
        
        # Processing breakdown
        logger.info(f"Articles processed:   {result['articles_processed']}")
        logger.info(f"Successfully saved:   {result.get('saved_articles', 0)}")
        logger.info(f"Failed saves:         {result.get('failed_saves', 0)}")
        logger.info(f"Skipped articles:     {result.get('skipped_articles', 0)}")
        logger.info(f"Duplicate articles:   {result.get('duplicate_articles', 0)}")
        
        # Performance metrics
        if result['articles_processed'] > 0 and result['processing_time'] > 0:
            articles_per_second = result['articles_processed'] / result['processing_time']
            logger.info(f"Processing rate:      {articles_per_second:.1f} articles/second")
        
        # Success rate
        if result['articles_processed'] > 0:
            success_rate = (result.get('saved_articles', 0) / result['articles_processed']) * 100
            logger.info(f"Save success rate:    {success_rate:.1f}%")
        
        # Error information
        if result.get('error_count', 0) > 0:
            logger.warning(f"Errors encountered:   {result['error_count']}")
        
        # Error details if any
        if result['error']:
            logger.error(f"Error: {result['error']}")
        
        logger.info("=" * 50 + "\n")
    
    def _is_duplicate_link(self, link: str) -> bool:
        """Fast duplicate check using link only (avoids expensive content extraction)."""
        try:
            # Quick database check for existing link
            response = self.db.client.table("articles").select("id").eq("link", link).limit(1).execute()
            return len(response.data) > 0
        except Exception:
            return False
    
    def process_entry_fast(self, source_id: int, entry: Any) -> Optional[Article]:
        """
        Optimized version of process_entry with reduced content extraction overhead.
        """
        try:
            # Extract basic information
            link = getattr(entry, 'link', None)
            if not link:
                return None
            
            title = getattr(entry, 'title', 'No Title')
            
            # Skip expensive content extraction for RSS-only processing
            # Use basic content from RSS feed directly
            try:
                raw_content = extract_content_from_entry(entry)
                clean_content = clean_html_content(raw_content)
                
                article_data = {
                    'title': title,
                    'description': clean_content[:300] + "..." if len(clean_content) > 300 else clean_content,
                    'link': link,
                    'pub_date': parse_date_enhanced(entry),
                    'content': clean_content,
                    'source_id': source_id,
                    'created_at': datetime.now(timezone.utc)
                }
                
            except Exception:
                # Fallback to minimal data if content extraction fails
                article_data = {
                    'title': title,
                    'description': getattr(entry, 'summary', '')[:300],
                    'link': link,
                    'pub_date': parse_date_enhanced(entry),
                    'content': getattr(entry, 'summary', ''),
                    'source_id': source_id,
                    'created_at': datetime.now(timezone.utc)
                }
            
            # Create Article instance
            article = Article(
                title=article_data.get('title', ''),
                description=article_data.get('description', ''),
                link=article_data.get('link', ''),
                pub_date=article_data.get('pub_date'),
                content=article_data.get('content', ''),
                source_id=source_id,
                created_at=article_data.get('created_at', datetime.now(timezone.utc))
            )
            
            # Save to database (streamlined)
            return self.db.insert_article(article)
            
        except Exception as e:
            logger.debug(f"Error in fast processing: {e}")
            return None
    
    def process_entry(self, source_id: int, entry: Any) -> Optional[Article]:
        """
        Process a single feed entry and save it to the database.
        
        Args:
            source_id: ID of the source
            entry: Feed entry object
            
        Returns:
            Saved Article object or None if processing failed
        """
        try:
            # Extract basic information
            link = getattr(entry, 'link', None)
            if not link:
                logger.warning("Skipping entry with no link")
                return None
            
            title = getattr(entry, 'title', 'No Title')
            # Removed per-article logging for performance - will log summary at source level
            
            try:
                # Use the unified extractor to get the article content
                article_data = {
                    'source_id': source_id,
                    'title': title,
                    'link': link,
                    'created_at': datetime.now(timezone.utc)
                }
                
                # Get the full article content using the unified extractor
                entry_data = self.extractor.extract(link)
                if entry_data and isinstance(entry_data, list) and len(entry_data) > 0:
                    # Use the first entry if multiple are returned
                    entry_content = entry_data[0]
                    article_data.update({
                        'description': entry_content.get('description', ''),
                        'content': entry_content.get('content', ''),
                        'pub_date': entry_content.get('pub_date', parse_date_enhanced(entry)),
                        'media_info': entry_content.get('media_info', extract_media_info(entry))
                    })
                else:
                    # Fallback to the original extraction if unified extractor returns no results
                    raw_content = extract_content_from_entry(entry)
                    clean_content = clean_html_content(raw_content)
                    article_data.update({
                        'description': clean_content[:300] + "..." if len(clean_content) > 300 else clean_content,
                        'content': clean_content,
                        'pub_date': parse_date_enhanced(entry),
                        'media_info': extract_media_info(entry)
                    })
            except Exception as e:
                logger.error(f"Error extracting content for {link}: {e}")
                # Fallback to basic extraction
                raw_content = extract_content_from_entry(entry)
                clean_content = clean_html_content(raw_content)
                article_data.update({
                    'description': clean_content[:300] + "..." if len(clean_content) > 300 else clean_content,
                    'content': clean_content,
                    'pub_date': parse_date_enhanced(entry),
                    'media_info': extract_media_info(entry)
                })
            
            # Add category if available
            category = getattr(entry, 'category', None)
            if category:
                if isinstance(category, list):
                    article_data['category'] = ', '.join(category)
                else:
                    article_data['category'] = str(category)
            
            # Ensure all required fields are present and properly formatted
            # Keep 'link' field consistent with database schema
            if 'url' in article_data and 'link' not in article_data:
                article_data['link'] = article_data.pop('url')
            elif 'url' in article_data:
                # Remove 'url' if both exist, keep 'link'
                article_data.pop('url', None)
            
            # Create Article instance with the correct field names
            article = Article(
                title=article_data.get('title', ''),
                description=article_data.get('description', ''),
                link=article_data.get('link', ''),
                pub_date=article_data.get('pub_date'),
                content=article_data.get('content', ''),
                source_id=source_id,
                created_at=article_data.get('created_at', datetime.now(timezone.utc)),
                media_url=article_data.get('media_info', {}).get('url') if article_data.get('media_info') else None
            )
            
            # Save to database (removed verbose logging for performance)
            saved_article = self.db.insert_article(article)
            return saved_article
            
        except Exception as e:
            logger.error(f"Error processing entry: {e}", exc_info=True)
            return None
    
    def run(self):
        """
        Main execution method to process all RSS sources with detailed reporting.
        """
        # Initialize statistics
        start_time = datetime.now(timezone.utc)
        session_id = f"rss_session_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Start monitoring session
        session_metrics = start_session(session_id)
        
        total_sources = 0
        total_articles = 0
        sources_processed = 0
        sources_with_errors = 0
        error_details = []  # Track detailed error information
        
        # Log start of processing
        logger.info("=" * 80)
        logger.info(f"RSS LOADER STARTED AT {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Environment: {self.settings.environment}")
        logger.info(f"Deduplication: {'enabled' if self.settings.content.enable_deduplication else 'disabled'}")
        logger.info("=" * 80)
        
        try:
            # Get all active RSS sources
            sources = self.db.get_sources()
            total_sources = len(sources)
            logger.info(f"Found {total_sources} active sources to process")
            
            # Process each source
            for source in sources:
                try:
                    result = self.process_source(source)
                    if result:
                        total_articles += result.get('articles_processed', 0)
                        if result.get('status') == 'failed':
                            sources_with_errors += 1
                        sources_processed += 1
                except Exception as e:
                    error_msg = f"Error processing source {source.name} (ID: {source.id}): {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    error_details.append({
                        'source_id': source.id,
                        'source_name': source.name,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
                    sources_with_errors += 1
            
            # Generate final report
            self._generate_summary_report({
                'start_time': start_time,
                'end_time': datetime.now(timezone.utc),
                'total_sources': total_sources,
                'sources_processed': sources_processed,
                'sources_with_errors': sources_with_errors,
                'error_details': error_details,
                'total_articles_processed': total_articles
            })
            
        except Exception as e:
            logger.error(f"Fatal error in RSS loader: {e}", exc_info=True)
            get_metrics_collector().record_error(0, "fatal_error", str(e))
            raise
        finally:
            # End monitoring session
            final_metrics = end_session()
            if final_metrics and self.settings.monitoring.enabled:
                # Export metrics if monitoring is enabled
                metrics_file = f"metrics_{session_id}.json"
                get_metrics_collector().export_metrics(metrics_file)
                logger.info(f"Session metrics exported to: {metrics_file}")
            
            # Clear deduplication cache if enabled
            if self.settings.content.enable_deduplication:
                from utils.deduplication import clear_deduplication_cache
                clear_deduplication_cache()
                logger.info("Deduplication cache cleared")
            
            # Ensure proper terminal cleanup
            try:
                import sys
                sys.stdout.flush()
                sys.stderr.flush()
                logger.info("RSS Loader session completed successfully")
            except Exception as e:
                logger.debug(f"Terminal cleanup warning: {e}")
    
    def _generate_summary_report(self, stats: Dict[str, Any]) -> None:
        """Generate and log a summary report of the RSS loading process."""
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("RSS LOADER SUMMARY REPORT")
        logger.info("=" * 80)
        logger.info(f"Processing started:    {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Processing finished:   {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Total duration:        {duration:.2f} seconds")
        logger.info("-" * 80)
        logger.info(f"Total sources:         {stats['total_sources']}")
        logger.info(f"Successfully processed: {stats['sources_processed'] - stats['sources_with_errors']}")
        logger.info(f"Sources with errors:   {stats['sources_with_errors']}")
        logger.info(f"Total articles processed: {stats['total_articles_processed']}")
        
        if stats['total_sources'] > 0:
            avg_articles = stats['total_articles_processed'] / (stats['sources_processed'] or 1)
            logger.info(f"Average articles per source: {avg_articles:.1f}")
        
        # Enhanced extraction method statistics
        logger.info("-" * 80)
        logger.info("EXTRACTION METHOD PERFORMANCE")
        logger.info("-" * 80)
        logger.info(f"✅ UnifiedExtractor Success:     {self.extraction_stats['unified_extractor_success']}")
        logger.info(f"❌ UnifiedExtractor Failed:      {self.extraction_stats['unified_extractor_failed']}")
        logger.info(f"🔄 Feedparser Fallback Success: {self.extraction_stats['feedparser_fallback_success']}")
        logger.info(f"❌ Feedparser Fallback Failed:  {self.extraction_stats['feedparser_fallback_failed']}")
        logger.info(f"💥 Total Complete Failures:     {self.extraction_stats['total_failed']}")
        
        # Calculate comprehensive success rates
        total_sources = stats['total_sources']
        if total_sources > 0:
            unified_success_rate = (self.extraction_stats['unified_extractor_success'] / total_sources) * 100
            fallback_usage_rate = (self.extraction_stats['feedparser_fallback_success'] / total_sources) * 100
            overall_success_rate = ((self.extraction_stats['unified_extractor_success'] + self.extraction_stats['feedparser_fallback_success']) / total_sources) * 100
            
            logger.info(f"📊 UnifiedExtractor Success Rate: {unified_success_rate:.1f}%")
            logger.info(f"📊 Fallback Usage Rate:          {fallback_usage_rate:.1f}%")
            logger.info(f"📊 Overall Extraction Success:   {overall_success_rate:.1f}%")
        
        # Performance metrics
        logger.info("-" * 80)
        logger.info("PERFORMANCE METRICS")
        logger.info("-" * 80)
        if stats['total_articles_processed'] > 0 and duration > 0:
            articles_per_second = stats['total_articles_processed'] / duration
            sources_per_minute = (stats['sources_processed'] / duration) * 60
            logger.info(f"⚡ Processing Speed:             {articles_per_second:.1f} articles/second")
            logger.info(f"⚡ Source Processing Rate:       {sources_per_minute:.1f} sources/minute")
            logger.info(f"⚡ Average Time per Source:      {duration/stats['sources_processed']:.2f} seconds")
        
        # Memory and efficiency metrics
        logger.info(f"🔧 Total Feed Entries Processed: {sum(getattr(result, 'feed_entries_found', 0) for result in stats.get('detailed_results', []))}")
        logger.info(f"🔧 Extraction Efficiency:        {(stats['total_articles_processed']/max(1, sum(getattr(result, 'feed_entries_found', 0) for result in stats.get('detailed_results', []))))*100:.1f}%")
        
        # Display detailed error information if any
        if stats['sources_with_errors'] > 0:
            logger.info("\n" + "!" * 80)
            logger.info(f"DETAILED ERROR REPORT ({stats['sources_with_errors']} SOURCES WITH ERRORS)")
            logger.info("!" * 80)
            for error in stats['error_details']:
                logger.error(f"\nSOURCE: {error['source_name']} (ID: {error['source_id']})")
                logger.error(f"ERROR: {error['error']}")
                # Log the full traceback at debug level to avoid cluttering the main log
                logger.debug(f"TRACEBACK:\n{error['traceback']}")
            logger.info("!" * 80 + "\n")
        
        logger.info("=" * 80 + "\n")

def main():
    """Main function with proper signal handling and cleanup."""
    import signal
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tunisia Intelligence RSS Loader')
    parser.add_argument('--force-all', action='store_true', 
                       help='Force process all articles, ignoring last processed state')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of sources to process (for testing)')
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug logging enabled")
    
    def signal_handler(signum, frame):
        """Handle interrupt signals gracefully."""
        logger.info("\n🛑 Received interrupt signal. Cleaning up...")
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        loader = RSSLoader()
        if args.force_all:
            logger.info("🔄 FORCE MODE: Processing all articles regardless of last processed state")
            loader.force_process_all = True
        loader.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Final cleanup
        sys.stdout.flush()
        sys.stderr.flush()
        logger.info("🎯 RSS Loader terminated cleanly")


if __name__ == "__main__":
    main()
