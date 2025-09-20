#!/usr/bin/env python3
"""
Streamlined French Language Consistency Enricher

This module implements the streamlined logic:
1. Only "content" column is fed to LLM
2. Language detection: French → process directly, Arabic/English → translate first
3. All AI outputs generated in French by default
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class ContentLanguage(str, Enum):
    FRENCH = "fr"
    ARABIC = "ar" 
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class StreamlinedFrenchEnricher:
    """Streamlined enricher with automatic French translation and processing."""
    
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
        
        # French category mapping for validation
        self.french_categories = [
            'Politique', 'Économie', 'Société', 'Culture', 'Sport', 
            'Éducation', 'Santé', 'Technologie', 'Environnement', 
            'Sécurité', 'International', 'Régional', 'Justice', 'Autre'
        ]
    
    def detect_language(self, content: str) -> ContentLanguage:
        """
        Simple language detection based on character patterns.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Detected language
        """
        if not content or len(content.strip()) < 10:
            return ContentLanguage.UNKNOWN
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', content))
        
        # Count Latin characters (French/English)
        latin_chars = len(re.findall(r'[a-zA-ZÀ-ÿ]', content))
        
        total_chars = len(re.findall(r'[a-zA-ZÀ-ÿ\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', content))
        
        if total_chars == 0:
            return ContentLanguage.UNKNOWN
        
        arabic_ratio = arabic_chars / total_chars
        latin_ratio = latin_chars / total_chars
        
        # Decision logic
        if arabic_ratio > 0.7:
            return ContentLanguage.ARABIC
        elif latin_ratio > 0.7:
            # Simple French vs English detection
            french_indicators = ['le ', 'la ', 'les ', 'de ', 'du ', 'des ', 'et ', 'à ', 'dans ', 'pour ', 'avec ', 'sur ']
            english_indicators = ['the ', 'and ', 'of ', 'to ', 'in ', 'for ', 'with ', 'on ', 'at ', 'by ']
            
            content_lower = content.lower()
            french_count = sum(1 for indicator in french_indicators if indicator in content_lower)
            english_count = sum(1 for indicator in english_indicators if indicator in content_lower)
            
            if french_count > english_count:
                return ContentLanguage.FRENCH
            else:
                return ContentLanguage.ENGLISH
        else:
            return ContentLanguage.MIXED
    
    def get_translation_prompt(self, content: str, source_language: ContentLanguage) -> str:
        """Get prompt for translation to French."""
        if source_language == ContentLanguage.ARABIC:
            return f"""
Traduisez le texte arabe suivant en français de manière précise et naturelle :

Texte arabe :
"{content}"

Fournissez uniquement la traduction française, sans commentaires ni explications.
Maintenez le sens, le ton et le contexte du texte original.
Utilisez un français correct et fluide.
"""
        elif source_language == ContentLanguage.ENGLISH:
            return f"""
Traduisez le texte anglais suivant en français de manière précise et naturelle :

Texte anglais :
"{content}"

Fournissez uniquement la traduction française, sans commentaires ni explications.
Maintenez le sens, le ton et le contexte du texte original.
Utilisez un français correct et fluide.
"""
        else:
            return f"""
Traduisez le texte suivant en français de manière précise et naturelle :

Texte :
"{content}"

Fournissez uniquement la traduction française, sans commentaires ni explications.
"""
    
    def get_enrichment_prompt(self, french_content: str, content_type: str) -> str:
        """Get enrichment prompt for French content."""
        if content_type == "article":
            return f"""
Analysez le contenu français suivant et fournissez une analyse complète en français :

Contenu à analyser :
"{french_content}"

Fournissez une réponse JSON avec TOUS les champs requis :

Format de réponse :
{{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": 0.8,
    "confidence": 0.85,
    "summary": "Résumé en français (max 200 mots)...",
    "keywords": ["mot-clé1", "mot-clé2", "politique", "économie"],
    "category": "Politique|Économie|Société|Culture|Sport|Éducation|Santé|Technologie|Environnement|Sécurité|International|Régional|Justice|Autre",
    "entities": [
        {{"text": "Kaïs Saïed", "type": "PERSON", "confidence": 0.95}},
        {{"text": "Tunisie", "type": "LOCATION", "confidence": 0.98}}
    ]
}}

IMPORTANT:
- sentiment_score: nombre entre -1.0 (très négatif) et 1.0 (très positif), 0.0 = neutre
- confidence: votre confiance globale dans l'analyse (0.0 à 1.0)
- keywords: 5-10 mots-clés français les plus importants
- category: choisir UNE catégorie parmi la liste fournie
- entities: personnes, lieux, organisations mentionnés

Contexte : Contenu journalistique tunisien. Toutes les réponses doivent être en français.
"""
        elif content_type == "social_media_post":
            return f"""
Analysez ce post en français et fournissez une analyse en français :

Post à analyser :
"{french_content}"

Fournissez une réponse JSON avec TOUS les champs requis :

