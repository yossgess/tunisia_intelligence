"""
Keyword/Key Phrase Extraction Processor.

This module provides keyword and key phrase extraction capabilities for multilingual content
with focus on important terms and concepts in Tunisian context.
"""

import time
from typing import Dict, Any, Optional, List, Set
import logging
import re
from collections import Counter

from ..core.base_processor import BaseProcessor, ProcessingResult, ProcessingStatus
from ..core.prompt_templates import PromptTemplates, Language
from ..core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class KeywordExtractor(BaseProcessor):
    """
    Keyword and key phrase extraction processor for multilingual content.
    
    Extracts important terms, phrases, and concepts from Arabic, French,
    and English text with special focus on Tunisian terminology.
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the keyword extractor.
        
        Args:
            ollama_client: Optional Ollama client instance
            config: Optional configuration dictionary
        """
        super().__init__(ollama_client, config)
        
        # Default configuration
        self.default_config = {
            'temperature': 0.2,  # Slightly higher for creativity in keyword selection
            'max_tokens': 1024,  # Sufficient for keyword lists
            'confidence_threshold': 0.6,
            'min_keyword_length': 2,
            'max_keywords_per_text': 30,
            'min_importance_score': 0.3,
            'deduplicate_keywords': True,
            'extract_phrases': True,
            'category_classification': True
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}
        
        # Keyword categories
        self.keyword_categories = {
            'politics': ['سياسة', 'politique', 'politics', 'government', 'حكومة', 'gouvernement'],
            'economy': ['اقتصاد', 'économie', 'economy', 'economic', 'اقتصادي', 'économique'],
            'society': ['مجتمع', 'société', 'society', 'social', 'اجتماعي', 'social'],
            'culture': ['ثقافة', 'culture', 'cultural', 'ثقافي', 'culturel'],
            'sports': ['رياضة', 'sport', 'sports', 'رياضي', 'sportif'],
            'education': ['تعليم', 'éducation', 'education', 'تعليمي', 'éducatif'],
            'health': ['صحة', 'santé', 'health', 'صحي', 'sanitaire'],
            'technology': ['تكنولوجيا', 'technologie', 'technology', 'تقني', 'technique'],
            'environment': ['بيئة', 'environnement', 'environment', 'بيئي', 'environnemental'],
            'security': ['أمن', 'sécurité', 'security', 'أمني', 'sécuritaire']
        }
        
        # Common stop words to filter out
        self.stop_words = {
            'ar': ['في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك', 'التي', 'الذي', 'كان', 'كانت'],
            'fr': ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or'],
            'en': ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from']
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for keyword extraction."""
        return PromptTemplates.SYSTEM_PROMPTS['keywords']
    
    def process(self, content: str, **kwargs) -> ProcessingResult:
        """
        Extract keywords and key phrases from the given content.
        
        Args:
            content: Text content to analyze
            **kwargs: Additional parameters
            
        Returns:
            ProcessingResult with extracted keywords
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
            prompt = PromptTemplates.get_keywords_prompt(processed_content, language)
            
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
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=processed_result,
                confidence=confidence,
                processing_time=processing_time,
                metadata={
                    'content_length': len(content),
                    'keywords_extracted': len(processed_result.get('keywords', [])),
                    'language_detected': processed_result.get('language_detected'),
                    'main_topics': len(processed_result.get('main_topics', []))
                }
            )
            
        except Exception as e:
            return self.handle_error(e, content)
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate keyword extraction result.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check if keywords field exists
        if 'keywords' not in result:
            self.logger.error("Missing 'keywords' field in result")
            return False
        
        keywords = result['keywords']
        if not isinstance(keywords, list):
            self.logger.error("'keywords' field must be a list")
            return False
        
        # Validate each keyword
        for i, keyword in enumerate(keywords):
            if not isinstance(keyword, dict):
                self.logger.error(f"Keyword {i} must be a dictionary")
                return False
            
            # Check required fields
            required_fields = ['text', 'importance']
            for field in required_fields:
                if field not in keyword:
                    self.logger.error(f"Keyword {i} missing required field: {field}")
                    return False
            
            # Validate importance score
            importance = keyword.get('importance', 0)
            if not isinstance(importance, (int, float)) or not 0 <= importance <= 1:
                self.logger.error(f"Invalid importance value: {importance}")
                return False
            
            # Validate keyword text length
            keyword_text = keyword.get('text', '')
            if len(keyword_text) < self.config['min_keyword_length']:
                self.logger.warning(f"Keyword text too short: '{keyword_text}'")
        
        return True
    
    def postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess keyword extraction result.
        
        Args:
            result: Raw LLM result
            
        Returns:
            Processed result with cleaned keywords
        """
        processed = result.copy()
        keywords = processed.get('keywords', [])
        
        # Clean and validate keywords
        cleaned_keywords = []
        seen_keywords = set() if self.config['deduplicate_keywords'] else None
        
        for keyword in keywords:
            # Clean keyword text
            keyword_text = keyword.get('text', '').strip()
            if not keyword_text or len(keyword_text) < self.config['min_keyword_length']:
                continue
            
            # Filter out stop words
            if self._is_stop_word(keyword_text):
                continue
            
            # Check importance threshold
            importance = keyword.get('importance', 0)
            if importance < self.config['min_importance_score']:
                continue
            
            # Deduplicate if enabled
            if seen_keywords is not None:
                keyword_key = keyword_text.lower()
                if keyword_key in seen_keywords:
                    continue
                seen_keywords.add(keyword_key)
            
            # Enhance keyword with additional fields
            enhanced_keyword = {
                'text': keyword_text,
                'type': keyword.get('type', 'single_word'),
                'importance': importance,
                'frequency': keyword.get('frequency', 1),
                'category': self._categorize_keyword(keyword_text),
                'is_phrase': len(keyword_text.split()) > 1,
                'language': self._detect_keyword_language(keyword_text)
            }
            
            cleaned_keywords.append(enhanced_keyword)
            
            # Limit number of keywords
            if len(cleaned_keywords) >= self.config['max_keywords_per_text']:
                break
        
        # Sort keywords by importance
        cleaned_keywords.sort(key=lambda x: x['importance'], reverse=True)
        
        processed['keywords'] = cleaned_keywords
        
        # Add processing metadata
        processed['processor'] = 'keyword_extractor'
        processed['model'] = self.ollama_client.config.model
        processed['total_keywords'] = len(cleaned_keywords)
        
        # Group keywords by category
        keywords_by_category = {}
        for keyword in cleaned_keywords:
            category = keyword['category']
            if category not in keywords_by_category:
                keywords_by_category[category] = []
            keywords_by_category[category].append(keyword)
        
        processed['keywords_by_category'] = keywords_by_category
        
        # Extract top keywords
        processed['top_keywords'] = cleaned_keywords[:10]
        
        # Ensure main_topics exists
        if 'main_topics' not in processed:
            processed['main_topics'] = self._extract_main_topics(cleaned_keywords)
        
        return processed
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for keyword extraction result.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        keywords = result.get('keywords', [])
        if not keywords:
            return 0.0
        
        # Calculate average importance of all keywords
        total_importance = sum(keyword.get('importance', 0.5) for keyword in keywords)
        avg_importance = total_importance / len(keywords)
        
        # Adjust based on various factors
        adjustments = 0.0
        
        # Boost confidence for diverse keyword types
        keyword_types = set(keyword.get('type', 'single_word') for keyword in keywords)
        if len(keyword_types) > 1:
            adjustments += 0.1
        
        # Boost confidence for categorized keywords
        categorized_keywords = sum(1 for keyword in keywords if keyword.get('category') != 'other')
        if categorized_keywords > 0:
            adjustments += 0.1 * (categorized_keywords / len(keywords))
        
        # Boost confidence for phrases
        phrases = sum(1 for keyword in keywords if keyword.get('is_phrase', False))
        if phrases > 0:
            adjustments += 0.05 * (phrases / len(keywords))
        
        # Penalize if too few keywords (might be under-extraction)
        if len(keywords) < 3:
            adjustments -= 0.2
        
        final_confidence = min(1.0, max(0.0, avg_importance + adjustments))
        return final_confidence
    
    def _is_stop_word(self, text: str) -> bool:
        """
        Check if text is a stop word.
        
        Args:
            text: Text to check
            
        Returns:
            True if stop word
        """
        text_lower = text.lower().strip()
        
        # Check against all stop word lists
        for lang_stop_words in self.stop_words.values():
            if text_lower in lang_stop_words:
                return True
        
        # Additional checks for very short or common words
        if len(text_lower) <= 1:
            return True
        
        # Common punctuation or numbers only
        if re.match(r'^[0-9\W]+$', text_lower):
            return True
        
        return False
    
    def _categorize_keyword(self, keyword_text: str) -> str:
        """
        Categorize a keyword based on its content.
        
        Args:
            keyword_text: Keyword text
            
        Returns:
            Category name
        """
        keyword_lower = keyword_text.lower()
        
        # Check against category keywords
        for category, category_keywords in self.keyword_categories.items():
            for cat_keyword in category_keywords:
                if cat_keyword in keyword_lower or keyword_lower in cat_keyword:
                    return category
        
        # Default category
        return 'other'
    
    def _detect_keyword_language(self, keyword_text: str) -> str:
        """
        Detect the language of a keyword.
        
        Args:
            keyword_text: Keyword text
            
        Returns:
            Language code (ar, fr, en, mixed)
        """
        # Simple heuristic-based language detection
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', keyword_text))
        latin_chars = len(re.findall(r'[a-zA-Z]', keyword_text))
        
        if arabic_chars > 0 and latin_chars > 0:
            return 'mixed'
        elif arabic_chars > 0:
            return 'ar'
        elif latin_chars > 0:
            # Distinguish between French and English (basic heuristic)
            french_indicators = ['é', 'è', 'à', 'ç', 'ù', 'ô', 'î', 'â', 'ê', 'û']
            if any(char in keyword_text for char in french_indicators):
                return 'fr'
            return 'en'
        
        return 'unknown'
    
    def _extract_main_topics(self, keywords: List[Dict[str, Any]]) -> List[str]:
        """
        Extract main topics from keywords.
        
        Args:
            keywords: List of keyword dictionaries
            
        Returns:
            List of main topics
        """
        # Group by category and get top categories
        category_scores = {}
        for keyword in keywords:
            category = keyword.get('category', 'other')
            importance = keyword.get('importance', 0)
            category_scores[category] = category_scores.get(category, 0) + importance
        
        # Sort categories by total importance
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top 5 categories as main topics
        return [category for category, score in sorted_categories[:5] if score > 0]
    
    def extract_keywords_batch(
        self,
        contents: List[str],
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Extract keywords from multiple content items.
        
        Args:
            contents: List of content strings
            **kwargs: Additional parameters
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Starting batch keyword extraction for {len(contents)} items")
        
        results = self.batch_process(contents, **kwargs)
        
        # Log summary statistics
        stats = self.get_processing_stats(results)
        self.logger.info(f"Batch keyword extraction completed: {stats}")
        
        return results
    
    def get_keyword_statistics(
        self,
        results: List[ProcessingResult]
    ) -> Dict[str, Any]:
        """
        Calculate keyword extraction statistics from results.
        
        Args:
            results: List of processing results
            
        Returns:
            Statistics dictionary
        """
        successful_results = [
            r for r in results 
            if r.status == ProcessingStatus.SUCCESS and r.data
        ]
        
        if not successful_results:
            return {}
        
        # Collect all keywords
        all_keywords = []
        category_counts = Counter()
        language_counts = Counter()
        
        for result in successful_results:
            keywords = result.data.get('keywords', [])
            all_keywords.extend(keywords)
            
            for keyword in keywords:
                category = keyword.get('category', 'other')
                language = keyword.get('language', 'unknown')
                category_counts[category] += 1
                language_counts[language] += 1
        
        # Find most common keywords
        keyword_frequency = Counter()
        for keyword in all_keywords:
            keyword_text = keyword.get('text', '')
            keyword_frequency[keyword_text] += 1
        
        most_common_keywords = keyword_frequency.most_common(20)
        
        # Calculate average importance
        total_importance = sum(keyword.get('importance', 0) for keyword in all_keywords)
        avg_importance = total_importance / len(all_keywords) if all_keywords else 0
        
        return {
            'total_keywords_extracted': len(all_keywords),
            'unique_keywords': len(keyword_frequency),
            'average_keywords_per_text': len(all_keywords) / len(successful_results) if successful_results else 0,
            'average_importance': avg_importance,
            'category_distribution': dict(category_counts),
            'language_distribution': dict(language_counts),
            'most_common_keywords': most_common_keywords,
            'phrases_extracted': sum(1 for kw in all_keywords if kw.get('is_phrase', False))
        }
