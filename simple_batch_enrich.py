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
        """Enrich a single article using comprehensive enrichment service."""
        article_id = article.get('id')
        
        try:
            # Use comprehensive enrichment service
            success = self.comprehensive_service.process_article(article)
            
            if success:
                logger.info(f"  ✅ Article {article_id} comprehensively enriched")
                return True
            else:
                logger.error(f"  ❌ Failed to enrich article {article_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error enriching article {article_id}: {e}")
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
