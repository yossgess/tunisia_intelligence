#!/usr/bin/env python3
"""
Simple Standalone Batch Enrichment for MVP

Direct implementation without complex imports.
Works immediately for MVP deployment.
"""

import requests
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simple_batch_enrichment.log')
    ]
)
logger = logging.getLogger(__name__)

class SimpleAIEnricher:
    """Simple AI enricher using direct Ollama calls."""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model = "qwen2.5:7b"
        self.db_manager = None
        
        # Initialize database
        try:
            from config.database import DatabaseManager
            self.db_manager = DatabaseManager()
            logger.info("Database manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def analyze_sentiment(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment using direct Ollama call."""
        try:
            prompt = f"""Analysez le sentiment du texte suivant et répondez avec du JSON valide uniquement :

Texte à analyser :
"{content}"

Répondez avec cette structure JSON exacte :
{{
    "sentiment": "positif|négatif|neutre",
    "sentiment_score": -1.0 à 1.0,
    "confidence": 0.0-1.0,
    "reasoning": "explication brève en français",
    "language_detected": "ar|fr|en"
}}

Considérez :
- Le contexte culturel et les expressions tunisiennes
- Le sarcasme et l'ironie
- Les nuances politiques et sociales

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
    
    def extract_keywords(self, content: str) -> Optional[List[str]]:
        """Extract keywords using direct Ollama call."""
        try:
            prompt = f"""Extract the most important keywords and key phrases from the following text and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "language_detected": "ar|fr|en"
}}

Focus on:
- Most significant terms that capture the content essence
- Tunisian-specific terminology and concepts
- Political, economic, and social terms
- Avoid common stop words and articles
- Maximum 10 keywords"""

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
    
    def classify_category(self, content: str) -> Optional[str]:
        """Classify content category using direct Ollama call."""
        try:
            prompt = f"""Classify the following text into appropriate categories and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "primary_category": "main category",
    "confidence": 0.0-1.0,
    "language_detected": "ar|fr|en"
}}

Available categories:
- politics (سياسة / Politique)
- economy (اقتصاد / Économie)  
- society (مجتمع / Société)
- culture (ثقافة / Culture)
- sports (رياضة / Sport)
- education (تعليم / Éducation)
- health (صحة / Santé)
- technology (تكنولوجيا / Technologie)
- environment (بيئة / Environnement)
- security (أمن / Sécurité)
- international (دولي / International)
- regional (جهوي / Régional)
- other (أخرى / Autre)

Consider the main subject matter and themes."""

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
        """Enrich a single article with AI analysis."""
        try:
            article_id = article.get('id')
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', '')
            
            # Combine content for analysis
            full_content = f"{title} {description} {content}".strip()
            
            if len(full_content) < 50:
                logger.warning(f"Article {article_id} too short, skipping")
                return False
            
            # Truncate if too long
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            
            logger.info(f"Enriching article {article_id}: {title[:50]}...")
            
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(full_content)
            
            # Extract keywords
            keywords = self.extract_keywords(full_content)
            
            # Classify category
            category = self.classify_category(full_content)
            
            # Prepare update data
            update_data = {}
            
            if sentiment_result:
                sentiment = sentiment_result.get('sentiment')
                sentiment_score = sentiment_result.get('sentiment_score', 0.0)
                confidence = sentiment_result.get('confidence', 0.0)
                
                # Map to French labels if needed
                sentiment_mapping = {
                    'positive': 'positif',
                    'negative': 'négatif', 
                    'neutral': 'neutre',
                    'positif': 'positif',
                    'négatif': 'négatif',
                    'neutre': 'neutre'
                }
                
                if sentiment and sentiment.lower() in sentiment_mapping:
                    french_sentiment = sentiment_mapping[sentiment.lower()]
                    update_data['sentiment'] = french_sentiment
                    update_data['sentiment_score'] = sentiment_score
                    logger.info(f"  Sentiment: {french_sentiment} ({sentiment_score:.2f})")
            
            if keywords:
                # Store keywords as JSON string
                update_data['keywords'] = json.dumps(keywords[:10], ensure_ascii=False)
                logger.info(f"  Keywords: {', '.join(keywords[:5])}")
            
            if category and category != 'other':
                category_mapping = {
                    'politics': 'Politique',
                    'economy': 'Économie',
                    'society': 'Société', 
                    'culture': 'Culture',
                    'sports': 'Sport',
                    'security': 'Sécurité',
                    'international': 'International',
                    'other': 'Autre'
                }
                
                french_category = category_mapping.get(category, category)
                update_data['category'] = french_category
                logger.info(f"  Category: {french_category}")
            
            # Update database
            if update_data:
                response = self.db_manager.client.table("articles") \
                    .update(update_data) \
                    .eq("id", article_id) \
                    .execute()
                
                if response.data:
                    logger.info(f"  ✅ Article {article_id} enriched successfully")
                    return True
                else:
                    logger.error(f"  ❌ Failed to update article {article_id}")
                    return False
            else:
                logger.warning(f"  ⚠️  No enrichment data for article {article_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching article {article.get('id')}: {e}")
            return False
    
    def get_articles_to_process(self, limit: int, days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles that need enrichment."""
        try:
            query = self.db_manager.client.table("articles") \
                .select("id, title, description, content, pub_date") \
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
    
    def process_articles_batch(self, limit: int = 10, days_back: Optional[int] = None):
        """Process a batch of articles."""
        logger.info(f"Starting batch processing - limit: {limit}, days_back: {days_back}")
        
        # Get articles to process
        articles = self.get_articles_to_process(limit, days_back)
        
        if not articles:
            print("📰 No articles found to process")
            return
        
        print(f"📰 Found {len(articles)} articles to process")
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        for i, article in enumerate(articles, 1):
            print(f"\n🔄 Processing article {i}/{len(articles)}: {article.get('title', 'No title')[:50]}...")
            
            if self.enrich_article(article):
                successful += 1
                print(f"   ✅ Success")
            else:
                failed += 1
                print(f"   ❌ Failed")
            
            # Small delay between articles
            time.sleep(1)
        
        # Summary
        total_time = time.time() - start_time
        success_rate = (successful / len(articles)) * 100 if articles else 0
        
        print(f"\n📊 Batch Processing Complete!")
        print(f"   Total Articles: {len(articles)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Processing Time: {total_time:.1f}s")
        print(f"   Avg Time per Article: {total_time/len(articles):.1f}s")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Batch Enrichment for MVP")
    parser.add_argument('--limit', type=int, default=10, help='Number of articles to process')
    parser.add_argument('--days-back', type=int, help='Process articles from N days back')
    
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
        enricher.process_articles_batch(limit=args.limit, days_back=args.days_back)
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
