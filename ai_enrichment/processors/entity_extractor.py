"""
Named Entity Recognition (NER) Processor.

This module provides named entity extraction capabilities for multilingual content
with focus on Tunisian entities (persons, organizations, locations).
"""

import time
from typing import Dict, Any, Optional, List, Set
import logging
import re

from ..core.base_processor import BaseProcessor, ProcessingResult, ProcessingStatus
from ..core.prompt_templates import PromptTemplates, Language
from ..core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class EntityExtractor(BaseProcessor):
    """
    Named Entity Recognition processor for multilingual content.
    
    Extracts persons, organizations, and locations from Arabic, French,
    and English text with special focus on Tunisian entities.
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the entity extractor.
        
        Args:
            ollama_client: Optional Ollama client instance
            config: Optional configuration dictionary
        """
        super().__init__(ollama_client, config)
        
        # Default configuration
        self.default_config = {
            'temperature': 0.1,  # Low temperature for consistent extraction
            'max_tokens': 1024,  # More tokens for entity lists
            'confidence_threshold': 0.7,  # Higher threshold for entities
            'min_entity_length': 2,  # Minimum entity name length
            'max_entities_per_text': 50,  # Limit entities per text
            'deduplicate_entities': True,
            'canonical_name_matching': True
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}
        
        # Entity types
        self.entity_types = {
            'PERSON': 'person',
            'ORGANIZATION': 'organization', 
            'LOCATION': 'location'
        }
        
        # Common Tunisian entity patterns for validation
        self.tunisian_patterns = {
            'locations': [
                r'تونس|tunis|tunisia',
                r'صفاقس|sfax',
                r'سوسة|sousse',
                r'قابس|gabes|gabès',
                r'بنزرت|bizerte',
                r'المنستير|monastir',
                r'القيروان|kairouan',
                r'جندوبة|jendouba',
                r'المهدية|mahdia',
                r'تطاوين|tataouine'
            ],
            'organizations': [
                r'الحكومة|gouvernement',
                r'البرلمان|parlement',
                r'الرئاسة|présidence',
                r'وزارة|ministère',
                r'بلدية|municipalité',
                r'جامعة|université'
            ]
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for entity extraction."""
        return PromptTemplates.SYSTEM_PROMPTS['entities']
    
    def process(self, content: str, **kwargs) -> ProcessingResult:
        """
        Extract named entities from the given content.
        
        Args:
            content: Text content to analyze
            **kwargs: Additional parameters
            
        Returns:
            ProcessingResult with extracted entities
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
            prompt = PromptTemplates.get_entities_prompt(processed_content, language)
            
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
                    'entities_extracted': len(processed_result.get('entities', [])),
                    'language_detected': processed_result.get('language_detected')
                }
            )
            
        except Exception as e:
            return self.handle_error(e, content)
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate entity extraction result.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check if entities field exists
        if 'entities' not in result:
            self.logger.error("Missing 'entities' field in result")
            return False
        
        entities = result['entities']
        if not isinstance(entities, list):
            self.logger.error("'entities' field must be a list")
            return False
        
        # Validate each entity
        for i, entity in enumerate(entities):
            if not isinstance(entity, dict):
                self.logger.error(f"Entity {i} must be a dictionary")
                return False
            
            # Check required fields
            required_fields = ['text', 'type', 'confidence']
            for field in required_fields:
                if field not in entity:
                    self.logger.error(f"Entity {i} missing required field: {field}")
                    return False
            
            # Validate entity type
            valid_types = ['PERSON', 'ORGANIZATION', 'LOCATION']
            if entity['type'] not in valid_types:
                self.logger.error(f"Invalid entity type: {entity['type']}")
                return False
            
            # Validate confidence
            confidence = entity.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                self.logger.error(f"Invalid confidence value: {confidence}")
                return False
            
            # Validate entity text length
            entity_text = entity.get('text', '')
            if len(entity_text) < self.config['min_entity_length']:
                self.logger.warning(f"Entity text too short: '{entity_text}'")
        
        return True
    
    def postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess entity extraction result.
        
        Args:
            result: Raw LLM result
            
        Returns:
            Processed result with cleaned entities
        """
        processed = result.copy()
        entities = processed.get('entities', [])
        
        # Clean and validate entities
        cleaned_entities = []
        seen_entities = set() if self.config['deduplicate_entities'] else None
        
        for entity in entities:
            # Clean entity text
            entity_text = entity.get('text', '').strip()
            if not entity_text or len(entity_text) < self.config['min_entity_length']:
                continue
            
            # Deduplicate if enabled
            if seen_entities is not None:
                entity_key = (entity_text.lower(), entity.get('type', ''))
                if entity_key in seen_entities:
                    continue
                seen_entities.add(entity_key)
            
            # Enhance entity with additional fields
            enhanced_entity = {
                'text': entity_text,
                'type': entity.get('type', 'UNKNOWN'),
                'confidence': entity.get('confidence', 0.5),
                'canonical_name': self._get_canonical_name(entity_text, entity.get('type')),
                'context': entity.get('context', ''),
                'is_tunisian': self._is_tunisian_entity(entity_text, entity.get('type'))
            }
            
            cleaned_entities.append(enhanced_entity)
            
            # Limit number of entities
            if len(cleaned_entities) >= self.config['max_entities_per_text']:
                break
        
        processed['entities'] = cleaned_entities
        
        # Add processing metadata
        processed['processor'] = 'entity_extractor'
        processed['model'] = self.ollama_client.config.model
        processed['total_entities'] = len(cleaned_entities)
        
        # Group entities by type
        entities_by_type = {}
        for entity in cleaned_entities:
            entity_type = entity['type']
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        processed['entities_by_type'] = entities_by_type
        
        return processed
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for entity extraction result.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        entities = result.get('entities', [])
        if not entities:
            return 0.0
        
        # Calculate average confidence of all entities
        total_confidence = sum(entity.get('confidence', 0.5) for entity in entities)
        avg_confidence = total_confidence / len(entities)
        
        # Adjust based on various factors
        adjustments = 0.0
        
        # Boost confidence for Tunisian entities
        tunisian_entities = sum(1 for entity in entities if entity.get('is_tunisian', False))
        if tunisian_entities > 0:
            adjustments += 0.1 * (tunisian_entities / len(entities))
        
        # Boost confidence if entities have context
        entities_with_context = sum(1 for entity in entities if entity.get('context'))
        if entities_with_context > 0:
            adjustments += 0.05 * (entities_with_context / len(entities))
        
        # Penalize if too many entities (might be over-extraction)
        if len(entities) > 20:
            adjustments -= 0.1
        
        final_confidence = min(1.0, max(0.0, avg_confidence + adjustments))
        return final_confidence
    
    def _get_canonical_name(self, entity_text: str, entity_type: str) -> str:
        """
        Get canonical name for an entity.
        
        Args:
            entity_text: Original entity text
            entity_type: Entity type
            
        Returns:
            Canonical name
        """
        if not self.config['canonical_name_matching']:
            return entity_text
        
        # Basic canonicalization
        canonical = entity_text.strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['السيد', 'السيدة', 'الدكتور', 'المهندس', 'الأستاذ', 'M.', 'Mme', 'Dr.', 'Prof.']
        for prefix in prefixes_to_remove:
            if canonical.startswith(prefix):
                canonical = canonical[len(prefix):].strip()
        
        # Handle common variations for locations
        if entity_type == 'LOCATION':
            location_mappings = {
                'تونس العاصمة': 'تونس',
                'Tunis Capitale': 'Tunis',
                'Grand Tunis': 'Tunis'
            }
            canonical = location_mappings.get(canonical, canonical)
        
        return canonical
    
    def _is_tunisian_entity(self, entity_text: str, entity_type: str) -> bool:
        """
        Check if an entity is likely Tunisian.
        
        Args:
            entity_text: Entity text
            entity_type: Entity type
            
        Returns:
            True if likely Tunisian entity
        """
        entity_lower = entity_text.lower()
        
        # Check against known patterns
        if entity_type in self.tunisian_patterns:
            patterns = self.tunisian_patterns[entity_type]
            for pattern in patterns:
                if re.search(pattern, entity_lower, re.IGNORECASE):
                    return True
        
        # Additional heuristics
        tunisian_indicators = [
            'تونس', 'tunisia', 'tunisie', 'tunisian', 'tunisien',
            'الجمهورية التونسية', 'république tunisienne'
        ]
        
        for indicator in tunisian_indicators:
            if indicator in entity_lower:
                return True
        
        return False
    
    def extract_entities_batch(
        self,
        contents: List[str],
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Extract entities from multiple content items.
        
        Args:
            contents: List of content strings
            **kwargs: Additional parameters
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Starting batch entity extraction for {len(contents)} items")
        
        results = self.batch_process(contents, **kwargs)
        
        # Log summary statistics
        stats = self.get_processing_stats(results)
        self.logger.info(f"Batch entity extraction completed: {stats}")
        
        return results
    
    def get_entity_statistics(
        self,
        results: List[ProcessingResult]
    ) -> Dict[str, Any]:
        """
        Calculate entity extraction statistics from results.
        
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
        
        # Collect all entities
        all_entities = []
        entity_type_counts = {'PERSON': 0, 'ORGANIZATION': 0, 'LOCATION': 0}
        tunisian_entity_count = 0
        
        for result in successful_results:
            entities = result.data.get('entities', [])
            all_entities.extend(entities)
            
            for entity in entities:
                entity_type = entity.get('type', 'UNKNOWN')
                if entity_type in entity_type_counts:
                    entity_type_counts[entity_type] += 1
                
                if entity.get('is_tunisian', False):
                    tunisian_entity_count += 1
        
        # Find most common entities
        entity_frequency = {}
        for entity in all_entities:
            canonical_name = entity.get('canonical_name', entity.get('text', ''))
            entity_frequency[canonical_name] = entity_frequency.get(canonical_name, 0) + 1
        
        most_common_entities = sorted(
            entity_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            'total_entities_extracted': len(all_entities),
            'unique_entities': len(entity_frequency),
            'entity_type_distribution': entity_type_counts,
            'tunisian_entities': tunisian_entity_count,
            'tunisian_percentage': (tunisian_entity_count / len(all_entities) * 100) if all_entities else 0,
            'most_common_entities': most_common_entities,
            'average_entities_per_text': len(all_entities) / len(successful_results) if successful_results else 0
        }
