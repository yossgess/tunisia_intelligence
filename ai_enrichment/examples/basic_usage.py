"""
Basic usage examples for AI Enrichment module.

This module demonstrates how to use the AI enrichment components
for various content analysis tasks.
"""

import asyncio
from datetime import datetime
from ai_enrichment import EnrichmentService, OllamaClient, OllamaConfig
from ai_enrichment.models.enrichment_models import EnrichmentRequest

def basic_enrichment_example():
    """Basic example of enriching text content."""
    print("🚀 Basic AI Enrichment Example")
    print("=" * 40)
    
    # Initialize the enrichment service
    service = EnrichmentService()
    
    # Test content in Arabic and French
    test_contents = [
        "الحكومة التونسية تعلن عن إجراءات جديدة لتحسين الاقتصاد",
        "Le gouvernement tunisien annonce de nouvelles mesures économiques",
        "Tunisia's government announces new economic measures to boost growth"
    ]
    
    for i, content in enumerate(test_contents, 1):
        print(f"\n📝 Example {i}: {content[:50]}...")
        
        # Enrich the content
        result = service.enrich_content(
            content=content,
            content_type="article"
        )
        
        # Display results
        print(f"   Status: {result.status.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        
        if result.sentiment:
            print(f"   Sentiment: {result.sentiment.sentiment.value}")
        
        if result.entities:
            entities = [e.text for e in result.entities[:3]]
            print(f"   Entities: {', '.join(entities)}")
        
        if result.keywords:
            keywords = [k.text for k in result.keywords[:5]]
            print(f"   Keywords: {', '.join(keywords)}")
        
        if result.category:
            print(f"   Category: {result.category.primary_category}")

def batch_processing_example():
    """Example of batch processing multiple articles."""
    print("\n🔄 Batch Processing Example")
    print("=" * 35)
    
    from ai_enrichment.services.batch_processor import BatchProcessor
    
    # Initialize batch processor
    batch_processor = BatchProcessor()
    
    # Get processing statistics
    stats = batch_processor.get_processing_statistics(
        content_type="article",
        days_back=7
    )
    
    print(f"📊 Current Statistics:")
    print(f"   Total Articles: {stats.get('total_items', 0):,}")
    print(f"   Enriched: {stats.get('enriched_items', 0):,}")
    print(f"   Pending: {stats.get('pending_items', 0):,}")
    print(f"   Enrichment Rate: {stats.get('enrichment_rate', 0):.1f}%")
    
    # Example batch processing (commented out to avoid actual processing)
    """
    print("\n🔄 Running batch processing...")
    result = batch_processor.process_articles(limit=10)
    
    print(f"✅ Processed: {result.successful_items}/{result.total_items}")
    print(f"📈 Success Rate: {result.success_rate:.1%}")
    """

def custom_processor_example():
    """Example of using individual processors."""
    print("\n🤖 Individual Processors Example")
    print("=" * 40)
    
    from ai_enrichment.processors import (
        SentimentAnalyzer, EntityExtractor, 
        KeywordExtractor, CategoryClassifier
    )
    
    # Initialize processors
    sentiment_analyzer = SentimentAnalyzer()
    entity_extractor = EntityExtractor()
    keyword_extractor = KeywordExtractor()
    category_classifier = CategoryClassifier()
    
    test_text = "وزير الاقتصاد التونسي يعلن عن خطة جديدة لتطوير الاستثمار في البلاد"
    
    print(f"📝 Analyzing: {test_text}")
    
    # Sentiment analysis
    sentiment_result = sentiment_analyzer.process(test_text)
    if sentiment_result.status.value == 'success':
        sentiment_data = sentiment_result.data
        print(f"😊 Sentiment: {sentiment_data['sentiment']} ({sentiment_result.confidence:.2f})")
    
    # Entity extraction
    entity_result = entity_extractor.process(test_text)
    if entity_result.status.value == 'success':
        entities = entity_result.data.get('entities', [])
        print(f"👥 Entities: {len(entities)} found")
        for entity in entities[:3]:
            print(f"   • {entity['text']} ({entity['type']})")
    
    # Keyword extraction
    keyword_result = keyword_extractor.process(test_text)
    if keyword_result.status.value == 'success':
        keywords = keyword_result.data.get('keywords', [])
        print(f"🔑 Keywords: {len(keywords)} found")
        for keyword in keywords[:5]:
            print(f"   • {keyword['text']} ({keyword['importance']:.2f})")
    
    # Category classification
    category_result = category_classifier.process(test_text)
    if category_result.status.value == 'success':
        category_data = category_result.data
        print(f"📂 Category: {category_data['primary_category']} ({category_result.confidence:.2f})")

def integration_with_database_example():
    """Example of integrating with existing database."""
    print("\n💾 Database Integration Example")
    print("=" * 40)
    
    from config.database import DatabaseManager
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Get recent articles that need enrichment
    try:
        response = db_manager.client.table("news_articles") \
            .select("id, title, content") \
            .is_("sentiment", "null") \
            .limit(5) \
            .execute()
        
        articles = response.data or []
        print(f"📰 Found {len(articles)} articles needing enrichment")
        
        # Initialize enrichment service
        service = EnrichmentService(db_manager=db_manager)
        
        for article in articles:
            content = article.get('content') or article.get('title', '')
            if content:
                print(f"\n🔄 Processing article {article['id']}: {content[:50]}...")
                
                # Enrich with database integration
                result = service.enrich_content(
                    content=content,
                    content_type="article",
                    content_id=article['id']
                )
                
                print(f"   Result: {result.status.value} (confidence: {result.confidence:.2f})")
                
                # The enrichment service automatically saves to database
                # when content_id is provided and save_to_database is True
        
    except Exception as e:
        print(f"❌ Database integration example failed: {e}")
        print("   Make sure your database is configured and accessible")

def multilingual_example():
    """Example demonstrating multilingual capabilities."""
    print("\n🌍 Multilingual Processing Example")
    print("=" * 40)
    
    service = EnrichmentService()
    
    # Test content in different languages
    multilingual_content = {
        "Arabic": "الرئيس التونسي يلتقي بوفد من رجال الأعمال لمناقشة الاستثمارات الجديدة",
        "French": "Le président tunisien rencontre une délégation d'hommes d'affaires pour discuter de nouveaux investissements",
        "English": "The Tunisian president meets with a business delegation to discuss new investments",
        "Mixed": "Le président تونس يناقش economic policies مع business leaders"
    }
    
    for language, content in multilingual_content.items():
        print(f"\n🗣️  {language}: {content}")
        
        result = service.enrich_content(content=content, content_type="article")
        
        if result.status.value == 'success':
            detected_lang = result.language_detected
            print(f"   Detected Language: {detected_lang}")
            
            if result.sentiment:
                print(f"   Sentiment: {result.sentiment.sentiment.value}")
            
            if result.entities:
                entities = [e.text for e in result.entities[:2]]
                print(f"   Key Entities: {', '.join(entities)}")

def performance_monitoring_example():
    """Example of monitoring performance and statistics."""
    print("\n📊 Performance Monitoring Example")
    print("=" * 40)
    
    service = EnrichmentService()
    
    # Test service status
    status = service.get_service_status()
    
    print("🔍 Service Status:")
    print(f"   Ollama Available: {'✅' if status['ollama_available'] else '❌'}")
    print(f"   Model: {status['ollama_model']}")
    print(f"   Database Connected: {'✅' if status['database_connected'] else '❌'}")
    
    # Test processors
    print("\n🧪 Testing Processors:")
    test_results = service.test_processors("هذا نص تجريبي للاختبار")
    
    for processor, result in test_results.items():
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_emoji} {processor}: {result['status']}")
        if 'processing_time' in result:
            print(f"      Time: {result['processing_time']:.2f}s")

def main():
    """Run all examples."""
    print("🎯 AI Enrichment Module Examples")
    print("=" * 50)
    
    try:
        # Run examples
        basic_enrichment_example()
        batch_processing_example()
        custom_processor_example()
        integration_with_database_example()
        multilingual_example()
        performance_monitoring_example()
        
        print("\n✅ All examples completed successfully!")
        print("\n📚 Next Steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull model: ollama pull qwen2.5:7b")
        print("   4. Run CLI: python ai_enrich.py test")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("   Make sure Ollama is running and qwen2.5:7b model is available")

if __name__ == "__main__":
    main()
