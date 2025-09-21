"""
Configurable AI Enrichment Service for Tunisia Intelligence System

This service integrates with the new configuration and prompts system to provide
flexible, tunable AI enrichment processing for all content types.
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ..core.ollama_client import OllamaClient, OllamaConfig
from config.database import DatabaseManager
from config.ai_enrichment_config import (
    get_ai_enrichment_config, ContentType, ProcessingMode,
    get_article_settings, get_post_settings, get_comment_settings,
    get_model_settings, get_rate_limiting_settings, get_quality_control_settings
)
from config.ai_enrichment_prompts import (
    get_ai_enrichment_prompts, PromptType,
    get_article_prompt, get_post_prompt, get_comment_prompt
)

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentResult:
    """Result of AI enrichment processing."""
    success: bool
    content_id: int
    content_type: ContentType
    processing_time_ms: int
    confidence: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConfigurableEnrichmentService:
    """
    Configurable AI Enrichment Service with dynamic parameter tuning.
    
    Features:
    - Uses configuration system for all parameters
    - Dynamic prompt selection and customization
    - Content type specific processing
    - Rate limiting and quality control
    - Dashboard integration ready
    """
    
    def __init__(self):
        """Initialize the configurable enrichment service."""
        self.db_manager = DatabaseManager()
        self.config = get_ai_enrichment_config()
        self.prompts = get_ai_enrichment_prompts()
        
        # Initialize Ollama client with model settings
        model_settings = get_model_settings()
        ollama_config = OllamaConfig(
            base_url=model_settings.ollama_url,
            model=model_settings.model_name,
            timeout=model_settings.ollama_timeout
        )
        self.ollama_client = OllamaClient(ollama_config)
        
        # Rate limiting state
        self._request_history = []
        
        logger.info("Configurable enrichment service initialized")
    
    def enrich_content(self, content_id: int, content_type: ContentType, 
                      content: str, force_reprocess: bool = False) -> EnrichmentResult:
        """
        Enrich a single piece of content using configurable parameters.
        
        Args:
            content_id: Database ID of the content
            content_type: Type of content (article, post, comment)
            content: Text content to enrich
            force_reprocess: Force reprocessing even if already enriched
            
        Returns:
            EnrichmentResult with processing outcome
        """
        start_time = time.time()
        
        try:
            # Check if content type is enabled
            if not self.config.is_content_type_enabled(content_type):
                return EnrichmentResult(
                    success=False,
                    content_id=content_id,
                    content_type=content_type,
                    processing_time_ms=0,
                    confidence=0.0,
                    error=f"Content type {content_type} is disabled"
                )
            
            # Get content type specific settings
            settings = self.config.get_content_type_settings(content_type)
            
            # Validate content length
            if len(content) < settings.min_content_length:
                return EnrichmentResult(
                    success=False,
                    content_id=content_id,
                    content_type=content_type,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    confidence=0.0,
                    error=f"Content too short: {len(content)} < {settings.min_content_length}"
                )
            
            if len(content) > settings.max_content_length:
                content = content[:settings.max_content_length]
                logger.warning(f"Content truncated to {settings.max_content_length} characters")
            
            # Apply rate limiting
            if not self._check_rate_limit(content_type):
                return EnrichmentResult(
                    success=False,
                    content_id=content_id,
                    content_type=content_type,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    confidence=0.0,
                    error="Rate limit exceeded"
                )
            
            # Detect language and translate if needed
            language_detected = self._detect_language(content)
            if language_detected == 'ar' and settings.enable_translation:
                content_fr = self._translate_content(content, content_type)
            else:
                content_fr = content
            
            # Perform AI enrichment based on processing mode
            enrichment_data = self._perform_enrichment(
                content_fr, content_type, settings, language_detected
            )
            
            # Validate results
            if not self._validate_enrichment_result(enrichment_data, settings):
                return EnrichmentResult(
                    success=False,
                    content_id=content_id,
                    content_type=content_type,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    confidence=0.0,
                    error="Enrichment result validation failed"
                )
            
            # Update database
            if enrichment_data.get('confidence', 0) >= settings.min_confidence_threshold:
                self._update_database(content_id, content_type, enrichment_data, content_fr)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return EnrichmentResult(
                success=True,
                content_id=content_id,
                content_type=content_type,
                processing_time_ms=processing_time_ms,
                confidence=enrichment_data.get('confidence', 0.0),
                data=enrichment_data
            )
            
        except Exception as e:
            logger.error(f"Enrichment failed for {content_type} {content_id}: {e}")
            return EnrichmentResult(
                success=False,
                content_id=content_id,
                content_type=content_type,
                processing_time_ms=int((time.time() - start_time) * 1000),
                confidence=0.0,
                error=str(e)
            )
    
    def _perform_enrichment(self, content: str, content_type: ContentType, 
                           settings: Any, language: str) -> Dict[str, Any]:
        """Perform AI enrichment based on processing mode and settings."""
        
        # Determine prompt type based on processing mode
        if settings.processing_mode == ProcessingMode.FULL:
            if content_type == ContentType.COMMENT and settings.enable_enhanced_processing:
                prompt_type = PromptType.ENHANCED_COMMENT
            else:
                prompt_type = PromptType.FULL_ENRICHMENT
        elif settings.processing_mode == ProcessingMode.SENTIMENT_ONLY:
            prompt_type = PromptType.SENTIMENT_ONLY
        elif settings.processing_mode == ProcessingMode.KEYWORDS_ONLY:
            prompt_type = PromptType.KEYWORDS_ONLY
        elif settings.processing_mode == ProcessingMode.ENTITIES_ONLY:
            prompt_type = PromptType.ENTITIES_ONLY
        else:
            prompt_type = PromptType.FULL_ENRICHMENT
        
        # Get prompt with template variables
        prompt_vars = {
            'content': content,
            'max_keywords': getattr(settings, 'max_keywords', 10),
            'max_entities': getattr(settings, 'max_entities', 15),
            'summary_max_length': getattr(settings, 'summary_max_length', 500)
        }
        
        prompt = self.prompts.get_prompt(content_type, prompt_type, **prompt_vars)
        
        # Get model settings
        model_settings = get_model_settings()
        
        # Make AI request
        response = self.ollama_client.generate(
            model=model_settings.model_name,
            prompt=prompt,
            options={
                "temperature": model_settings.temperature,
                "top_p": model_settings.top_p,
                "num_predict": model_settings.max_tokens
            }
        )
        
        # Parse response
        try:
            result = json.loads(response.get('response', '{}'))
            
            # Add metadata
            result['language_detected'] = language
            result['processing_metadata'] = {
                'model_version': model_settings.model_name,
                'prompt_type': prompt_type.value,
                'processing_mode': settings.processing_mode.value
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._get_fallback_result(content_type, settings)
    
    def _get_fallback_result(self, content_type: ContentType, settings: Any) -> Dict[str, Any]:
        """Get fallback result when AI processing fails."""
        return {
            'sentiment': 'neutral',
            'sentiment_score': 0.5,
            'keywords': [],
            'entities': [],
            'confidence': 0.1,
            'language_detected': 'unknown',
            'processing_metadata': {
                'fallback_used': True,
                'processing_mode': settings.processing_mode.value
            }
        }
    
    def _check_rate_limit(self, content_type: ContentType) -> bool:
        """Check if request is within rate limits."""
        rate_settings = get_rate_limiting_settings()
        current_time = time.time()
        
        # Clean old requests
        self._request_history = [
            req_time for req_time in self._request_history 
            if current_time - req_time < 60  # Keep last minute
        ]
        
        # Check global rate limit
        if len(self._request_history) >= rate_settings.requests_per_minute:
            return False
        
        # Check content type specific limits
        content_type_limits = {
            ContentType.ARTICLE: rate_settings.articles_per_minute,
            ContentType.POST: rate_settings.posts_per_minute,
            ContentType.COMMENT: rate_settings.comments_per_minute
        }
        
        content_type_requests = [
            req for req in self._request_history 
            if req.get('content_type') == content_type
        ]
        
        if len(content_type_requests) >= content_type_limits.get(content_type, 10):
            return False
        
        # Record this request
        self._request_history.append({
            'time': current_time,
            'content_type': content_type
        })
        
        return True
    
    def _detect_language(self, content: str) -> str:
        """Detect content language."""
        # Simple language detection based on character patterns
        arabic_chars = sum(1 for c in content if '\u0600' <= c <= '\u06FF')
        total_chars = len([c for c in content if c.isalpha()])
        
        if total_chars == 0:
            return 'unknown'
        
        arabic_ratio = arabic_chars / total_chars
        
        if arabic_ratio > 0.3:
            return 'ar'
        elif any(word in content.lower() for word in ['le', 'la', 'les', 'de', 'du', 'des']):
            return 'fr'
        else:
            return 'en'
    
    def _translate_content(self, content: str, content_type: ContentType) -> str:
        """Translate Arabic content to French."""
        try:
            prompt = self.prompts.get_prompt(content_type, PromptType.TRANSLATION, content=content)
            
            model_settings = get_model_settings()
            response = self.ollama_client.generate(
                model=model_settings.model_name,
                prompt=prompt,
                options={"temperature": 0.1}
            )
            
            result = json.loads(response.get('response', '{}'))
            return result.get('content_fr', content)
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return content
    
    def _validate_enrichment_result(self, result: Dict[str, Any], settings: Any) -> bool:
        """Validate enrichment result quality."""
        quality_settings = get_quality_control_settings()
        
        if not quality_settings.enable_response_validation:
            return True
        
        # Check required fields
        if quality_settings.validate_sentiment_values:
            sentiment = result.get('sentiment')
            if sentiment not in ['positive', 'negative', 'neutral']:
                return False
        
        # Check confidence score
        if quality_settings.validate_confidence_scores:
            confidence = result.get('confidence', 0)
            if not 0 <= confidence <= 1:
                return False
        
        return True
    
    def _update_database(self, content_id: int, content_type: ContentType, 
                        enrichment_data: Dict[str, Any], content_fr: str) -> None:
        """Update database with enrichment results."""
        try:
            if content_type == ContentType.ARTICLE:
                self._update_article_enrichment(content_id, enrichment_data, content_fr)
            elif content_type == ContentType.POST:
                self._update_post_enrichment(content_id, enrichment_data, content_fr)
            elif content_type == ContentType.COMMENT:
                self._update_comment_enrichment(content_id, enrichment_data, content_fr)
                
        except Exception as e:
            logger.error(f"Database update failed: {e}")
    
    def _update_article_enrichment(self, article_id: int, data: Dict[str, Any], content_fr: str) -> None:
        """Update article with enrichment data."""
        self.db_manager.client.rpc('update_article_enrichment', {
            'p_article_id': article_id,
            'p_sentiment': data.get('sentiment'),
            'p_sentiment_score': data.get('sentiment_score'),
            'p_keywords': json.dumps(data.get('keywords', [])),
            'p_summary': data.get('summary'),
            'p_category': data.get('category', {}).get('primary_category'),
            'p_confidence': data.get('confidence'),
            'p_content_fr': content_fr
        }).execute()
    
    def _update_post_enrichment(self, post_id: int, data: Dict[str, Any], content_fr: str) -> None:
        """Update social media post with enrichment data."""
        self.db_manager.client.rpc('update_post_enrichment', {
            'p_post_id': post_id,
            'p_sentiment': data.get('sentiment'),
            'p_sentiment_score': data.get('sentiment_score'),
            'p_summary': data.get('summary'),
            'p_confidence': data.get('confidence'),
            'p_content_fr': content_fr
        }).execute()
    
    def _update_comment_enrichment(self, comment_id: int, data: Dict[str, Any], content_fr: str) -> None:
        """Update comment with enrichment data."""
        # Use enhanced comment enrichment if available
        if data.get('keywords_fr') and data.get('entities_fr'):
            self.db_manager.client.rpc('update_comment_enrichment', {
                'p_comment_id': comment_id,
                'p_sentiment': data.get('sentiment'),
                'p_sentiment_score': data.get('sentiment_score'),
                'p_confidence': data.get('confidence'),
                'p_content_fr': content_fr,
                'p_keywords': json.dumps(data.get('keywords', [])),
                'p_entities': json.dumps(data.get('entities', [])),
                'p_keywords_fr': json.dumps(data.get('keywords_fr', [])),
                'p_entities_fr': json.dumps(data.get('entities_fr', []))
            }).execute()
        else:
            # Simple comment enrichment
            self.db_manager.client.table("social_media_comments") \
                .update({
                    'sentiment_score': data.get('sentiment_score'),
                    'relevance': data.get('relevance_score', 0.5)
                }) \
                .eq("id", comment_id) \
                .execute()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and configuration."""
        return {
            'enabled': self.config.enabled,
            'content_types': {
                'articles': {
                    'enabled': self.config.articles.enabled,
                    'batch_size': self.config.articles.batch_size,
                    'processing_mode': self.config.articles.processing_mode.value
                },
                'posts': {
                    'enabled': self.config.posts.enabled,
                    'batch_size': self.config.posts.batch_size,
                    'processing_mode': self.config.posts.processing_mode.value
                },
                'comments': {
                    'enabled': self.config.comments.enabled,
                    'batch_size': self.config.comments.batch_size,
                    'processing_mode': self.config.comments.processing_mode.value
                }
            },
            'model': {
                'provider': self.config.model.provider.value,
                'model_name': self.config.model.model_name,
                'ollama_available': self.ollama_client.health_check()
            },
            'rate_limiting': {
                'requests_per_minute': self.config.rate_limiting.requests_per_minute,
                'current_requests': len(self._request_history)
            }
        }
    
    def reload_configuration(self) -> bool:
        """Reload configuration and prompts from files/environment."""
        try:
            from config.ai_enrichment_config import reload_ai_enrichment_config
            from config.ai_enrichment_prompts import reload_ai_enrichment_prompts
            
            self.config = reload_ai_enrichment_config()
            self.prompts = reload_ai_enrichment_prompts()
            
            logger.info("Configuration and prompts reloaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
