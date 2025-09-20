"""
Category Classification Processor.

This module provides content categorization capabilities for multilingual content
with focus on Tunisian news and social media content classification.
"""

import time
from typing import Dict, Any, Optional, List
import logging

from ..core.base_processor import BaseProcessor, ProcessingResult, ProcessingStatus
from ..core.prompt_templates import PromptTemplates, Language
from ..core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class CategoryClassifier(BaseProcessor):
    """
    Content category classification processor for multilingual content.
    
    Classifies content into predefined categories with support for
    hierarchical categorization and confidence scoring.
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the category classifier.
        
        Args:
            ollama_client: Optional Ollama client instance
            config: Optional configuration dictionary
        """
        super().__init__(ollama_client, config)
        
        # Default configuration
        self.default_config = {
            'temperature': 0.1,  # Low temperature for consistent classification
            'max_tokens': 512,   # Sufficient for category classification
            'confidence_threshold': 0.7,
            'max_secondary_categories': 3,
            'enable_hierarchical': True,
            'require_reasoning': True
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}
        
        # Predefined categories with multilingual support
        self.categories = {
            'politics': {
                'ar': 'سياسة',
                'fr': 'Politique',
                'en': 'Politics',
                'keywords': ['حكومة', 'برلمان', 'رئيس', 'وزير', 'gouvernement', 'parlement', 'président', 'ministre', 'government', 'parliament', 'president', 'minister'],
                'subcategories': ['domestic_politics', 'international_relations', 'elections', 'legislation']
            },
            'economy': {
                'ar': 'اقتصاد',
                'fr': 'Économie',
                'en': 'Economy',
                'keywords': ['اقتصاد', 'مالية', 'استثمار', 'تجارة', 'économie', 'finance', 'investissement', 'commerce', 'economy', 'finance', 'investment', 'trade'],
                'subcategories': ['finance', 'trade', 'investment', 'employment', 'inflation']
            },
            'society': {
                'ar': 'مجتمع',
                'fr': 'Société',
                'en': 'Society',
                'keywords': ['مجتمع', 'اجتماعي', 'أسرة', 'شباب', 'société', 'social', 'famille', 'jeunesse', 'society', 'social', 'family', 'youth'],
                'subcategories': ['social_issues', 'demographics', 'civil_society', 'human_rights']
            },
            'culture': {
                'ar': 'ثقافة',
                'fr': 'Culture',
                'en': 'Culture',
                'keywords': ['ثقافة', 'فن', 'تراث', 'أدب', 'culture', 'art', 'patrimoine', 'littérature', 'culture', 'art', 'heritage', 'literature'],
                'subcategories': ['arts', 'heritage', 'literature', 'entertainment', 'festivals']
            },
            'sports': {
                'ar': 'رياضة',
                'fr': 'Sport',
                'en': 'Sports',
                'keywords': ['رياضة', 'كرة', 'بطولة', 'لاعب', 'sport', 'football', 'championnat', 'joueur', 'sports', 'football', 'championship', 'player'],
                'subcategories': ['football', 'olympics', 'local_sports', 'international_sports']
            },
            'education': {
                'ar': 'تعليم',
                'fr': 'Éducation',
                'en': 'Education',
                'keywords': ['تعليم', 'مدرسة', 'جامعة', 'طالب', 'éducation', 'école', 'université', 'étudiant', 'education', 'school', 'university', 'student'],
                'subcategories': ['primary_education', 'higher_education', 'vocational_training', 'research']
            },
            'health': {
                'ar': 'صحة',
                'fr': 'Santé',
                'en': 'Health',
                'keywords': ['صحة', 'طب', 'مستشفى', 'دواء', 'santé', 'médecine', 'hôpital', 'médicament', 'health', 'medicine', 'hospital', 'medication'],
                'subcategories': ['public_health', 'healthcare_system', 'medical_research', 'epidemics']
            },
            'technology': {
                'ar': 'تكنولوجيا',
                'fr': 'Technologie',
                'en': 'Technology',
                'keywords': ['تكنولوجيا', 'رقمي', 'إنترنت', 'ذكي', 'technologie', 'numérique', 'internet', 'intelligent', 'technology', 'digital', 'internet', 'smart'],
                'subcategories': ['digital_transformation', 'innovation', 'telecommunications', 'artificial_intelligence']
            },
            'environment': {
                'ar': 'بيئة',
                'fr': 'Environnement',
                'en': 'Environment',
                'keywords': ['بيئة', 'مناخ', 'تلوث', 'طبيعة', 'environnement', 'climat', 'pollution', 'nature', 'environment', 'climate', 'pollution', 'nature'],
                'subcategories': ['climate_change', 'pollution', 'conservation', 'renewable_energy']
            },
            'security': {
                'ar': 'أمن',
                'fr': 'Sécurité',
                'en': 'Security',
                'keywords': ['أمن', 'شرطة', 'جيش', 'إرهاب', 'sécurité', 'police', 'armée', 'terrorisme', 'security', 'police', 'army', 'terrorism'],
                'subcategories': ['national_security', 'public_safety', 'cybersecurity', 'counter_terrorism']
            },
            'international': {
                'ar': 'دولي',
                'fr': 'International',
                'en': 'International',
                'keywords': ['دولي', 'عالمي', 'خارجي', 'سفارة', 'international', 'mondial', 'extérieur', 'ambassade', 'international', 'global', 'foreign', 'embassy'],
                'subcategories': ['diplomacy', 'international_trade', 'global_affairs', 'migration']
            },
            'regional': {
                'ar': 'جهوي',
                'fr': 'Régional',
                'en': 'Regional',
                'keywords': ['جهوي', 'محلي', 'ولاية', 'بلدية', 'régional', 'local', 'gouvernorat', 'municipalité', 'regional', 'local', 'governorate', 'municipality'],
                'subcategories': ['local_government', 'regional_development', 'municipal_affairs', 'rural_development']
            }
        }
        
        # Category hierarchy
        self.category_hierarchy = {
            'politics': ['domestic_politics', 'international_relations', 'elections', 'legislation'],
            'economy': ['finance', 'trade', 'investment', 'employment'],
            'society': ['social_issues', 'demographics', 'civil_society'],
            'culture': ['arts', 'heritage', 'literature', 'entertainment'],
            'sports': ['football', 'olympics', 'local_sports'],
            'education': ['primary_education', 'higher_education', 'research'],
            'health': ['public_health', 'healthcare_system', 'medical_research'],
            'technology': ['digital_transformation', 'innovation', 'telecommunications'],
            'environment': ['climate_change', 'pollution', 'conservation'],
            'security': ['national_security', 'public_safety', 'cybersecurity'],
            'international': ['diplomacy', 'international_trade', 'global_affairs'],
            'regional': ['local_government', 'regional_development', 'municipal_affairs']
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for category classification."""
        return PromptTemplates.SYSTEM_PROMPTS['categories']
    
    def process(self, content: str, **kwargs) -> ProcessingResult:
        """
        Classify the content into appropriate categories.
        
        Args:
            content: Text content to classify
            **kwargs: Additional parameters
            
        Returns:
            ProcessingResult with classification data
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
            prompt = PromptTemplates.get_categories_prompt(processed_content, language)
            
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
                    'primary_category': processed_result.get('primary_category'),
                    'secondary_categories_count': len(processed_result.get('secondary_categories', [])),
                    'language_detected': processed_result.get('language_detected')
                }
            )
            
        except Exception as e:
            return self.handle_error(e, content)
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate category classification result.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['primary_category', 'confidence']
        for field in required_fields:
            if field not in result:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate primary category
        primary_category = result.get('primary_category', '').lower()
        valid_categories = list(self.categories.keys()) + ['other']
        
        if primary_category not in valid_categories:
            self.logger.error(f"Invalid primary category: {primary_category}")
            return False
        
        # Validate confidence
        confidence = result.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            self.logger.error(f"Invalid confidence value: {confidence}")
            return False
        
        # Validate secondary categories if present
        secondary_categories = result.get('secondary_categories', [])
        if secondary_categories:
            if not isinstance(secondary_categories, list):
                self.logger.error("Secondary categories must be a list")
                return False
            
            for category in secondary_categories:
                if category.lower() not in valid_categories:
                    self.logger.warning(f"Invalid secondary category: {category}")
        
        return True
    
    def postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess category classification result.
        
        Args:
            result: Raw LLM result
            
        Returns:
            Processed result with enhanced categorization
        """
        processed = result.copy()
        
        # Normalize category names
        primary_category = processed.get('primary_category', '').lower().strip()
        processed['primary_category'] = primary_category
        
        # Process secondary categories
        secondary_categories = processed.get('secondary_categories', [])
        if isinstance(secondary_categories, str):
            secondary_categories = [secondary_categories]
        
        # Normalize and limit secondary categories
        normalized_secondary = []
        for category in secondary_categories:
            normalized_cat = category.lower().strip()
            if (normalized_cat != primary_category and 
                normalized_cat in self.categories and 
                len(normalized_secondary) < self.config['max_secondary_categories']):
                normalized_secondary.append(normalized_cat)
        
        processed['secondary_categories'] = normalized_secondary
        
        # Add hierarchical information if enabled
        if self.config['enable_hierarchical']:
            processed['subcategories'] = self._get_subcategories(primary_category)
            processed['category_path'] = self._get_category_path(primary_category)
        
        # Add category metadata
        processed['category_info'] = self._get_category_info(primary_category)
        
        # Ensure reasoning exists if required
        if self.config['require_reasoning'] and not processed.get('reasoning'):
            processed['reasoning'] = f"Classified as {primary_category} based on content analysis"
        
        # Add processing metadata
        processed['processor'] = 'category_classifier'
        processed['model'] = self.ollama_client.config.model
        processed['total_categories'] = 1 + len(normalized_secondary)
        
        return processed
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for category classification result.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = result.get('confidence', 0.5)
        
        # Adjust confidence based on various factors
        adjustments = 0.0
        
        # Boost confidence if reasoning is provided
        reasoning = result.get('reasoning', '')
        if reasoning and len(reasoning) > 20:
            adjustments += 0.1
        
        # Boost confidence for known categories
        primary_category = result.get('primary_category', '')
        if primary_category in self.categories:
            adjustments += 0.1
        
        # Boost confidence if secondary categories are relevant
        secondary_categories = result.get('secondary_categories', [])
        relevant_secondary = [cat for cat in secondary_categories if cat in self.categories]
        if relevant_secondary:
            adjustments += 0.05 * len(relevant_secondary)
        
        # Boost confidence if category keywords match content
        category_info = result.get('category_info', {})
        if category_info.get('keyword_matches', 0) > 0:
            adjustments += 0.1
        
        # Penalize if confidence is very low
        if base_confidence < 0.3:
            adjustments -= 0.1
        
        final_confidence = min(1.0, max(0.0, base_confidence + adjustments))
        return final_confidence
    
    def _get_subcategories(self, category: str) -> List[str]:
        """
        Get subcategories for a given category.
        
        Args:
            category: Main category
            
        Returns:
            List of subcategories
        """
        return self.category_hierarchy.get(category, [])
    
    def _get_category_path(self, category: str) -> str:
        """
        Get hierarchical path for a category.
        
        Args:
            category: Category name
            
        Returns:
            Category path string
        """
        if category in self.categories:
            return f"root > {category}"
        return f"root > other > {category}"
    
    def _get_category_info(self, category: str) -> Dict[str, Any]:
        """
        Get detailed information about a category.
        
        Args:
            category: Category name
            
        Returns:
            Category information dictionary
        """
        if category not in self.categories:
            return {'exists': False, 'keyword_matches': 0}
        
        cat_info = self.categories[category]
        return {
            'exists': True,
            'multilingual_names': {
                'ar': cat_info.get('ar', ''),
                'fr': cat_info.get('fr', ''),
                'en': cat_info.get('en', '')
            },
            'keywords': cat_info.get('keywords', []),
            'subcategories': cat_info.get('subcategories', []),
            'keyword_matches': 0  # This would be calculated based on content analysis
        }
    
    def classify_batch(
        self,
        contents: List[str],
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Classify multiple content items.
        
        Args:
            contents: List of content strings
            **kwargs: Additional parameters
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Starting batch classification for {len(contents)} items")
        
        results = self.batch_process(contents, **kwargs)
        
        # Log summary statistics
        stats = self.get_processing_stats(results)
        self.logger.info(f"Batch classification completed: {stats}")
        
        return results
    
    def get_classification_statistics(
        self,
        results: List[ProcessingResult]
    ) -> Dict[str, Any]:
        """
        Calculate classification statistics from results.
        
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
        
        # Count categories
        primary_category_counts = {}
        secondary_category_counts = {}
        total_confidence = 0.0
        
        for result in successful_results:
            # Primary categories
            primary_cat = result.data.get('primary_category', 'unknown')
            primary_category_counts[primary_cat] = primary_category_counts.get(primary_cat, 0) + 1
            
            # Secondary categories
            secondary_cats = result.data.get('secondary_categories', [])
            for cat in secondary_cats:
                secondary_category_counts[cat] = secondary_category_counts.get(cat, 0) + 1
            
            # Confidence
            total_confidence += result.confidence or 0.0
        
        total = len(successful_results)
        
        # Sort categories by frequency
        sorted_primary = sorted(
            primary_category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        sorted_secondary = sorted(
            secondary_category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'total_classified': total,
            'average_confidence': total_confidence / total if total > 0 else 0.0,
            'primary_category_distribution': dict(primary_category_counts),
            'secondary_category_distribution': dict(secondary_category_counts),
            'most_common_primary': sorted_primary[:10],
            'most_common_secondary': sorted_secondary[:10],
            'unique_primary_categories': len(primary_category_counts),
            'unique_secondary_categories': len(secondary_category_counts),
            'items_with_secondary_categories': sum(
                1 for r in successful_results 
                if r.data.get('secondary_categories')
            )
        }
    
    def suggest_new_categories(
        self,
        results: List[ProcessingResult],
        min_frequency: int = 3
    ) -> List[str]:
        """
        Suggest new categories based on classification results.
        
        Args:
            results: List of processing results
            min_frequency: Minimum frequency for suggestion
            
        Returns:
            List of suggested new categories
        """
        # This would analyze misclassified or low-confidence results
        # to suggest new categories that might be needed
        
        low_confidence_results = [
            r for r in results 
            if (r.status == ProcessingStatus.SUCCESS and 
                r.confidence and r.confidence < 0.5)
        ]
        
        # Extract reasoning from low confidence results
        suggestions = []
        reasoning_terms = []
        
        for result in low_confidence_results:
            reasoning = result.data.get('reasoning', '') if result.data else ''
            if reasoning:
                # Simple extraction of potential category terms
                words = reasoning.lower().split()
                reasoning_terms.extend(words)
        
        # Count term frequency and suggest categories
        from collections import Counter
        term_counts = Counter(reasoning_terms)
        
        for term, count in term_counts.most_common(10):
            if count >= min_frequency and len(term) > 3:
                suggestions.append(term)
        
        return suggestions[:5]  # Return top 5 suggestions
