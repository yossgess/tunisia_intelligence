"""
Main AI Enrichment Service.

This module provides the main orchestration service for AI-powered content enrichment,
integrating all processors and managing database operations.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from ..core.ollama_client import OllamaClient, OllamaConfig
from ..processors.sentiment_analyzer import SentimentAnalyzer
from ..processors.entity_extractor import EntityExtractor
from ..processors.keyword_extractor import KeywordExtractor
from ..processors.category_classifier import CategoryClassifier
from ..models.enrichment_models import (
    EnrichmentResult, EnrichmentRequest, ProcessingStatus,
    SentimentResult, EntityResult, KeywordResult, CategoryResult,
    ProcessingMetadata, LanguageCode
)

# Import existing database components
from ...config.database import DatabaseManager, Article

logger = logging.getLogger(__name__)

class EnrichmentService:
    """
    Main service for AI-powered content enrichment.
    
    Orchestrates all AI processors and manages database integration
    for comprehensive content analysis.
    """
    
    def __init__(
        self,
        ollama_config: Optional[OllamaConfig] = None,
        db_manager: Optional[DatabaseManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enrichment service.
        
        Args:
            ollama_config: Configuration for Ollama client
            db_manager: Database manager instance
            config: Service configuration
        """
        self.config = config or {}
        self.db_manager = db_manager or DatabaseManager()
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient(ollama_config)
        
        # Initialize processors
        self.sentiment_analyzer = SentimentAnalyzer(self.ollama_client, self.config.get('sentiment', {}))
        self.entity_extractor = EntityExtractor(self.ollama_client, self.config.get('entities', {}))
        self.keyword_extractor = KeywordExtractor(self.ollama_client, self.config.get('keywords', {}))
        self.category_classifier = CategoryClassifier(self.ollama_client, self.config.get('categories', {}))
        
        # Service configuration
        self.default_config = {
            'parallel_processing': True,
            'max_workers': 4,
            'timeout': 300,  # 5 minutes timeout
            'retry_failed': True,
            'max_retries': 2,
            'save_to_database': True,
            'update_existing': True
        }
        
        self.config = {**self.default_config, **self.config}
        
        # Validate Ollama connection
        if not self.ollama_client.health_check():
            logger.warning("Ollama service is not available - enrichment will fail")
    
    def enrich_content(
        self,
        content: str,
        content_type: str = "article",
        content_id: Optional[int] = None,
        options: Optional[Dict[str, bool]] = None
    ) -> EnrichmentResult:
        """
        Enrich a single piece of content with AI analysis.
        
        Args:
            content: Text content to enrich
            content_type: Type of content ('article', 'social_media_post', 'comment')
            content_id: Optional ID of the content in database
            options: Processing options (enable_sentiment, enable_entities, etc.)
            
        Returns:
            EnrichmentResult with all analysis results
        """
        start_time = time.time()
        
        # Default processing options
        default_options = {
            'enable_sentiment': True,
            'enable_entities': True,
            'enable_keywords': True,
            'enable_categories': True,
            'enable_summary': False
        }
        options = {**default_options, **(options or {})}
        
        logger.info(f"Starting enrichment for {content_type} (ID: {content_id})")
        
        try:
            # Initialize result
            result = EnrichmentResult(
                content_id=content_id,
                content_type=content_type,
                status=ProcessingStatus.PENDING,
                confidence=0.0
            )
            
            # Process in parallel if enabled
            if self.config['parallel_processing']:
                result = self._enrich_parallel(content, result, options)
            else:
                result = self._enrich_sequential(content, result, options)
            
            # Calculate overall processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Create processing metadata
            result.metadata = ProcessingMetadata(
                processor="enrichment_service",
                model=self.ollama_client.config.model,
                processing_time=processing_time,
                content_length=len(content)
            )
            
            # Save to database if enabled
            if self.config['save_to_database'] and content_id:
                self._save_enrichment_to_database(result)
            
            logger.info(f"Enrichment completed in {processing_time:.2f}s with confidence {result.confidence:.2f}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enrichment failed after {processing_time:.2f}s: {e}")
            
            return EnrichmentResult(
                content_id=content_id,
                content_type=content_type,
                status=ProcessingStatus.FAILED,
                confidence=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _enrich_parallel(
        self,
        content: str,
        result: EnrichmentResult,
        options: Dict[str, bool]
    ) -> EnrichmentResult:
        """
        Process content with parallel AI analysis.
        
        Args:
            content: Content to process
            result: Result object to populate
            options: Processing options
            
        Returns:
            Updated EnrichmentResult
        """
        tasks = []
        
        # Prepare processing tasks
        if options.get('enable_sentiment'):
            tasks.append(('sentiment', self.sentiment_analyzer.process, content))
        
        if options.get('enable_entities'):
            tasks.append(('entities', self.entity_extractor.process, content))
        
        if options.get('enable_keywords'):
            tasks.append(('keywords', self.keyword_extractor.process, content))
        
        if options.get('enable_categories'):
            tasks.append(('categories', self.category_classifier.process, content))
        
        # Execute tasks in parallel
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            future_to_task = {
                executor.submit(task_func, task_content): task_name
                for task_name, task_func, task_content in tasks
            }
            
            completed_tasks = 0
            failed_tasks = 0
            
            for future in as_completed(future_to_task, timeout=self.config['timeout']):
                task_name = future_to_task[future]
                
                try:
                    task_result = future.result()
                    
                    if task_result.status == ProcessingStatus.SUCCESS:
                        self._apply_task_result(result, task_name, task_result)
                        completed_tasks += 1
                    else:
                        logger.warning(f"Task {task_name} failed: {task_result.error}")
                        failed_tasks += 1
                        
                except Exception as e:
                    logger.error(f"Task {task_name} raised exception: {e}")
                    failed_tasks += 1
        
        # Determine overall status
        if completed_tasks > 0:
            result.status = ProcessingStatus.SUCCESS if failed_tasks == 0 else ProcessingStatus.PARTIAL
        else:
            result.status = ProcessingStatus.FAILED
            result.error_message = "All processing tasks failed"
        
        return result
    
    def _enrich_sequential(
        self,
        content: str,
        result: EnrichmentResult,
        options: Dict[str, bool]
    ) -> EnrichmentResult:
        """
        Process content with sequential AI analysis.
        
        Args:
            content: Content to process
            result: Result object to populate
            options: Processing options
            
        Returns:
            Updated EnrichmentResult
        """
        completed_tasks = 0
        failed_tasks = 0
        
        # Sentiment analysis
        if options.get('enable_sentiment'):
            try:
                sentiment_result = self.sentiment_analyzer.process(content)
                if sentiment_result.status == ProcessingStatus.SUCCESS:
                    self._apply_task_result(result, 'sentiment', sentiment_result)
                    completed_tasks += 1
                else:
                    failed_tasks += 1
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                failed_tasks += 1
        
        # Entity extraction
        if options.get('enable_entities'):
            try:
                entity_result = self.entity_extractor.process(content)
                if entity_result.status == ProcessingStatus.SUCCESS:
                    self._apply_task_result(result, 'entities', entity_result)
                    completed_tasks += 1
                else:
                    failed_tasks += 1
            except Exception as e:
                logger.error(f"Entity extraction failed: {e}")
                failed_tasks += 1
        
        # Keyword extraction
        if options.get('enable_keywords'):
            try:
                keyword_result = self.keyword_extractor.process(content)
                if keyword_result.status == ProcessingStatus.SUCCESS:
                    self._apply_task_result(result, 'keywords', keyword_result)
                    completed_tasks += 1
                else:
                    failed_tasks += 1
            except Exception as e:
                logger.error(f"Keyword extraction failed: {e}")
                failed_tasks += 1
        
        # Category classification
        if options.get('enable_categories'):
            try:
                category_result = self.category_classifier.process(content)
                if category_result.status == ProcessingStatus.SUCCESS:
                    self._apply_task_result(result, 'categories', category_result)
                    completed_tasks += 1
                else:
                    failed_tasks += 1
            except Exception as e:
                logger.error(f"Category classification failed: {e}")
                failed_tasks += 1
        
        # Determine overall status
        if completed_tasks > 0:
            result.status = ProcessingStatus.SUCCESS if failed_tasks == 0 else ProcessingStatus.PARTIAL
        else:
            result.status = ProcessingStatus.FAILED
            result.error_message = "All processing tasks failed"
        
        return result
    
    def _apply_task_result(
        self,
        result: EnrichmentResult,
        task_name: str,
        task_result: Any
    ) -> None:
        """
        Apply individual task result to the overall enrichment result.
        
        Args:
            result: Main enrichment result
            task_name: Name of the completed task
            task_result: Result from the task
        """
        if task_name == 'sentiment' and task_result.data:
            result.sentiment = SentimentResult(
                sentiment=task_result.data['sentiment'],
                sentiment_score=task_result.data.get('sentiment_score', 0),
                confidence=task_result.confidence,
                reasoning=task_result.data.get('reasoning'),
                emotions=task_result.data.get('emotions', []),
                language_detected=task_result.data.get('language_detected')
            )
            
        elif task_name == 'entities' and task_result.data:
            entities = task_result.data.get('entities', [])
            result.entities = [
                EntityResult(
                    text=entity['text'],
                    type=entity['type'],
                    confidence=entity['confidence'],
                    canonical_name=entity.get('canonical_name'),
                    context=entity.get('context'),
                    is_tunisian=entity.get('is_tunisian', False)
                )
                for entity in entities
            ]
            
        elif task_name == 'keywords' and task_result.data:
            keywords = task_result.data.get('keywords', [])
            result.keywords = [
                KeywordResult(
                    text=keyword['text'],
                    type=keyword.get('type', 'single_word'),
                    importance=keyword['importance'],
                    frequency=keyword.get('frequency', 1),
                    category=keyword.get('category', 'other'),
                    is_phrase=keyword.get('is_phrase', False),
                    language=keyword.get('language')
                )
                for keyword in keywords
            ]
            
        elif task_name == 'categories' and task_result.data:
            result.category = CategoryResult(
                primary_category=task_result.data['primary_category'],
                secondary_categories=task_result.data.get('secondary_categories', []),
                confidence=task_result.confidence,
                reasoning=task_result.data.get('reasoning'),
                subcategories=task_result.data.get('subcategories', []),
                category_path=task_result.data.get('category_path')
            )
        
        # Update language detection
        if hasattr(task_result, 'data') and task_result.data:
            detected_lang = task_result.data.get('language_detected')
            if detected_lang and not result.language_detected:
                result.language_detected = detected_lang
    
    def _save_enrichment_to_database(self, result: EnrichmentResult) -> None:
        """
        Save enrichment results to the database.
        
        Args:
            result: Enrichment result to save
        """
        try:
            if result.content_type == 'article' and result.content_id:
                self._update_article_enrichment(result)
            elif result.content_type == 'social_media_post' and result.content_id:
                self._update_social_media_post_enrichment(result)
            elif result.content_type == 'comment' and result.content_id:
                self._update_comment_enrichment(result)
                
        except Exception as e:
            logger.error(f"Failed to save enrichment to database: {e}")
    
    def _update_article_enrichment(self, result: EnrichmentResult) -> None:
        """Update article with enrichment results."""
        update_data = {}
        
        # Update sentiment
        if result.sentiment:
            update_data['sentiment'] = result.sentiment.sentiment.value
            update_data['sentiment_score'] = result.sentiment.sentiment_score
        
        # Update keywords (as JSON string)
        if result.keywords:
            import json
            keywords_data = [
                {
                    'text': kw.text,
                    'importance': kw.importance,
                    'category': kw.category
                }
                for kw in result.keywords[:10]  # Limit to top 10
            ]
            update_data['keywords'] = json.dumps(keywords_data, ensure_ascii=False)
        
        # Update category
        if result.category:
            update_data['category'] = result.category.primary_category
            # Also update category_id if we have it
            if result.category.category_id:
                update_data['category_id'] = result.category.category_id
        
        # Update summary if available
        if result.summary:
            update_data['summary'] = result.summary
        
        if update_data:
            try:
                # Use Supabase client to update article
                response = self.db_manager.client.table("news_articles") \
                    .update(update_data) \
                    .eq("id", result.content_id) \
                    .execute()
                
                if response.data:
                    logger.info(f"Updated article {result.content_id} with enrichment data")
                else:
                    logger.warning(f"No article found with ID {result.content_id}")
                    
            except Exception as e:
                logger.error(f"Failed to update article {result.content_id}: {e}")
    
    def _update_social_media_post_enrichment(self, result: EnrichmentResult) -> None:
        """Update social media post with enrichment results."""
        update_data = {}
        
        # Update sentiment
        if result.sentiment:
            # Note: Would need to create/link to sentiment record first
            update_data['sentiment_score'] = result.sentiment.sentiment_score
        
        # Update summary
        if result.summary:
            update_data['summary'] = result.summary
        
        if update_data:
            try:
                response = self.db_manager.client.table("social_media_posts") \
                    .update(update_data) \
                    .eq("id", result.content_id) \
                    .execute()
                
                if response.data:
                    logger.info(f"Updated social media post {result.content_id} with enrichment data")
                    
            except Exception as e:
                logger.error(f"Failed to update social media post {result.content_id}: {e}")
    
    def _update_comment_enrichment(self, result: EnrichmentResult) -> None:
        """Update comment with enrichment results."""
        update_data = {}
        
        # Update sentiment
        if result.sentiment:
            update_data['sentiment_score'] = result.sentiment.sentiment_score
        
        if update_data:
            try:
                response = self.db_manager.client.table("social_media_comments") \
                    .update(update_data) \
                    .eq("id", result.content_id) \
                    .execute()
                
                if response.data:
                    logger.info(f"Updated comment {result.content_id} with enrichment data")
                    
            except Exception as e:
                logger.error(f"Failed to update comment {result.content_id}: {e}")
    
    def enrich_from_request(self, request: EnrichmentRequest) -> EnrichmentResult:
        """
        Enrich content from an EnrichmentRequest.
        
        Args:
            request: Enrichment request with content and options
            
        Returns:
            EnrichmentResult
        """
        options = {
            'enable_sentiment': request.enable_sentiment,
            'enable_entities': request.enable_entities,
            'enable_keywords': request.enable_keywords,
            'enable_categories': request.enable_categories,
            'enable_summary': request.enable_summary
        }
        
        return self.enrich_content(
            content=request.content,
            content_type=request.content_type,
            content_id=request.content_id,
            options=options
        )
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of the enrichment service.
        
        Returns:
            Status information dictionary
        """
        return {
            'ollama_available': self.ollama_client.health_check(),
            'ollama_model': self.ollama_client.config.model,
            'database_connected': True,  # Assume connected if no exception
            'processors': {
                'sentiment_analyzer': True,
                'entity_extractor': True,
                'keyword_extractor': True,
                'category_classifier': True
            },
            'configuration': {
                'parallel_processing': self.config['parallel_processing'],
                'max_workers': self.config['max_workers'],
                'save_to_database': self.config['save_to_database']
            }
        }
    
    def test_processors(self, test_content: str = "هذا نص تجريبي للاختبار") -> Dict[str, Any]:
        """
        Test all processors with sample content.
        
        Args:
            test_content: Content to use for testing
            
        Returns:
            Test results for each processor
        """
        results = {}
        
        # Test sentiment analyzer
        try:
            sentiment_result = self.sentiment_analyzer.process(test_content)
            results['sentiment'] = {
                'status': sentiment_result.status.value,
                'confidence': sentiment_result.confidence,
                'processing_time': sentiment_result.processing_time
            }
        except Exception as e:
            results['sentiment'] = {'status': 'error', 'error': str(e)}
        
        # Test entity extractor
        try:
            entity_result = self.entity_extractor.process(test_content)
            results['entities'] = {
                'status': entity_result.status.value,
                'confidence': entity_result.confidence,
                'processing_time': entity_result.processing_time,
                'entities_found': len(entity_result.data.get('entities', [])) if entity_result.data else 0
            }
        except Exception as e:
            results['entities'] = {'status': 'error', 'error': str(e)}
        
        # Test keyword extractor
        try:
            keyword_result = self.keyword_extractor.process(test_content)
            results['keywords'] = {
                'status': keyword_result.status.value,
                'confidence': keyword_result.confidence,
                'processing_time': keyword_result.processing_time,
                'keywords_found': len(keyword_result.data.get('keywords', [])) if keyword_result.data else 0
            }
        except Exception as e:
            results['keywords'] = {'status': 'error', 'error': str(e)}
        
        # Test category classifier
        try:
            category_result = self.category_classifier.process(test_content)
            results['categories'] = {
                'status': category_result.status.value,
                'confidence': category_result.confidence,
                'processing_time': category_result.processing_time,
                'primary_category': category_result.data.get('primary_category') if category_result.data else None
            }
        except Exception as e:
            results['categories'] = {'status': 'error', 'error': str(e)}
        
        return results
