#!/usr/bin/env python3
"""
Simplified Enhanced AI Enrichment Pipeline Runner.

This script provides direct access to run the enhanced AI enrichment pipelines
without complex import dependencies.
"""

import sys
import os
import logging
import time
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from config.database import DatabaseManager
from ai_enrichment.core.ollama_client import OllamaClient, OllamaConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EnrichmentStats:
    """Statistics for enrichment operations."""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    processing_time_ms: int = 0
    average_confidence: float = 0.0

class SimpleEnhancedEnrichmentService:
    """Simplified enhanced enrichment service."""
    
    def __init__(self):
        """Initialize the service."""
        self.db_manager = DatabaseManager()
        self.ollama_client = OllamaClient(OllamaConfig())
        logger.info("Enhanced enrichment service initialized")
    
    def enrich_comments(self, limit: Optional[int] = None, force_reprocess: bool = False) -> EnrichmentStats:
        """Run the enhanced comment enrichment pipeline."""
        logger.info(f"Starting enhanced comment enrichment pipeline (limit={limit})")
        
        try:
            stats = EnrichmentStats()
            start_time = time.time()
            
            # Get comments to process
            comments = self._get_comments_for_enrichment(limit=limit, force_reprocess=force_reprocess)
            
            stats.total_items = len(comments)
            logger.info(f"Found {stats.total_items} comments to enrich")
            
            if stats.total_items == 0:
                logger.info("No comments found for enrichment")
                return stats
            
            # Process each comment
            for i, comment in enumerate(comments):
                try:
                    result = self._enrich_single_comment(comment)
                    if result['success']:
                        stats.successful_items += 1
                        stats.average_confidence += result.get('confidence', 0.0)
                    else:
                        stats.failed_items += 1
                    
                    stats.processed_items += 1
                    
                    # Progress update
                    if stats.processed_items % 10 == 0:
                        logger.info(f"Progress: {stats.processed_items}/{stats.total_items} comments processed")
                        
                except Exception as e:
                    logger.error(f"Failed to enrich comment {comment.get('id')}: {e}")
                    stats.failed_items += 1
                    stats.processed_items += 1
            
            # Calculate final statistics
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            if stats.successful_items > 0:
                stats.average_confidence /= stats.successful_items
            
            # Populate cross-reference tables
            if stats.successful_items > 0:
                logger.info("Populating comment keywords and entities...")
                try:
                    keyword_result = self.db_manager.client.rpc('populate_comment_keywords').execute()
                    entity_result = self.db_manager.client.rpc('populate_comment_entities').execute()
                    
                    keyword_count = keyword_result.data if keyword_result.data else 0
                    entity_count = entity_result.data if entity_result.data else 0
                    
                    logger.info(f"Populated {keyword_count} keywords and {entity_count} entities")
                except Exception as e:
                    logger.warning(f"Failed to populate cross-reference tables: {e}")
            
            logger.info(f"Comment enrichment completed: {stats.successful_items}/{stats.total_items} successful")
            return stats
            
        except Exception as e:
            logger.error(f"Comment enrichment pipeline failed: {e}")
            raise
    
    def _get_comments_for_enrichment(self, limit=None, force_reprocess=False):
        """Get comments that need enrichment."""
        try:
            query = self.db_manager.client.table("social_media_comments").select("*")
            
            if not force_reprocess:
                query = query.is_("enriched_at", "null")
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get comments for enrichment: {e}")
            return []
    
    def _enrich_single_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single comment with enhanced AI analysis."""
        start_time = time.time()
        
        try:
            content = comment.get('content', '')
            content_length = len(content)
            
            if not content.strip():
                return {'success': False, 'error': 'Empty content'}
            
            # Detect language
            language_detected = self._detect_language(content)
            
            # Translate if needed
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform enhanced comment enrichment
            enrichment_result = self._perform_enhanced_comment_enrichment(content_fr, language_detected)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Update comment in database using the new enhanced function
            # Now using English sentiment values after fixing the constraint
            success = self.db_manager.client.rpc('update_comment_enrichment', {
                'p_comment_id': comment['id'],
                'p_sentiment': enrichment_result['sentiment'],  # English values: positive/negative/neutral
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_keywords': json.dumps(enrichment_result['keywords']),
                'p_entities': json.dumps(enrichment_result['entities']),
                'p_content_fr': content_fr,
                'p_keywords_fr': json.dumps(enrichment_result['keywords_fr']),
                'p_entities_fr': json.dumps(enrichment_result['entities_fr']),
                'p_language_detected': language_detected,
                'p_confidence': enrichment_result['confidence'],
                'p_processing_time_ms': processing_time_ms,
                'p_content_length': content_length,
                'p_ai_model_version': 'qwen2.5:7b'
            }).execute()
            
            return {
                'success': True,
                'confidence': enrichment_result['confidence'],
                'processing_time_ms': processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich comment {comment['id']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of content."""
        # Simple heuristic - check for Arabic characters
        arabic_chars = sum(1 for char in content if '\u0600' <= char <= '\u06FF')
        if arabic_chars > len(content) * 0.3:
            return 'ar'
        return 'fr'
    
    def _translate_to_french(self, content: str) -> str:
        """Translate Arabic content to French using Ollama."""
        try:
            prompt = f"""Translate the following Arabic text to French. Return only the French translation, no explanations:

{content}"""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            # Handle both dict and string responses
            if isinstance(response, dict):
                return response.get('response', content)
            elif isinstance(response, str):
                return response
            else:
                return content
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return content
    
    def _perform_enhanced_comment_enrichment(self, content: str, language: str) -> Dict[str, Any]:
        """Perform enhanced AI enrichment specifically for comments."""
        try:
            prompt = f"""Analyze the following French comment and provide enhanced AI enrichment in JSON format.

Comment: {content}

Requirements:
1. Sentiment analysis (positive/negative/neutral)
2. Extract top 5 keywords with importance scores
3. Identify named entities (persons, organizations, locations)
4. Provide French translation of keywords and entities
5. Focus on Tunisian context

Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.72,
  "keywords": [
    {{"text": "keyword", "importance": 0.85, "category": "opinion", "normalized_form": "normalized"}}
  ],
  "entities": [
    {{"text": "entity", "type": "LOCATION", "canonical_name": "Tunisia", "confidence": 0.95, "is_tunisian": true}}
  ],
  "keywords_fr": [
    {{"text": "french_keyword", "importance": 0.85, "original_text": "keyword"}}
  ],
  "entities_fr": [
    {{"text": "french_entity", "canonical_name": "Tunisia", "original_text": "entity"}}
  ],
  "confidence": 0.85
}}"""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            # Handle both dict and string responses
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get('response', '{}')
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = '{}'
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response, using defaults")
                result = {}
            
            # Validate and set defaults with French sentiment labels (consistent across database)
            result.setdefault('sentiment', 'neutre')  # Use French labels consistently
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('keywords', [])
            result.setdefault('entities', [])
            result.setdefault('keywords_fr', [])
            result.setdefault('entities_fr', [])
            result.setdefault('confidence', 0.7)
            
            # Convert English sentiment to French format (for database consistency)
            sentiment_mapping = {
                'positive': 'positif',
                'negative': 'négatif', 
                'neutral': 'neutre'
            }
            if result['sentiment'] in sentiment_mapping:
                result['sentiment'] = sentiment_mapping[result['sentiment']]
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced comment enrichment failed: {e}")
            return {
                'sentiment': 'neutre',  # Use French label for consistency
                'sentiment_score': 0.5,
                'keywords': [],
                'entities': [],
                'keywords_fr': [],
                'entities_fr': [],
                'confidence': 0.1
            }

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced Comment Enrichment Pipeline")
    parser.add_argument('--limit', type=int, help='Limit number of comments to process')
    parser.add_argument('--force-reprocess', action='store_true', help='Reprocess already enriched comments')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("ENHANCED COMMENT ENRICHMENT PIPELINE")
        logger.info("Tunisia Intelligence System")
        logger.info("=" * 60)
        
        # Initialize service
        service = SimpleEnhancedEnrichmentService()
        
        # Run comment enrichment
        stats = service.enrich_comments(
            limit=args.limit,
            force_reprocess=args.force_reprocess
        )
        
        # Print results
        logger.info("-" * 50)
        logger.info("ENRICHMENT RESULTS")
        logger.info("-" * 50)
        logger.info(f"Total Comments: {stats.total_items}")
        logger.info(f"Processed: {stats.processed_items}")
        logger.info(f"Successful: {stats.successful_items}")
        logger.info(f"Failed: {stats.failed_items}")
        logger.info(f"Processing Time: {stats.processing_time_ms / 1000:.2f} seconds")
        logger.info(f"Average Confidence: {stats.average_confidence:.3f}")
        
        if stats.total_items > 0:
            success_rate = (stats.successful_items / stats.total_items) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("-" * 50)
        
        # Check analytics
        logger.info("Checking enrichment analytics...")
        try:
            analytics = service.db_manager.client.table("streamlined_enrichment_analytics") \
                .select("*") \
                .eq("content_type", "social_media_comments") \
                .execute()
            
            if analytics.data:
                data = analytics.data[0]
                logger.info(f"Updated Analytics:")
                logger.info(f"  Total Comments: {data['total_items']}")
                logger.info(f"  Enriched: {data['enriched_items']}")
                logger.info(f"  Keywords Extracted: {data['keywords_extracted']}")
                logger.info(f"  Entities Extracted: {data['entities_extracted']}")
                logger.info(f"  Enrichment Percentage: {data['enrichment_percentage']}%")
        except Exception as e:
            logger.warning(f"Failed to get analytics: {e}")
        
        logger.info("Enhanced comment enrichment completed!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
