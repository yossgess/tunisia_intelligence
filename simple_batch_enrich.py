#!/usr/bin/env python3
"""
Comprehensive Batch Enrichment

Uses the comprehensive enrichment service to store LLM output
in ALL destination tables according to the database schema.
"""

import requests
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simple_batch_enrichment.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class SimpleAIEnricher:
    """Simple AI enricher using direct Ollama calls."""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model = "qwen2.5:7b"
        self.db_manager = None
        
        # Initialize database and comprehensive service
        try:
            from config.database import DatabaseManager
            from comprehensive_enrichment_service import ComprehensiveEnrichmentService
            
            self.db_manager = DatabaseManager()
            
            # Create mock Ollama client for comprehensive service
            class MockOllamaClient:
                def generate_structured(self, prompt, temperature=0.1, max_tokens=1024):
                    # Use the same direct Ollama call as before
                    import requests
                    payload = {
                        "model": "qwen2.5:7b",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                    
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json=payload,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get('response', '').strip()
                    return None
            
            # Initialize comprehensive enrichment service
            ollama_client = MockOllamaClient()
            self.comprehensive_service = ComprehensiveEnrichmentService(ollama_client, self.db_manager)
            
            logger.info("Database manager and comprehensive service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def detect_language(self, content: str) -> Optional[str]:
        """Detect the primary language of the content."""
        try:
            prompt = f"""Detect the primary language of the following text and respond with valid JSON only:

Text to analyze:
"{content[:500]}"

Respond with this exact JSON structure:
{{
    "primary_language": "ar|fr|en|mixed",
    "confidence": 0.0-1.0,
    "secondary_languages": ["ar", "fr", "en"]
}}

Focus on:
- Arabic (ar) - includes Tunisian Arabic dialect
- French (fr) - standard and Tunisian French
- English (en)
- Mixed - if multiple languages are present"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Extract JSON from response
                start = generated_text.find('{')
                end = generated_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = generated_text[start:end]
                    lang_result = json.loads(json_str)
                    return lang_result.get('primary_language', 'ar')
            
            return 'ar'  # Default to Arabic
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'ar'  # Default to Arabic

    def translate_to_french(self, content: str, source_language: str) -> Optional[str]:
        """Translate content to French."""
        if source_language == 'fr':
            return content  # Already French
            
        try:
            prompt = f"""Translate the following {source_language} text to French. Respond with ONLY the French translation, no explanations:

Text to translate:
"{content}"

Requirements:
- Maintain the original meaning and tone
- Use appropriate French terminology for Tunisian context
- Keep proper nouns and names as they are
- Preserve formatting and structure"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                french_text = result.get('response', '').strip()
                
                # Clean up the response - remove any prefixes
                if french_text.startswith('"') and french_text.endswith('"'):
                    french_text = french_text[1:-1]
                
                return french_text if french_text else content
            
            return content  # Fallback to original
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return content  # Fallback to original

    def analyze_sentiment(self, french_content: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment from French translation using direct Ollama call."""
        try:
            prompt = f"""Analysez le sentiment du texte français suivant et répondez avec du JSON valide uniquement :

Texte français à analyser :
"{french_content}"

Répondez avec cette structure JSON exacte :
{{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": -1.0 à 1.0,
    "confidence": 0.0-1.0,
    "reasoning": "explication brève en français"
}}

Considérez :
- Le contexte culturel et politique tunisien
- Le sarcasme et l'ironie
- Les nuances gouvernementales et sociales
- Le ton officiel vs informel

TOUTES les réponses doivent être en français."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Extract JSON from response
                start = generated_text.find('{')
                end = generated_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = generated_text[start:end]
                    return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None
    
    def extract_keywords(self, french_content: str) -> Optional[List[str]]:
        """Extract keywords from French translation using direct Ollama call."""
        try:
            prompt = f"""Extrayez les mots-clés les plus importants du texte français suivant et répondez avec du JSON valide uniquement :

Texte français à analyser :
"{french_content}"

Répondez avec cette structure JSON exacte :
{{
    "keywords": ["mot-clé1", "mot-clé2", "mot-clé3", "mot-clé4", "mot-clé5"],
    "importance_scores": [0.9, 0.8, 0.7, 0.6, 0.5]
}}

Concentrez-vous sur :
- Termes les plus significatifs qui capturent l'essence du contenu
- Terminologie spécifique à la Tunisie
- Termes politiques, économiques et sociaux
- Évitez les mots vides et articles communs
- Maximum 10 mots-clés par ordre d'importance"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 200
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Extract JSON from response
                start = generated_text.find('{')
                end = generated_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = generated_text[start:end]
                    keyword_result = json.loads(json_str)
                    return keyword_result.get('keywords', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def extract_named_entities(self, french_content: str) -> Optional[List[Dict[str, Any]]]:
        """Extract named entities from French translation using direct Ollama call."""
        try:
            prompt = f"""Extrayez les entités nommées du texte français suivant et répondez avec du JSON valide uniquement :

Texte français à analyser :
"{french_content}"

Répondez avec cette structure JSON exacte :
{{
    "entities": [
        {{
            "text": "nom de l'entité",
            "type": "PERSON|ORGANIZATION|LOCATION|EVENT|POLICY",
            "confidence": 0.0-1.0,
            "context": "contexte court"
        }}
    ]
}}

Types d'entités :
- PERSON : Personnes (ministres, officiels, personnalités)
- ORGANIZATION : Organisations (ministères, institutions, entreprises)
- LOCATION : Lieux (villes, régions, pays)
- EVENT : Événements (conférences, réunions, programmes)
- POLICY : Politiques et lois (programmes gouvernementaux, réglementations)

Concentrez-vous sur les entités importantes pour l'intelligence tunisienne."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 400
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Extract JSON from response
                start = generated_text.find('{')
                end = generated_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = generated_text[start:end]
                    entity_result = json.loads(json_str)
                    return entity_result.get('entities', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Named entity extraction failed: {e}")
            return []

    def classify_category(self, french_content: str) -> Optional[str]:
        """Classify content category from French translation using direct Ollama call."""
        try:
            prompt = f"""Classifiez le texte français suivant dans les catégories appropriées et répondez avec du JSON valide uniquement :

Texte français à analyser :
"{french_content}"

Répondez avec cette structure JSON exacte :
{{
    "primary_category": "catégorie principale",
    "confidence": 0.0-1.0,
    "secondary_categories": ["catégorie2", "catégorie3"]
}}

Catégories disponibles :
- politics (Politique)
- economy (Économie)  
- society (Société)
- culture (Culture)
- sports (Sport)
- education (Éducation)
- health (Santé)
- technology (Technologie)
- environment (Environnement)
- security (Sécurité)
- international (International)
- regional (Régional)
- other (Autre)

Considérez le sujet principal et les thèmes du contenu."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Extract JSON from response
                start = generated_text.find('{')
                end = generated_text.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = generated_text[start:end]
                    category_result = json.loads(json_str)
                    return category_result.get('primary_category', 'other')
            
            return 'other'
            
        except Exception as e:
            logger.error(f"Category classification failed: {e}")
            return 'other'
    
    def enrich_article(self, article: Dict[str, Any]) -> bool:
        """Enrich a single article following the complete pipeline."""
        article_id = article.get('id')
        content = article.get('content', '').strip()
        title = article.get('title', '').strip()
        description = article.get('description', '').strip()
        
        # Combine title, description and content for analysis
        full_content = f"{title}. {description}. {content}".strip()
        
        if not full_content:
            logger.warning(f"Article {article_id} has no content to analyze")
            return False
        
        try:
            logger.info(f"Starting enrichment pipeline for article {article_id}")
            
            # Step 1: Language detection
            logger.info(f"Step 1: Language detection for article {article_id}")
            detected_language = self.detect_language(full_content)
            
            # Step 2: Category detection (on original content)
            logger.info(f"Step 2: Category detection for article {article_id}")
            category = self.classify_category(full_content)
            
            # Step 3: Translation to French
            logger.info(f"Step 3: Translation to French for article {article_id}")
            french_content = self.translate_to_french(full_content, detected_language)
            
            # Step 4: Sentiment analysis from French translation
            logger.info(f"Step 4: Sentiment analysis from French for article {article_id}")
            sentiment_result = self.analyze_sentiment(french_content)
            
            # Step 5: Named entities extraction from French translation
            logger.info(f"Step 5: Named entities extraction from French for article {article_id}")
            entities = self.extract_named_entities(french_content)
            
            # Step 6: Keywords extraction from French translation
            logger.info(f"Step 6: Keywords extraction from French for article {article_id}")
            keywords = self.extract_keywords(french_content)
            
            # Re-classify category using French translation for better accuracy
            category = self.classify_category(french_content)
            
            # Prepare update data
            update_data = {}
            
            # Store French translation
            if french_content and french_content != full_content:
                update_data['content_fr'] = french_content
            
            if sentiment_result:
                update_data['sentiment_score'] = sentiment_result.get('sentiment_score', 0.0)
                # Map sentiment to database-compatible values (French)
                sentiment_map = {'positif': 'positif', 'négatif': 'négatif', 'neutre': 'neutre'}
                sentiment_str = sentiment_map.get(sentiment_result.get('sentiment', 'neutre'), 'neutre')
                update_data['sentiment'] = sentiment_str
            
            if keywords:
                # Store keywords as comma-separated string
                update_data['keywords'] = ', '.join(keywords[:10])  # Limit to 10 keywords
            
            if category and category != 'other':
                # Find or create category in content_categories table
                try:
                    # Check by English name first
                    category_result = self.db_manager.client.table("content_categories") \
                        .select("id") \
                        .eq("name_en", category) \
                        .limit(1) \
                        .execute()
                    
                    if category_result.data:
                        update_data['category_id'] = category_result.data[0]['id']
                    else:
                        # Create new category with all language fields
                        new_category = self.db_manager.client.table("content_categories") \
                            .insert({
                                "name_en": category,
                                "name_ar": category,  # Use same for now
                                "name_fr": category,  # Use same for now
                                "description": f"Auto-generated category: {category}"
                            }) \
                            .execute()
                        
                        if new_category.data:
                            update_data['category_id'] = new_category.data[0]['id']
                except Exception as e:
                    logger.warning(f"Could not set category for article {article_id}: {e}")
            
            # Log extracted information
            if entities:
                entity_count = len(entities)
                logger.info(f"Named entities extracted for article {article_id}: {entity_count} entities found")
            
            if keywords:
                keyword_count = len(keywords)
                logger.info(f"Keywords extracted for article {article_id}: {keyword_count} keywords found")
            
            # Update the article
            if update_data:
                update_data['updated_at'] = datetime.now().isoformat()
                update_data['enriched_at'] = datetime.now().isoformat()
                
                result = self.db_manager.client.table("articles") \
                    .update(update_data) \
                    .eq("id", article_id) \
                    .execute()
                
                if result.data:
                    logger.info(f"  ✅ Article {article_id} enriched successfully")
                    return True
                else:
                    logger.error(f"  ❌ Failed to update article {article_id}")
                    return False
            else:
                logger.warning(f"  ⚠️ No enrichment data generated for article {article_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching article {article_id}: {e}")
            return False
    
    def enrich_social_post(self, post: Dict[str, Any]) -> bool:
        """Enrich a single social media post following the complete pipeline."""
        post_id = post.get('id')
        content = post.get('content', '').strip()
        
        if not content:
            logger.warning(f"Post {post_id} has no content to analyze")
            return False
        
        try:
            logger.info(f"Starting enrichment pipeline for post {post_id}")
            
            # Step 1: Language detection
            logger.info(f"Step 1: Language detection for post {post_id}")
            detected_language = self.detect_language(content)
            
            # Step 2: Category detection (on original content)
            logger.info(f"Step 2: Category detection for post {post_id}")
            category = self.classify_category(content)  # Use original for now, will update after translation
            
            # Step 3: Translation to French
            logger.info(f"Step 3: Translation to French for post {post_id}")
            french_content = self.translate_to_french(content, detected_language)
            
            # Step 4: Sentiment analysis from French translation
            logger.info(f"Step 4: Sentiment analysis from French for post {post_id}")
            sentiment_result = self.analyze_sentiment(french_content)
            
            # Step 5: Named entities extraction from French translation
            logger.info(f"Step 5: Named entities extraction from French for post {post_id}")
            entities = self.extract_named_entities(french_content)
            
            # Step 6: Keywords extraction from French translation
            logger.info(f"Step 6: Keywords extraction from French for post {post_id}")
            keywords = self.extract_keywords(french_content)
            
            # Re-classify category using French translation for better accuracy
            category = self.classify_category(french_content)
            
            # Prepare update data
            update_data = {}
            
            # Store French translation
            if french_content and french_content != content:
                update_data['content_fr'] = french_content
            
            if sentiment_result:
                update_data['sentiment_score'] = sentiment_result.get('sentiment_score', 0.0)
                # Map sentiment to database-compatible values (French)
                sentiment_map = {'positif': 'positif', 'négatif': 'négatif', 'neutre': 'neutre'}
                sentiment_str = sentiment_map.get(sentiment_result.get('sentiment', 'neutre'), 'neutre')
                update_data['sentiment'] = sentiment_str
            
            if keywords:
                # Store keywords as comma-separated string
                update_data['keywords'] = ', '.join(keywords[:10])  # Limit to 10 keywords
            
            if category and category != 'other':
                # Find or create category in content_categories table
                try:
                    # Check by English name first
                    category_result = self.db_manager.client.table("content_categories") \
                        .select("id") \
                        .eq("name_en", category) \
                        .limit(1) \
                        .execute()
                    
                    if category_result.data:
                        update_data['category_id'] = category_result.data[0]['id']
                    else:
                        # Create new category with all language fields
                        new_category = self.db_manager.client.table("content_categories") \
                            .insert({
                                "name_en": category,
                                "name_ar": category,  # Use same for now
                                "name_fr": category,  # Use same for now
                                "description": f"Auto-generated category: {category}"
                            }) \
                            .execute()
                        
                        if new_category.data:
                            update_data['category_id'] = new_category.data[0]['id']
                except Exception as e:
                    logger.warning(f"Could not set category for post {post_id}: {e}")
            
            # Keywords column exists in social_media_posts table
            if keywords:
                keyword_count = len(keywords)
                logger.info(f"Keywords extracted for post {post_id}: {keyword_count} keywords found")
            
            # Update the post
            if update_data:
                update_data['updated_at'] = datetime.now().isoformat()
                
                result = self.db_manager.client.table("social_media_posts") \
                    .update(update_data) \
                    .eq("id", post_id) \
                    .execute()
                
                if result.data:
                    logger.info(f"  ✅ Social post {post_id} enriched successfully")
                    return True
                else:
                    logger.error(f"  ❌ Failed to update social post {post_id}")
                    return False
            else:
                logger.warning(f"  ⚠️ No enrichment data generated for post {post_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching social post {post_id}: {e}")
            return False
    
    def get_articles_to_process(self, limit: int, days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles that need enrichment including source_id and content_hash."""
        try:
            query = self.db_manager.client.table("articles") \
                .select("id, title, description, content, pub_date, source_id, content_hash") \
                .is_("sentiment", "null")
            
            if days_back:
                date_from = datetime.now() - timedelta(days=days_back)
                query = query.gte("pub_date", date_from.isoformat())
            
            query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to fetch articles: {e}")
            return []
    
    def get_social_posts_to_process(self, limit: int, days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get social media posts that need enrichment."""
        try:
            query = self.db_manager.client.table("social_media_posts") \
                .select("id, content, account, social_media, publish_date, source_id, url") \
                .is_("sentiment_score", "null") \
                .not_.is_("content", "null")
            
            if days_back:
                date_from = datetime.now() - timedelta(days=days_back)
                query = query.gte("publish_date", date_from.isoformat())
            
            query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to fetch social media posts: {e}")
            return []
    
    def process_articles_batch(self, limit: int, days_back: Optional[int] = None):
        """Process a batch of articles for enrichment with proper state tracking."""
        logger.info(f"Starting batch processing - limit: {limit}, days_back: {days_back}")
        
        # Get articles to process
        articles = self.get_articles_to_process(limit, days_back)
        
        if not articles:
            print("📰 No articles found to process")
            return
        
        print(f"📰 Found {len(articles)} articles to process")
        
        # Process each article with comprehensive tracking
        successful = 0
        failed = 0
        start_time = time.time()
        batch_start_time = datetime.now()
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')[:50]
            print(f"\n🔄 Processing article {i}/{len(articles)}: {title}...")
            logger.info(f"Enriching article {i}: {title}...")
            
            try:
                if self.enrich_article(article):
                    successful += 1
                    print("   ✅ Success")
                else:
                    failed += 1
                    print("   ❌ Failed")
                    
                    # Update enrichment state for failure
                    source_id = article.get('source_id')
                    if source_id:
                        self.comprehensive_service.update_enrichment_state_failure('article', source_id)
                        
            except Exception as e:
                failed += 1
                print(f"   💥 Error: {e}")
                logger.error(f"Article {i} processing error: {e}")
                
                # Update enrichment state for failure
                source_id = article.get('source_id')
                if source_id:
                    self.comprehensive_service.update_enrichment_state_failure('article', source_id)
        
        # Calculate statistics
        total_time = time.time() - start_time
        avg_time = total_time / len(articles) if articles else 0
        success_rate = (successful / len(articles)) * 100 if articles else 0
        processing_duration_ms = int(total_time * 1000)
        
        # Log batch processing results
        try:
            self.comprehensive_service.log_enrichment_batch(
                content_type='article',
                source_id=None,  # Mixed sources in batch
                items_processed=len(articles),
                items_successful=successful,
                items_failed=failed,
                processing_duration_ms=processing_duration_ms,
                started_at=batch_start_time,
                batch_size=limit
            )
        except Exception as e:
            logger.error(f"Failed to log batch results: {e}")
        
        # Display summary
        print(f"\n📊 Batch Processing Complete!")
        print(f"   Total Articles: {len(articles)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Processing Time: {total_time:.1f}s")
        print(f"   Avg Time per Article: {avg_time:.1f}s")
        print(f"   📊 Batch logged to enrichment_log table")
        print(f"   📊 Source states updated in enrichment_state table")
    
    def process_social_posts_batch(self, limit: int, days_back: Optional[int] = None):
        """Process a batch of social media posts for enrichment."""
        logger.info(f"Starting social media posts batch processing - limit: {limit}, days_back: {days_back}")
        
        # Get posts to process
        posts = self.get_social_posts_to_process(limit, days_back)
        
        if not posts:
            print("📱 No social media posts found to process")
            return
        
        print(f"📱 Found {len(posts)} social media posts to process")
        
        # Process each post
        successful = 0
        failed = 0
        start_time = time.time()
        
        for i, post in enumerate(posts, 1):
            account = post.get('account', 'Unknown')[:30]
            content_preview = (post.get('content', '') or '')[:50]
            print(f"\n🔄 Processing post {i}/{len(posts)}: {account} - {content_preview}...")
            logger.info(f"Enriching social post {i}: {account}")
            
            try:
                if self.enrich_social_post(post):
                    successful += 1
                    print("   ✅ Success")
                else:
                    failed += 1
                    print("   ❌ Failed")
                    
            except Exception as e:
                failed += 1
                print(f"   💥 Error: {e}")
                logger.error(f"Social post {i} processing error: {e}")
        
        # Calculate statistics
        total_time = time.time() - start_time
        avg_time = total_time / len(posts) if posts else 0
        success_rate = (successful / len(posts)) * 100 if posts else 0
        
        # Display summary
        print(f"\n📊 Social Media Posts Batch Complete!")
        print(f"   Total Posts: {len(posts)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Processing Time: {total_time:.1f}s")
        print(f"   Avg Time per Post: {avg_time:.1f}s")
    
    def process_all_content_batch(self, limit: int, days_back: Optional[int] = None):
        """Process both articles and social media posts."""
        print("🚀 Processing ALL Content Types")
        print("=" * 50)
        
        # Process articles first
        print("\n📰 PROCESSING ARTICLES")
        print("-" * 30)
        self.process_articles_batch(limit, days_back)
        
        # Process social media posts
        print("\n📱 PROCESSING SOCIAL MEDIA POSTS")
        print("-" * 40)
        self.process_social_posts_batch(limit, days_back)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Batch Enrichment for MVP - Articles & Social Media")
    parser.add_argument('--limit', type=int, default=10, help='Number of items to process per content type')
    parser.add_argument('--days-back', type=int, help='Process content from N days back')
    parser.add_argument('--articles-only', action='store_true', help='Process only articles')
    parser.add_argument('--social-only', action='store_true', help='Process only social media posts')
    
    args = parser.parse_args()
    
    print("🚀 Simple Batch Enrichment - MVP")
    print("=" * 40)
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama not running. Start with: ollama serve")
            sys.exit(1)
        print("✅ Ollama is running")
    except:
        print("❌ Cannot connect to Ollama. Start with: ollama serve")
        sys.exit(1)
    
    # Initialize enricher and process
    try:
        enricher = SimpleAIEnricher()
        
        if args.articles_only:
            print("📰 Processing ARTICLES ONLY")
            enricher.process_articles_batch(limit=args.limit, days_back=args.days_back)
        elif args.social_only:
            print("📱 Processing SOCIAL MEDIA POSTS ONLY")
            enricher.process_social_posts_batch(limit=args.limit, days_back=args.days_back)
        else:
            print("🌐 Processing ALL CONTENT TYPES")
            enricher.process_all_content_batch(limit=args.limit, days_back=args.days_back)
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
