#!/usr/bin/env python3
"""
Test vector generation and storage specifically.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager
from ai_enrichment.core.vector_service import VectorService
from ai_enrichment.core.vector_database import VectorDatabase

def test_vector_storage():
    """Test vector generation and storage."""
    print("🧪 TESTING VECTOR GENERATION AND STORAGE")
    print("=" * 60)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        db = DatabaseManager()
        vector_service = VectorService()
        vector_db = VectorDatabase()
        
        # Test content
        test_content = """
        تونس - أعلنت وزارة الداخلية التونسية اليوم عن إجراءات جديدة لتعزيز الأمن في العاصمة.
        وقال الوزير في بيان صحفي أن هذه الإجراءات تهدف إلى ضمان سلامة المواطنين.
        """
        
        print("📝 Testing vector generation...")
        
        # Generate vector
        vector_result = vector_service.generate_vector(
            content=test_content,
            content_type="article",
            content_id=999  # Test ID
        )
        
        if vector_result and vector_result.vector:
            print(f"✅ Vector generated successfully")
            print(f"   Dimensions: {len(vector_result.vector)}")
            print(f"   Language: {vector_result.language or 'unknown'}")
            print(f"   Processing time: {vector_result.processing_time:.2f}s")
            print(f"   Chunks processed: {vector_result.chunks_processed}")
            
            # Store vector in database
            print("💾 Testing vector storage...")
            
            # Create embedding record
            embedding_data = {
                'content_type': 'article',
                'content_id': 999,  # Test ID
                'content_embedding': vector_result.vector,
                'embedding_model': 'qwen2.5:7b',
                'embedding_version': '1.0',
                'content_length': len(test_content),
                'embedding_quality_score': 0.8,
                'language': vector_result.language or 'ar',
                'content_hash': vector_result.content_hash or 'test_hash_123'
            }
            
            # Check if test record already exists and clean it up first
            existing = db.client.table("content_embeddings").select("id").eq("content_id", 999).execute()
            if existing.data:
                print("🧹 Cleaning up existing test record...")
                db.client.table("content_embeddings").delete().eq("content_id", 999).execute()
            
            # Insert into content_embeddings table
            result = db.client.table("content_embeddings").insert(embedding_data).execute()
            
            if result.data:
                print("✅ Vector stored successfully!")
                print(f"   Record ID: {result.data[0]['id']}")
                
                # Verify storage
                print("🔍 Verifying storage...")
                check_result = db.client.table("content_embeddings").select("*").eq("content_id", 999).execute()
                
                if check_result.data:
                    stored_record = check_result.data[0]
                    print(f"✅ Vector verified in database")
                    print(f"   Content Type: {stored_record['content_type']}")
                    print(f"   Content ID: {stored_record['content_id']}")
                    print(f"   Model: {stored_record['embedding_model']}")
                    print(f"   Language: {stored_record.get('language', 'N/A')}")
                    print(f"   Quality Score: {stored_record.get('embedding_quality_score', 'N/A')}")
                    
                    # Test similarity search
                    print("🔎 Testing similarity search...")
                    similar_results = vector_db.find_similar_content(
                        content_id="999",
                        content_type='article',
                        limit=5
                    )
                    
                    print(f"✅ Similarity search returned {len(similar_results)} results")
                    
                    # Clean up test record
                    print("🧹 Cleaning up test record...")
                    db.client.table("content_embeddings").delete().eq("content_id", 999).execute()
                    print("✅ Test record cleaned up")
                    
                else:
                    print("❌ Vector not found in database after storage")
            else:
                print("❌ Failed to store vector in database")
        else:
            print("❌ Failed to generate vector")
            
    except Exception as e:
        print(f"❌ Error in vector storage test: {e}")
        import traceback
        traceback.print_exc()

def test_real_article_vectorization():
    """Test vectorization of real articles from database."""
    print("\n🔍 TESTING REAL ARTICLE VECTORIZATION")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        vector_service = VectorService()
        
        # Get a few real articles
        print("📊 Fetching real articles...")
        articles_result = db.client.table("articles").select("id", "title", "content").limit(3).execute()
        
        if articles_result.data:
            print(f"✅ Found {len(articles_result.data)} articles to test")
            
            for i, article in enumerate(articles_result.data, 1):
                print(f"\n📝 Testing article {i}: ID {article['id']}")
                print(f"   Title: {article['title'][:50]}...")
                
                # Generate vector for this article
                content_to_vectorize = f"{article['title']}\n\n{article.get('content', '')}"
                
                vector_result = vector_service.generate_vector(
                    content=content_to_vectorize,
                    content_type="article",
                    content_id=article['id']
                )
                
                if vector_result and vector_result.vector:
                    print(f"   ✅ Vector generated: {len(vector_result.vector)} dimensions")
                    print(f"   Language: {vector_result.language or 'unknown'}")
                    print(f"   Processing time: {vector_result.processing_time:.2f}s")
                    
                    # Store in content_embeddings
                    embedding_data = {
                        'content_type': 'article',
                        'content_id': article['id'],
                        'content_embedding': vector_result.vector,
                        'embedding_model': 'qwen2.5:7b',
                        'embedding_version': '1.0',
                        'content_length': len(content_to_vectorize),
                        'embedding_quality_score': 0.8,
                        'language': vector_result.language or 'ar',
                        'content_hash': vector_result.content_hash
                    }
                    
                    # Check if already exists
                    existing = db.client.table("content_embeddings").select("id").eq("content_type", "article").eq("content_id", article['id']).execute()
                    
                    if existing.data:
                        # Update existing
                        result = db.client.table("content_embeddings").update(embedding_data).eq("content_type", "article").eq("content_id", article['id']).execute()
                        print(f"   ✅ Vector updated in database")
                    else:
                        # Insert new
                        result = db.client.table("content_embeddings").insert(embedding_data).execute()
                        print(f"   ✅ Vector stored in database")
                else:
                    print(f"   ❌ Failed to generate vector")
        else:
            print("❌ No articles found in database")
            
    except Exception as e:
        print(f"❌ Error in real article vectorization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test vector storage
    test_vector_storage()
    
    # Test real article vectorization
    test_real_article_vectorization()
    
    # Check final status
    print("\n📊 FINAL VECTOR COUNT CHECK")
    print("=" * 40)
    try:
        db = DatabaseManager()
        count_result = db.client.table("content_embeddings").select("content_type", count="exact").execute()
        print(f"Total vectors in database: {count_result.count}")
        
        if count_result.count > 0:
            # Show sample
            sample_result = db.client.table("content_embeddings").select("content_type", "content_id", "embedding_model", "created_at").limit(5).execute()
            print("\nSample vectors:")
            for row in sample_result.data:
                print(f"  - {row['content_type']} {row['content_id']}: {row['embedding_model']} ({row['created_at']})")
    except Exception as e:
        print(f"Error checking final count: {e}")
