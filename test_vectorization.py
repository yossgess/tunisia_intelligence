#!/usr/bin/env python3
"""
Test script for the vectorization system.

This script tests the vector generation, storage, and similarity search functionality.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_enrichment.core.vector_service import VectorService, VectorConfig
from ai_enrichment.core.vector_database import VectorDatabase
from ai_enrichment.services.enrichment_service import EnrichmentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vector_service():
    """Test the vector service functionality."""
    print("="*60)
    print("TESTING VECTOR SERVICE")
    print("="*60)
    
    try:
        # Initialize vector service
        print("🔧 Initializing vector service...")
        vector_service = VectorService()
        
        # Health check
        print("🏥 Checking service health...")
        if not vector_service.health_check():
            print("❌ Vector service health check failed")
            return False
        print("✅ Vector service is healthy")
        
        # Test content samples
        test_content = [
            {
                'id': 'test1',
                'type': 'article',
                'content': 'الرئيس التونسي قيس سعيد يعلن عن إجراءات جديدة لمكافحة الفساد في البلاد'
            },
            {
                'id': 'test2', 
                'type': 'article',
                'content': 'Le président tunisien annonce de nouvelles mesures contre la corruption'
            },
            {
                'id': 'test3',
                'type': 'social_post',
                'content': 'التونسيون يطالبون بالإصلاحات الاقتصادية العاجلة'
            }
        ]
        
        # Test single vector generation
        print("\n📝 Testing single vector generation...")
        result = vector_service.generate_vector(
            content=test_content[0]['content'],
            content_id=test_content[0]['id'],
            content_type=test_content[0]['type']
        )
        
        if result.vector:
            print(f"✅ Vector generated successfully")
            print(f"   Dimensions: {len(result.vector)}")
            print(f"   Language: {result.language}")
            print(f"   Processing time: {result.processing_time:.2f}s")
            print(f"   Chunks processed: {result.chunks_processed}")
        else:
            print(f"❌ Vector generation failed: {result.error}")
            return False
        
        # Test batch vector generation
        print("\n📦 Testing batch vector generation...")
        batch_results = vector_service.batch_generate_vectors(test_content)
        
        successful = sum(1 for r in batch_results if r.vector is not None)
        print(f"✅ Batch processing completed: {successful}/{len(test_content)} successful")
        
        for i, result in enumerate(batch_results):
            if result.vector:
                print(f"   Item {i+1}: ✅ {len(result.vector)} dimensions, {result.language}")
            else:
                print(f"   Item {i+1}: ❌ {result.error}")
        
        # Test cache functionality
        print("\n💾 Testing cache functionality...")
        cache_stats = vector_service.get_cache_stats()
        print(f"   Cache enabled: {cache_stats.get('cache_enabled', False)}")
        print(f"   Cached items: {cache_stats.get('cached_items', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector service test failed: {e}")
        logger.error(f"Vector service test error: {e}", exc_info=True)
        return False

def test_vector_database():
    """Test the vector database functionality."""
    print("\n" + "="*60)
    print("TESTING VECTOR DATABASE")
    print("="*60)
    
    try:
        # Initialize vector database
        print("🔧 Initializing vector database...")
        vector_db = VectorDatabase()
        
        # Health check
        print("🏥 Checking database health...")
        health = vector_db.health_check()
        print(f"   Status: {health['status']}")
        print(f"   pgvector enabled: {health.get('pgvector_enabled', False)}")
        print(f"   Indexes exist: {health.get('indexes_exist', False)}")
        print(f"   Total vectors: {health.get('total_vectors', 0)}")
        
        if health['status'] != 'healthy':
            print("⚠️  Database not healthy, attempting setup...")
            if vector_db.setup_vector_extensions():
                print("✅ Database setup completed")
            else:
                print("❌ Database setup failed")
                return False
        
        # Get vector statistics
        print("\n📊 Getting vector statistics...")
        stats = vector_db.get_vector_stats()
        print(f"   Total vectors: {stats.total_vectors}")
        print(f"   Average dimensions: {stats.avg_dimensions:.0f}")
        print(f"   Storage size: {stats.storage_size_mb:.2f} MB")
        print(f"   By content type: {stats.by_content_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        logger.error(f"Vector database test error: {e}", exc_info=True)
        return False

def test_enrichment_service():
    """Test the enrichment service with vectorization."""
    print("\n" + "="*60)
    print("TESTING ENRICHMENT SERVICE WITH VECTORIZATION")
    print("="*60)
    
    try:
        # Initialize enrichment service
        print("🔧 Initializing enrichment service...")
        enrichment_service = EnrichmentService()
        
        # Check service status
        print("🏥 Checking service status...")
        status = enrichment_service.get_service_status()
        print(f"   Ollama available: {status.get('ollama_available', False)}")
        print(f"   Vector service: {status.get('processors', {}).get('vector_service', False)}")
        
        # Test content enrichment with vectorization
        print("\n🔍 Testing content enrichment with vectorization...")
        test_content = "الحكومة التونسية تعلن عن خطة جديدة للتنمية الاقتصادية والاجتماعية"
        
        result = enrichment_service.enrich_content(
            content=test_content,
            content_type="article",
            options={
                'enable_sentiment': True,
                'enable_entities': True,
                'enable_keywords': True,
                'enable_categories': True,
                'enable_vectorization': True
            }
        )
        
        print(f"   Status: {result.status.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Language detected: {result.language_detected}")
        
        if hasattr(result, 'vector_data') and result.vector_data:
            print(f"   Vector generated: ✅ {len(result.vector_data.get('vector', []))} dimensions")
            print(f"   Vector language: {result.vector_data.get('language')}")
        else:
            print("   Vector generated: ❌ No vector data")
        
        if result.sentiment:
            print(f"   Sentiment: {result.sentiment.sentiment.value} ({result.sentiment.sentiment_score:.2f})")
        
        if result.entities:
            print(f"   Entities found: {len(result.entities)}")
            for entity in result.entities[:3]:  # Show first 3
                print(f"     - {entity.text} ({entity.type})")
        
        if result.keywords:
            print(f"   Keywords found: {len(result.keywords)}")
            for keyword in result.keywords[:5]:  # Show first 5
                print(f"     - {keyword.text} ({keyword.importance:.2f})")
        
        if result.category:
            print(f"   Category: {result.category.primary_category}")
        
        # Test similarity search
        print("\n🔎 Testing similarity search...")
        similar_content = enrichment_service.find_similar_content(
            content="الاقتصاد التونسي والتنمية المستدامة",
            limit=3,
            similarity_threshold=0.5
        )
        
        print(f"   Similar content found: {len(similar_content)} items")
        for i, item in enumerate(similar_content, 1):
            print(f"     {i}. {item['content_type']} {item['content_id']} (similarity: {item['similarity_score']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Enrichment service test failed: {e}")
        logger.error(f"Enrichment service test error: {e}", exc_info=True)
        return False

def main():
    """Main test function."""
    print("🧪 TUNISIA INTELLIGENCE - VECTORIZATION SYSTEM TEST")
    print(f"Started at: {datetime.now()}")
    print()
    
    test_results = []
    
    # Test vector service
    test_results.append(("Vector Service", test_vector_service()))
    
    # Test vector database
    test_results.append(("Vector Database", test_vector_database()))
    
    # Test enrichment service
    test_results.append(("Enrichment Service", test_enrichment_service()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vectorization system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the logs.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
