#!/usr/bin/env python3
"""
Test the new fast sentence transformer vectorization service.
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager
from ai_enrichment.core.sentence_transformer_service import SentenceTransformerVectorService, SentenceTransformerConfig

def test_fast_vectorization():
    """Test the new fast vectorization service."""
    print("🚀 TESTING FAST SENTENCE TRANSFORMER VECTORIZATION")
    print("=" * 70)
    
    try:
        # Initialize the fast service
        print("🔧 Initializing sentence transformer service...")
        config = SentenceTransformerConfig()
        vector_service = SentenceTransformerVectorService(config)
        
        print(f"✅ Model loaded: {config.model_name}")
        print(f"   Dimensions: {config.embedding_dimensions}")
        print(f"   Device: {config.device}")
        
        # Health check
        print("\n🏥 Running health check...")
        if vector_service.health_check():
            print("✅ Service is healthy")
        else:
            print("❌ Service health check failed")
            return
        
        # Test single vector generation
        print("\n📝 Testing single vector generation...")
        test_content = """
        Une cyberattaque majeure a perturbé les systèmes informatiques de plusieurs aéroports européens aujourd'hui, 
        causant des retards et des annulations de vols. Les autorités enquêtent sur l'origine de cette attaque 
        qui semble cibler spécifiquement les infrastructures de transport.
        """
        
        start_time = time.time()
        result = vector_service.generate_vector(
            content=test_content,
            content_id="999999",
            content_type="article"
        )
        processing_time = time.time() - start_time
        
        if result.vector:
            print(f"✅ Vector generated successfully!")
            print(f"   Dimensions: {len(result.vector)}")
            print(f"   Processing time: {processing_time:.3f}s")
            print(f"   Content hash: {result.content_hash[:16]}...")
            print(f"   Model used: {result.model_used}")
        else:
            print(f"❌ Vector generation failed: {result.error}")
            return
        
        # Test database storage
        print("\n💾 Testing database storage...")
        db = DatabaseManager()
        
        # Clean up any existing test record
        db.client.table("content_embeddings").delete().eq("content_id", 999999).execute()
        
        embedding_data = {
            'content_type': 'article',
            'content_id': 999999,
            'content_embedding': result.vector,
            'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            'embedding_version': '1.0',
            'content_length': len(test_content),
            'embedding_quality_score': 0.95,
            'language': 'french',
            'content_hash': result.content_hash
        }
        
        storage_result = db.client.table("content_embeddings").insert(embedding_data).execute()
        
        if storage_result.data:
            print("✅ Vector stored successfully in database!")
            print(f"   Record ID: {storage_result.data[0]['id']}")
            
            # Clean up
            db.client.table("content_embeddings").delete().eq("content_id", 999999).execute()
            print("✅ Test record cleaned up")
        else:
            print("❌ Failed to store vector in database")
        
        # Test batch processing
        print("\n📊 Testing batch processing...")
        
        # Get some real articles
        articles_result = db.client.table("articles").select("id", "title", "content_fr").limit(5).execute()
        
        if articles_result.data:
            print(f"✅ Found {len(articles_result.data)} articles for batch test")
            
            # Prepare batch items
            batch_items = []
            for article in articles_result.data:
                content = article.get('content_fr') or article.get('title', '')
                if content:
                    batch_items.append({
                        'id': article['id'],
                        'content': content,
                        'type': 'article'
                    })
            
            if batch_items:
                print(f"📦 Processing batch of {len(batch_items)} items...")
                
                batch_start = time.time()
                batch_results = vector_service.batch_generate_vectors(batch_items)
                batch_time = time.time() - batch_start
                
                successful = len([r for r in batch_results if r.vector is not None])
                
                print(f"✅ Batch processing completed!")
                print(f"   Total time: {batch_time:.3f}s")
                print(f"   Average time per item: {batch_time/len(batch_items):.3f}s")
                print(f"   Success rate: {successful}/{len(batch_items)} ({successful/len(batch_items)*100:.1f}%)")
                
                # Show some sample results
                print(f"\n📋 Sample results:")
                for i, result in enumerate(batch_results[:3]):
                    if result.vector:
                        print(f"   Article {result.content_id}: {len(result.vector)} dims, {result.processing_time:.3f}s")
                    else:
                        print(f"   Article {result.content_id}: FAILED - {result.error}")
            
        else:
            print("⚠️  No articles found for batch testing")
        
        # Performance comparison
        print(f"\n🏆 PERFORMANCE COMPARISON")
        print("=" * 50)
        print(f"Old Ollama method:     ~116s per article")
        print(f"New Sentence Transformers: ~{processing_time:.3f}s per article")
        print(f"Speed improvement:     ~{116/processing_time:.0f}x faster!")
        
        # Model info
        print(f"\n📊 MODEL INFORMATION")
        print("=" * 40)
        model_info = vector_service.get_model_info()
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error in fast vectorization test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fast_vectorization()
