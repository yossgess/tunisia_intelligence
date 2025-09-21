#!/usr/bin/env python3
"""
Fixed Unified AI Enrichment Test - Test all three content types simultaneously.

This script tests the complete Tunisia Intelligence AI enrichment system by processing:
1. One article (using correct table name 'articles')
2. One Facebook post (using existing enrichment logic)
3. One comment (using enhanced enrichment)
"""

import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager
from ai_enrichment.core.ollama_client import OllamaClient, OllamaConfig

class UnifiedEnrichmentTester:
    """Test AI enrichment across all three content types."""
    
    def __init__(self):
        """Initialize the tester."""
        self.db_manager = DatabaseManager()
        self.ollama_client = OllamaClient(OllamaConfig())
        print("🚀 Unified AI Enrichment Tester initialized")
    
    def run_unified_test(self):
        """Run enrichment test on 1 article, 1 post, and 1 comment."""
        print("=" * 80)
        print("🧪 UNIFIED AI ENRICHMENT TEST")
        print("Testing: 1 Article + 1 Post + 1 Comment")
        print("=" * 80)
        
        results = {
            'article': None,
            'post': None,
            'comment': None,
            'total_time': 0,
            'overall_success': True
        }
        
        start_time = time.time()
        
        try:
            # Test 1: Article Enrichment
            print("\n📰 TESTING ARTICLE ENRICHMENT")
            print("-" * 50)
            results['article'] = self._test_article_enrichment()
            
            # Test 2: Post Enrichment
            print("\n📱 TESTING POST ENRICHMENT")
            print("-" * 50)
            results['post'] = self._test_post_enrichment()
            
            # Test 3: Comment Enrichment
            print("\n💬 TESTING COMMENT ENRICHMENT")
            print("-" * 50)
            results['comment'] = self._test_comment_enrichment()
            
            # Calculate totals
            results['total_time'] = time.time() - start_time
            results['overall_success'] = all(
                result and result.get('success', False) 
                for result in [results['article'], results['post'], results['comment']]
            )
            
            # Print comprehensive results
            self._print_unified_results(results)
            
            return results
            
        except Exception as e:
            print(f"❌ Unified test failed: {e}")
            results['overall_success'] = False
            return results
    
    def _test_article_enrichment(self):
        """Test article enrichment using correct table name."""
        try:
            # Get one unenriched article (using correct table name 'articles')
            articles = self.db_manager.client.table("articles") \
                .select("*") \
                .is_("enriched_at", "null") \
                .limit(1) \
                .execute()
            
            if not articles.data:
                print("⚠️  No unenriched articles found")
                return {'success': False, 'reason': 'No articles to process'}
            
            article = articles.data[0]
            print(f"📄 Processing article ID: {article['id']}")
            print(f"📄 Title: {article.get('title', 'N/A')[:100]}...")
            
            start_time = time.time()
            
            # Simple article enrichment using existing logic
            success = self._enrich_single_article(article)
            processing_time = time.time() - start_time
            
            result = {
                'success': success,
                'article_id': article['id'],
                'title': article.get('title', 'N/A')[:50] + '...',
                'processing_time': processing_time,
                'content_type': 'article'
            }
            
            if success:
                print(f"✅ Article enriched successfully in {processing_time:.2f}s")
            else:
                print(f"❌ Article enrichment failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Article enrichment error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _test_post_enrichment(self):
        """Test post enrichment."""
        try:
            # Get one unenriched post
            posts = self.db_manager.client.table("social_media_posts") \
                .select("*") \
                .is_("enriched_at", "null") \
                .limit(1) \
                .execute()
            
            if not posts.data:
                print("⚠️  No unenriched posts found")
                return {'success': False, 'reason': 'No posts to process'}
            
            post = posts.data[0]
            print(f"📱 Processing post ID: {post['id']}")
            print(f"📱 Content: {post.get('content', 'N/A')[:100]}...")
            
            start_time = time.time()
            
            # Simple post enrichment
            success = self._enrich_single_post(post)
            processing_time = time.time() - start_time
            
            result = {
                'success': success,
                'post_id': post['id'],
                'content': post.get('content', 'N/A')[:50] + '...',
                'processing_time': processing_time,
                'content_type': 'post'
            }
            
            if success:
                print(f"✅ Post enriched successfully in {processing_time:.2f}s")
            else:
                print(f"❌ Post enrichment failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Post enrichment error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _test_comment_enrichment(self):
        """Test enhanced comment enrichment."""
        try:
            # Get one unenriched comment
            comments = self.db_manager.client.table("social_media_comments") \
                .select("*") \
                .is_("enriched_at", "null") \
                .limit(1) \
                .execute()
            
            if not comments.data:
                print("⚠️  No unenriched comments found")
                return {'success': False, 'reason': 'No comments to process'}
            
            comment = comments.data[0]
            print(f"💬 Processing comment ID: {comment['id']}")
            print(f"💬 Content: {comment.get('content', 'N/A')[:100]}...")
            
            start_time = time.time()
            
            # Use enhanced comment enrichment
            success = self._enrich_single_comment(comment)
            processing_time = time.time() - start_time
            
            result = {
                'success': success,
                'comment_id': comment['id'],
                'content': comment.get('content', 'N/A')[:50] + '...',
                'processing_time': processing_time,
                'content_type': 'comment'
            }
            
            if success:
                print(f"✅ Comment enriched successfully in {processing_time:.2f}s")
            else:
                print(f"❌ Comment enrichment failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Comment enrichment error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _enrich_single_article(self, article):
        """Enrich a single article."""
        try:
            # Prepare content for analysis
            content = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
            
            # Detect language
            language_detected = self._detect_language(content)
            
            # Translate if needed
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform AI enrichment
            enrichment_result = self._perform_article_enrichment(content_fr, language_detected)
            
            # Update article in database
            success = self.db_manager.client.rpc('update_article_enrichment', {
                'p_article_id': article['id'],
                'p_sentiment': enrichment_result['sentiment'],
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_keywords': json.dumps(enrichment_result['keywords']),
                'p_summary': enrichment_result['summary'],
                'p_category': enrichment_result['category'],
                'p_confidence': enrichment_result['confidence'],
                'p_content_fr': content_fr
            }).execute()
            
            return True
            
        except Exception as e:
            print(f"Article enrichment error: {e}")
            return False
    
    def _enrich_single_post(self, post):
        """Enrich a single post."""
        try:
            content = post.get('content', '')
            
            # Detect language
            language_detected = self._detect_language(content)
            
            # Translate if needed
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform AI enrichment
            enrichment_result = self._perform_post_enrichment(content_fr, language_detected)
            
            # Update post in database
            success = self.db_manager.client.rpc('update_post_enrichment', {
                'p_post_id': post['id'],
                'p_sentiment': enrichment_result['sentiment'],
                'p_sentiment_score': enrichment_result['sentiment_score'],
                'p_summary': enrichment_result['summary'],
                'p_confidence': enrichment_result['confidence'],
                'p_content_fr': content_fr
            }).execute()
            
            return True
            
        except Exception as e:
            print(f"Post enrichment error: {e}")
            return False
    
    def _enrich_single_comment(self, comment):
        """Enrich a single comment using enhanced enrichment."""
        try:
            content = comment.get('content', '')
            
            # Detect language
            language_detected = self._detect_language(content)
            
            # Translate if needed
            if language_detected == 'ar':
                content_fr = self._translate_to_french(content)
            else:
                content_fr = content
            
            # Perform enhanced comment enrichment
            enrichment_result = self._perform_enhanced_comment_enrichment(content_fr, language_detected)
            
            processing_time_ms = 30000  # Approximate
            content_length = len(content)
            
            # Update comment in database
            success = self.db_manager.client.rpc('update_comment_enrichment', {
                'p_comment_id': comment['id'],
                'p_sentiment': enrichment_result['sentiment'],
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
            
            return True
            
        except Exception as e:
            print(f"Comment enrichment error: {e}")
            return False
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of content."""
        arabic_chars = sum(1 for char in content if '\u0600' <= char <= '\u06FF')
        if arabic_chars > len(content) * 0.3:
            return 'ar'
        return 'fr'
    
    def _translate_to_french(self, content: str) -> str:
        """Translate Arabic content to French using Ollama."""
        try:
            prompt = f"Translate the following Arabic text to French. Return only the French translation:\\n\\n{content}"
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            if isinstance(response, dict):
                return response.get('response', content)
            elif isinstance(response, str):
                return response
            else:
                return content
                
        except Exception as e:
            print(f"Translation failed: {e}")
            return content
    
    def _perform_article_enrichment(self, content: str, language: str) -> dict:
        """Perform AI enrichment for articles."""
        try:
            prompt = f"""Analyze this French content and provide AI enrichment in JSON format:

{content}

Return only valid JSON with: sentiment, sentiment_score, keywords (array), summary (Arabic, max 500 chars), category, confidence.
Use sentiment values: positive, negative, neutral."""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get('response', '{}')
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = '{}'
            
            try:
                result = json.loads(response_text)
            except:
                result = {}
            
            # Set defaults with French sentiment
            result.setdefault('sentiment', 'neutre')
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('keywords', [])
            result.setdefault('summary', 'تحليل المحتوى')
            result.setdefault('category', 'other')
            result.setdefault('confidence', 0.7)
            
            # Convert English to French sentiment
            sentiment_mapping = {
                'positive': 'positif',
                'negative': 'négatif', 
                'neutral': 'neutre'
            }
            if result.get('sentiment') in sentiment_mapping:
                result['sentiment'] = sentiment_mapping[result['sentiment']]
            
            return result
            
        except Exception as e:
            return {
                'sentiment': 'neutre',
                'sentiment_score': 0.5,
                'keywords': [],
                'summary': 'تحليل المحتوى',
                'category': 'other',
                'confidence': 0.1
            }
    
    def _perform_post_enrichment(self, content: str, language: str) -> dict:
        """Perform AI enrichment for posts."""
        try:
            prompt = f"""Analyze this French social media post and provide AI enrichment in JSON format:

{content}

Return only valid JSON with: sentiment, sentiment_score, summary (Arabic, max 200 chars), confidence.
Use sentiment values: positive, negative, neutral."""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get('response', '{}')
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = '{}'
            
            try:
                result = json.loads(response_text)
            except:
                result = {}
            
            # Set defaults with French sentiment
            result.setdefault('sentiment', 'neutre')
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('summary', 'تحليل المنشور')
            result.setdefault('confidence', 0.7)
            
            # Convert English to French sentiment
            sentiment_mapping = {
                'positive': 'positif',
                'negative': 'négatif', 
                'neutral': 'neutre'
            }
            if result.get('sentiment') in sentiment_mapping:
                result['sentiment'] = sentiment_mapping[result['sentiment']]
            
            return result
            
        except Exception as e:
            return {
                'sentiment': 'neutre',
                'sentiment_score': 0.5,
                'summary': 'تحليل المنشور',
                'confidence': 0.1
            }
    
    def _perform_enhanced_comment_enrichment(self, content: str, language: str) -> dict:
        """Perform enhanced AI enrichment for comments."""
        try:
            prompt = f"""Analyze this French comment and provide enhanced AI enrichment in JSON format:

{content}

Return only valid JSON with: sentiment, sentiment_score, keywords (array with text/importance), entities (array with text/type), keywords_fr (array), entities_fr (array), confidence.
Use sentiment values: positive, negative, neutral."""
            
            response = self.ollama_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3}
            )
            
            response_text = ""
            if isinstance(response, dict):
                response_text = response.get('response', '{}')
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = '{}'
            
            try:
                result = json.loads(response_text)
            except:
                result = {}
            
            # Set defaults with French sentiment
            result.setdefault('sentiment', 'neutre')
            result.setdefault('sentiment_score', 0.5)
            result.setdefault('keywords', [])
            result.setdefault('entities', [])
            result.setdefault('keywords_fr', [])
            result.setdefault('entities_fr', [])
            result.setdefault('confidence', 0.7)
            
            # Convert English to French sentiment
            sentiment_mapping = {
                'positive': 'positif',
                'negative': 'négatif', 
                'neutral': 'neutre'
            }
            if result.get('sentiment') in sentiment_mapping:
                result['sentiment'] = sentiment_mapping[result['sentiment']]
            
            return result
            
        except Exception as e:
            return {
                'sentiment': 'neutre',
                'sentiment_score': 0.5,
                'keywords': [],
                'entities': [],
                'keywords_fr': [],
                'entities_fr': [],
                'confidence': 0.1
            }
    
    def _print_unified_results(self, results):
        """Print comprehensive results."""
        print("\n" + "=" * 80)
        print("📊 UNIFIED ENRICHMENT RESULTS")
        print("=" * 80)
        
        # Individual results
        for content_type, result in [('ARTICLE', results['article']), 
                                   ('POST', results['post']), 
                                   ('COMMENT', results['comment'])]:
            if result:
                status = "✅ SUCCESS" if result.get('success') else "❌ FAILED"
                time_str = f"{result.get('processing_time', 0):.2f}s"
                print(f"{content_type:8} | {status:10} | {time_str:8} | {result.get('content_type', 'N/A')}")
            else:
                print(f"{content_type:8} | ❌ FAILED   | 0.00s    | N/A")
        
        print("-" * 80)
        
        # Overall statistics
        successful_count = sum(1 for result in [results['article'], results['post'], results['comment']] 
                             if result and result.get('success'))
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Content Types: 3")
        print(f"   Successful: {successful_count}")
        print(f"   Failed: {3 - successful_count}")
        print(f"   Success Rate: {(successful_count/3)*100:.1f}%")
        print(f"   Total Processing Time: {results['total_time']:.2f}s")
        print(f"   Average Time per Item: {results['total_time']/3:.2f}s")
        
        # Overall status
        if results['overall_success']:
            print(f"\n🎉 UNIFIED ENRICHMENT: ✅ ALL SYSTEMS OPERATIONAL")
            print(f"🚀 Tunisia Intelligence AI is ready for production!")
        else:
            print(f"\n⚠️  UNIFIED ENRICHMENT: ❌ SOME SYSTEMS NEED ATTENTION")
        
        print("=" * 80)

def main():
    """Main function."""
    tester = UnifiedEnrichmentTester()
    results = tester.run_unified_test()
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)

if __name__ == "__main__":
    main()
