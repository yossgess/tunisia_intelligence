#!/usr/bin/env python3
"""
Production batch vectorization of French articles using sentence transformers.
"""

import sys
import os
import time
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager
from ai_enrichment.core.sentence_transformer_service import SentenceTransformerVectorService, SentenceTransformerConfig

def batch_vectorize_french_articles(limit: int = 15):
    """Vectorize a batch of French articles."""
    print(f"🚀 BATCH VECTORIZATION OF {limit} FRENCH ARTICLES")
    print("=" * 70)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        db = DatabaseManager()
        
        config = SentenceTransformerConfig(
            batch_size=16,  # Process 16 at once for optimal performance
            max_workers=4,
            cache_vectors=True
        )
        vector_service = SentenceTransformerVectorService(config)
        
        print(f"✅ Services initialized")
        print(f"   Model: {config.model_name}")
        print(f"   Batch size: {config.batch_size}")
        print(f"   Dimensions: {config.embedding_dimensions}")
        
        # Fetch articles with French content
        print(f"\n📊 Fetching {limit} articles...")
        
        # Get articles using simple query
        articles_result = db.client.table("articles").select(
            "id", "title", "content_fr", "content", "created_at"
        ).order("created_at", desc=True).limit(limit).execute()
        
        if not articles_result.data:
            print("❌ No articles found in database")
            return
        
        articles = articles_result.data
        print(f"✅ Found {len(articles)} articles")
        
        # Prepare content for vectorization
        print("\n📝 Preparing content for vectorization...")
        batch_items = []
        content_stats = {"french": 0, "original": 0, "title_only": 0}
        
        for article in articles:
            # Prioritize French content, fallback to original, then title
            content = ""
            content_type = ""
            
            if article.get('content_fr') and len(article['content_fr'].strip()) > 50:
                content = article['content_fr']
                content_type = "french"
                content_stats["french"] += 1
            elif article.get('content') and len(article['content'].strip()) > 50:
                content = article['content']
                content_type = "original"
                content_stats["original"] += 1
            elif article.get('title') and len(article['title'].strip()) > 10:
                content = article['title']
                content_type = "title_only"
                content_stats["title_only"] += 1
            
            if content:
                batch_items.append({
                    'id': article['id'],
                    'content': content,
                    'type': 'article',
                    'content_source': content_type,
                    'title': article.get('title', '')[:100],  # For display
                    'created_at': article.get('created_at', '')
                })
        
        print(f"✅ Prepared {len(batch_items)} items for vectorization")
        print(f"   French content: {content_stats['french']}")
        print(f"   Original content: {content_stats['original']}")
        print(f"   Title only: {content_stats['title_only']}")
        
        if not batch_items:
            print("❌ No suitable content found for vectorization")
            return
        
        # Check for existing vectors
        print(f"\n🔍 Checking for existing vectors...")
        existing_ids = []
        for item in batch_items:
            check_result = db.client.table("content_embeddings").select("id").eq(
                "content_type", "article"
            ).eq("content_id", item['id']).execute()
            
            if check_result.data:
                existing_ids.append(item['id'])
        
        print(f"   Found {len(existing_ids)} existing vectors")
        print(f"   Will process {len(batch_items) - len(existing_ids)} new vectors")
        
        # Run batch vectorization
        print(f"\n🚀 Starting batch vectorization...")
        start_time = time.time()
        
        results = vector_service.batch_generate_vectors(
            batch_items, 
            force_regenerate=False  # Skip existing vectors
        )
        
        vectorization_time = time.time() - start_time
        
        # Analyze results
        successful_vectors = [r for r in results if r.vector is not None]
        failed_vectors = [r for r in results if r.vector is None]
        
        print(f"\n📊 VECTORIZATION RESULTS")
        print("=" * 50)
        print(f"Total articles processed: {len(results)}")
        print(f"Successful vectors: {len(successful_vectors)}")
        print(f"Failed vectors: {len(failed_vectors)}")
        print(f"Success rate: {len(successful_vectors)/len(results)*100:.1f}%")
        print(f"Total processing time: {vectorization_time:.3f}s")
        print(f"Average time per article: {vectorization_time/len(results):.3f}s")
        
        # Store vectors in database
        if successful_vectors:
            print(f"\n💾 Storing {len(successful_vectors)} vectors in database...")
            storage_start = time.time()
            
            stored_count = 0
            for result in successful_vectors:
                try:
                    # Check if vector already exists
                    existing = db.client.table("content_embeddings").select("id").eq(
                        "content_type", "article"
                    ).eq("content_id", int(result.content_id)).execute()
                    
                    if existing.data:
                        print(f"   Skipping article {result.content_id} (vector exists)")
                        continue
                    
                    # Store new vector
                    embedding_data = {
                        'content_type': 'article',
                        'content_id': int(result.content_id),
                        'content_embedding': result.vector,
                        'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                        'embedding_version': '2.0',
                        'content_length': len(next(item['content'] for item in batch_items if str(item['id']) == result.content_id)),
                        'embedding_quality_score': 0.95,  # High quality for sentence transformers
                        'language': 'french',
                        'content_hash': result.content_hash
                    }
                    
                    storage_result = db.client.table("content_embeddings").insert(embedding_data).execute()
                    
                    if storage_result.data:
                        stored_count += 1
                        print(f"   ✅ Stored vector for article {result.content_id}")
                    else:
                        print(f"   ❌ Failed to store vector for article {result.content_id}")
                        
                except Exception as e:
                    print(f"   ❌ Error storing article {result.content_id}: {e}")
            
            storage_time = time.time() - storage_start
            
            print(f"\n✅ Storage completed!")
            print(f"   Vectors stored: {stored_count}")
            print(f"   Storage time: {storage_time:.3f}s")
        
        # Show sample results
        print(f"\n📋 SAMPLE VECTORIZED ARTICLES")
        print("=" * 60)
        
        for i, result in enumerate(successful_vectors[:5]):
            # Find corresponding article info
            article_info = next(item for item in batch_items if str(item['id']) == result.content_id)
            
            print(f"\n{i+1}. Article ID: {result.content_id}")
            print(f"   Title: {article_info['title']}")
            print(f"   Content source: {article_info['content_source']}")
            print(f"   Vector dimensions: {len(result.vector)}")
            print(f"   Processing time: {result.processing_time:.3f}s")
            print(f"   Content hash: {result.content_hash[:16]}...")
        
        # Performance summary
        print(f"\n🏆 PERFORMANCE SUMMARY")
        print("=" * 50)
        print(f"Articles processed: {len(results)}")
        print(f"Total time: {vectorization_time:.3f}s")
        print(f"Average per article: {vectorization_time/len(results):.3f}s")
        print(f"Throughput: {len(results)/vectorization_time:.1f} articles/second")
        print(f"Estimated time for 1000 articles: {(vectorization_time/len(results))*1000/60:.1f} minutes")
        
        # Model info
        model_info = vector_service.get_model_info()
        print(f"\n📊 MODEL INFORMATION")
        print("=" * 40)
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        print(f"\n🎉 Batch vectorization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in batch vectorization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    batch_vectorize_french_articles(15)
