"""
Sentiment Analysis Processor.

This module provides sentiment analysis capabilities for multilingual content
using Ollama LLM with specialized prompts for Tunisian context.
"""

import time
from typing import Dict, Any, Optional, List
import logging

from ..core.base_processor import BaseProcessor, ProcessingResult, ProcessingStatus
from ..core.prompt_templates import PromptTemplates, Language
from ..core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class SentimentAnalyzer(BaseProcessor):
    """
    Sentiment analysis processor for multilingual content.
    
    Analyzes sentiment in Arabic, French, and English text with
    special consideration for Tunisian cultural context.
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the sentiment analyzer.
        
        Args:
            ollama_client: Optional Ollama client instance
            config: Optional configuration dictionary
        """
        super().__init__(ollama_client, config)
        
        # Default configuration
        self.default_config = {
            'temperature': 0.1,  # Low temperature for consistent results
            'max_tokens': 512,   # Sufficient for sentiment analysis
            'confidence_threshold': 0.6,  # Minimum confidence for results
            'language_detection': True,
            'emotion_analysis': True
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}
        
        # Sentiment mapping
        self.sentiment_labels = {
            'positive': 1,
            'negative': -1,
            'neutral': 0
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for sentiment analysis."""
        return PromptTemplates.SYSTEM_PROMPTS['sentiment']
    
    def process(self, content: str, **kwargs) -> ProcessingResult:
        """
        Analyze sentiment of the given content.
        
        Args:
            content: Text content to analyze
            **kwargs: Additional parameters
            
        Returns:
            ProcessingResult with sentiment analysis data
        """
        start_time = time.time()
        
        try:
            # Preprocess content
            processed_content = self.preprocess_content(content)
            if not processed_content:
                return ProcessingResult(
                    status=ProcessingStatus.SKIPPED,
                    error="Empty content after preprocessing"
                )
            
            # Generate prompt
            language = kwargs.get('language', Language.AUTO)
            prompt = PromptTemplates.get_sentiment_prompt(processed_content, language)
            
            # Get LLM response
            response = self.ollama_client.generate_structured(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens']
            )
            
            if not response:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error="No response from LLM"
                )
            
            # Validate and process result
            if not self.validate_result(response):
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error="Invalid response format",
                    metadata={'raw_response': response}
                )
            
            # Postprocess result
            processed_result = self.postprocess_result(response)
            confidence = self.calculate_confidence(processed_result)
            
            # Check confidence threshold
            if confidence < self.config['confidence_threshold']:
                self.logger.warning(f"Low confidence result: {confidence}")
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=processed_result,
                confidence=confidence,
                processing_time=processing_time,
                metadata={
                    'content_length': len(content),
                    'language_detected': processed_result.get('language_detected'),
                    'emotions_detected': len(processed_result.get('emotions', []))
                }
            )
            
        except Exception as e:
            return self.handle_error(e, content)
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate sentiment analysis result.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['sentiment', 'confidence']
        
        # Check required fields
        for field in required_fields:
            if field not in result:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate sentiment value
        valid_sentiments = ['positive', 'negative', 'neutral']
        if result['sentiment'] not in valid_sentiments:
            self.logger.error(f"Invalid sentiment value: {result['sentiment']}")
            return False
        
        # Validate confidence range
        confidence = result.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            self.logger.error(f"Invalid confidence value: {confidence}")
            return False
        
        return True
    
    def postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess sentiment analysis result.
        
        Args:
            result: Raw LLM result
            
        Returns:
            Processed result with additional fields
        """
        processed = result.copy()
        
        # Add sentiment score
        sentiment_label = processed.get('sentiment', 'neutral')
        processed['sentiment_score'] = self.sentiment_labels.get(sentiment_label, 0)
        
        # Normalize emotions list
        emotions = processed.get('emotions', [])
        if isinstance(emotions, str):
            emotions = [emotions]
        processed['emotions'] = emotions
        
        # Ensure language detection
        if 'language_detected' not in processed:
            processed['language_detected'] = 'auto'
        
        # Add processing metadata
        processed['processor'] = 'sentiment_analyzer'
        processed['model'] = self.ollama_client.config.model
        
        return processed
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for sentiment result.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = result.get('confidence', 0.5)
        
        # Adjust confidence based on various factors
        adjustments = 0.0
        
        # Boost confidence if reasoning is provided
        if result.get('reasoning') and len(result['reasoning']) > 10:
            adjustments += 0.1
        
        # Boost confidence if emotions are detected
        emotions = result.get('emotions', [])
        if emotions and len(emotions) > 0:
            adjustments += 0.05
        
        # Boost confidence if language is clearly detected
        if result.get('language_detected') in ['ar', 'fr', 'en']:
            adjustments += 0.05
        
        # Ensure confidence stays within bounds
        final_confidence = min(1.0, max(0.0, base_confidence + adjustments))
        
        return final_confidence
    
    def analyze_batch_sentiments(
        self,
        contents: List[str],
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Analyze sentiments for multiple content items.
        
        Args:
            contents: List of content strings
            **kwargs: Additional parameters
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Starting batch sentiment analysis for {len(contents)} items")
        
        results = self.batch_process(contents, **kwargs)
        
        # Log summary statistics
        stats = self.get_processing_stats(results)
        self.logger.info(f"Batch sentiment analysis completed: {stats}")
        
        return results
    
    def get_sentiment_distribution(
        self,
        results: List[ProcessingResult]
    ) -> Dict[str, Any]:
        """
        Calculate sentiment distribution from results.
        
        Args:
            results: List of processing results
            
        Returns:
            Distribution statistics
        """
        successful_results = [
            r for r in results 
            if r.status == ProcessingStatus.SUCCESS and r.data
        ]
        
        if not successful_results:
            return {}
        
        # Count sentiments
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_confidence = 0.0
        emotions_counter = {}
        
        for result in successful_results:
            sentiment = result.data.get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1
            
            total_confidence += result.confidence or 0.0
            
            # Count emotions
            emotions = result.data.get('emotions', [])
            for emotion in emotions:
                emotions_counter[emotion] = emotions_counter.get(emotion, 0) + 1
        
        total = len(successful_results)
        
        return {
            'total_analyzed': total,
            'sentiment_distribution': {
                k: {'count': v, 'percentage': (v / total) * 100}
                for k, v in sentiment_counts.items()
            },
            'average_confidence': total_confidence / total if total > 0 else 0.0,
            'top_emotions': sorted(
                emotions_counter.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