Format de réponse :
{{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": 0.6,
    "confidence": 0.80,
    "summary": "Résumé français concis (max 100 mots)...",
    "keywords": ["social", "gouvernement", "citoyens"],
    "category": "Politique|Économie|Société|Culture|Sport|Éducation|Santé|Technologie|Environnement|Sécurité|International|Régional|Justice|Autre",
    "entities": [
        {{"text": "Gouvernement", "type": "ORGANIZATION", "confidence": 0.90}}
    ]
}}

IMPORTANT:
- sentiment_score: nombre entre -1.0 (très négatif) et 1.0 (très positif), 0.0 = neutre
- confidence: votre confiance globale dans l'analyse (0.0 à 1.0)
- keywords: 3-7 mots-clés français les plus pertinents
- category: choisir UNE catégorie parmi la liste fournie
- entities: personnes, lieux, organisations mentionnés

Contexte : Post officiel tunisien. Toutes les réponses en français.
"""
        else:  # comment
            return f"""
Analysez ce commentaire et fournissez UNIQUEMENT l'analyse des métadonnées en français :

Commentaire :
"{french_content}"

Format de réponse JSON avec TOUS les champs requis :
{{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": -0.3,
    "confidence": 0.75,
    "keywords": ["opinion", "réaction", "citoyen"],
    "entities": [
        {{"text": "Président", "type": "PERSON", "confidence": 0.85}}
    ],
    "reasoning": "Explication du sentiment en français"
}}

IMPORTANT:
- sentiment_score: nombre entre -1.0 (très négatif) et 1.0 (très positif), 0.0 = neutre
- confidence: votre confiance dans l'analyse (0.0 à 1.0)
- keywords: 2-5 mots-clés français décrivant le commentaire
- entities: personnes, lieux, organisations mentionnés (si applicable)
- reasoning: courte explication de votre analyse du sentiment

Contexte : Commentaire citoyen tunisien. Analysez seulement les métadonnées en français.
"""
    
    def translate_content(self, content: str, source_language: ContentLanguage) -> Optional[str]:
        """
        Translate content to French if needed.
        
        Args:
            content: Original content
            source_language: Detected language
            
        Returns:
            French translation or None if translation failed
        """
        if source_language == ContentLanguage.FRENCH:
            return content  # Already French, no translation needed
        
        try:
            prompt = self.get_translation_prompt(content, source_language)
            
            response = self.ollama_client.generate_structured(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2048
            )
            
            # Handle both string and dict responses from Ollama
            if response:
                if isinstance(response, dict):
                    response_text = response.get('response', '') or response.get('content', '') or str(response)
                else:
                    response_text = str(response)
                
                if response_text and response_text.strip():
                    return response_text.strip()
            
            logger.warning(f"Empty translation response for {source_language} content")
            return None
                
        except Exception as e:
            logger.error(f"Translation failed for {source_language} content: {e}")
            return None
    
    def enrich_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """
        Main enrichment function following streamlined logic.
        
        Args:
            content: Original content (only this is fed to LLM)
            content_type: Type of content (article, social_media_post, comment)
            
        Returns:
            Enrichment results with French translation if needed
        """
        try:
            # Step 1: Detect language
            detected_language = self.detect_language(content)
            logger.info(f"Detected language: {detected_language}")
            
            # Step 2: Translate to French if needed
            french_content = content
            translation_needed = detected_language != ContentLanguage.FRENCH
            
            if translation_needed:
                logger.info(f"Translating {detected_language} content to French")
                french_content = self.translate_content(content, detected_language)
                
                if not french_content:
                    return self._create_error_result(f"Translation from {detected_language} to French failed")
            
            # Step 3: Process French content for enrichment
            logger.info("Processing French content for enrichment")
            prompt = self.get_enrichment_prompt(french_content, content_type)
            
            response = self.ollama_client.generate_structured(
                prompt=prompt,
                temperature=0.1,
                max_tokens=1024
            )
            
            # Handle both string and dict responses from Ollama
            if response:
                if isinstance(response, dict):
                    response_text = response.get('response', '') or response.get('content', '') or str(response)
                else:
                    response_text = str(response)
            else:
                response_text = None
            
            if not response_text:
                return self._create_error_result("No response from LLM for enrichment")
            
            # Use the processed response text for JSON parsing
            response = response_text
            
            # Step 4: Parse and validate response
            try:
                result = json.loads(response)
                
                # Add translation info to result
                processed_result = {
                    'sentiment': result.get('sentiment', 'neutre'),
                    'sentiment_score': result.get('sentiment_score', 0.0),  # Use LLM's numeric score directly
                    'confidence': result.get('confidence', 0.0),
                    'keywords': result.get('keywords', []),
                    'entities': result.get('entities', []),
                    'detected_language': detected_language.value,
                    'translation_needed': translation_needed,
                    'content_type': content_type
                }
                
                # Add content-specific fields
                if content_type in ['article', 'social_media_post']:
                    processed_result['summary'] = result.get('summary', '')
                    processed_result['category'] = result.get('category', 'Autre')
                    
                    # Add French translation if it was needed
                    if translation_needed:
                        processed_result['content_fr'] = french_content
                
                if content_type == 'comment':
                    processed_result['reasoning'] = result.get('reasoning', '')
                
                return processed_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {e}")
                return self._create_error_result("Invalid JSON response from LLM")
                
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            return self._create_error_result(str(e))
    
    def _convert_sentiment_score(self, sentiment: str) -> float:
        """Convert French sentiment label to numeric score."""
        sentiment_mapping = {
            'positif': 1.0,
            'négatif': -1.0,
            'neutre': 0.0
        }
        return sentiment_mapping.get(sentiment.lower(), 0.0)
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            'sentiment': 'neutre',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'keywords': [],
            'entities': [],
            'error': error_message,
            'status': 'failed'
        }
    
    def prepare_database_update(self, enrichment_result: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """
        Prepare data for database update.
        
        Args:
            enrichment_result: Result from enrich_content()
            content_type: Type of content being processed
            
        Returns:
            Dictionary ready for database update
        """
        base_data = {
            'p_sentiment': enrichment_result['sentiment'],
            'p_sentiment_score': enrichment_result['sentiment_score'],
            'p_confidence': enrichment_result['confidence']
        }
        
        if content_type == 'article':
            base_data.update({
                'p_keywords': json.dumps(enrichment_result['keywords'], ensure_ascii=False),
                'p_summary': enrichment_result.get('summary', ''),
                'p_category': enrichment_result.get('category', 'Autre'),
                'p_content_fr': enrichment_result.get('content_fr')  # Only if translation was needed
            })
        elif content_type == 'social_media_post':
            base_data.update({
                'p_summary': enrichment_result.get('summary', ''),
                'p_content_fr': enrichment_result.get('content_fr')  # Only if translation was needed
            })
        # Comments only get base enrichment data
        
        return base_data

# Integration with existing enrichment service
class StreamlinedEnrichmentService:
    """Enhanced enrichment service with streamlined French consistency."""
    
    def __init__(self, ollama_client, db_manager):
        self.french_enricher = StreamlinedFrenchEnricher(ollama_client)
        self.db_manager = db_manager
    
    def process_article(self, article_data: Dict[str, Any]) -> bool:
        """Process article with streamlined French logic."""
        content = article_data.get('content', '')
        if not content:
            # Fallback to title + description if no content
            content = f"{article_data.get('title', '')} {article_data.get('description', '')}".strip()
        
        if not content:
            logger.warning(f"No content to process for article {article_data.get('id')}")
            return False
        
        # Enrich with streamlined logic
        result = self.french_enricher.enrich_content(content, 'article')
        
        if result.get('status') == 'failed':
            logger.error(f"Failed to enrich article {article_data.get('id')}: {result.get('error')}")
            return False
        
        # Prepare database update
        update_data = self.french_enricher.prepare_database_update(result, 'article')
        update_data['p_article_id'] = article_data['id']
        
        # Update database using the function
        try:
            response = self.db_manager.client.rpc('update_article_enrichment', update_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Database update failed for article {article_data['id']}: {e}")
            return False
    
    def process_post(self, post_data: Dict[str, Any]) -> bool:
        """Process social media post with streamlined French logic."""
        content = post_data.get('content', '')
        
        if not content:
            logger.warning(f"No content to process for post {post_data.get('id')}")
            return False
        
        # Enrich with streamlined logic
        result = self.french_enricher.enrich_content(content, 'social_media_post')
        
        if result.get('status') == 'failed':
            logger.error(f"Failed to enrich post {post_data.get('id')}: {result.get('error')}")
            return False
        
        # Prepare database update
        update_data = self.french_enricher.prepare_database_update(result, 'social_media_post')
        update_data['p_post_id'] = post_data['id']
        
        # Update database
        try:
            response = self.db_manager.client.rpc('update_post_enrichment', update_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Database update failed for post {post_data['id']}: {e}")
            return False
    
    def process_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Process comment with French metadata only."""
        content = comment_data.get('content', '')
        
        if not content:
            logger.warning(f"No content to process for comment {comment_data.get('id')}")
            return False
        
        # Enrich with French metadata only (no translation stored)
        result = self.french_enricher.enrich_content(content, 'comment')
        
        if result.get('status') == 'failed':
            logger.error(f"Failed to enrich comment {comment_data.get('id')}: {result.get('error')}")
            return False
        
        # Prepare database update (no content_fr for comments)
        update_data = self.french_enricher.prepare_database_update(result, 'comment')
        update_data['p_comment_id'] = comment_data['id']
        
        # Update database
        try:
            response = self.db_manager.client.rpc('update_comment_enrichment', update_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Database update failed for comment {comment_data['id']}: {e}")
            return False

if __name__ == "__main__":
    print("🇫🇷 Streamlined French Language Consistency Enricher")
    print("=" * 55)
    print("Logic:")
    print("1. Only 'content' column fed to LLM")
    print("2. Language detection → French: direct, Arabic/English: translate first")
    print("3. All AI outputs generated in French by default")
    print("4. Translation stored only when needed (content_fr)")
