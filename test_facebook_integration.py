"""
Test script for Facebook integration

Tests the Facebook extractor and loader functionality with a sample page.
"""

import logging
import sys
import os
from datetime import datetime
from config.secrets import get_secret
from extractors.facebook_extractor import FacebookExtractor, extract_facebook_page_posts
from facebook_loader import FacebookLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_facebook_extractor():
    """Test the Facebook extractor with a sample page"""
    try:
        print("🧪 Testing Facebook Extractor...")
        
        # Set backend to file for persistent storage
        os.environ["SECRETS_BACKEND"] = "file"
        
        # Import and use SecretManager directly to ensure file backend
        from config.secrets import SecretManager
        secret_manager = SecretManager(backend="file")
        
        # Get app token
        app_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
        if not app_token:
            print("❌ Facebook app token not found. Run setup_facebook_token.py first.")
            print("🔍 Debugging: Checking available secrets...")
            secrets = secret_manager.list_secrets()
            print(f"Available secrets: {secrets}")
            return False
        
        print("✅ Facebook app token found")
        
        # Test with a sample page (using one from your sources)
        # Let's use the Présidence de la République page
        test_page_id = "271178572940207"  # Présidence de la République
        
        print(f"📱 Testing extraction from page ID: {test_page_id}")
        
        # Extract posts
        result = extract_facebook_page_posts(test_page_id, app_token, hours_back=24)
        
        if "error" in result:
            print(f"❌ Extraction failed: {result['error']}")
            return False
        
        print("✅ Extraction successful!")
        print(f"📊 Page: {result.get('page_info', {}).get('name', 'Unknown')}")
        print(f"📝 Posts found: {result.get('total_posts', 0)}")
        
        # Show sample post data
        posts = result.get('posts', [])
        if posts:
            sample_post = posts[0]
            print(f"\n📄 Sample post:")
            print(f"   ID: {sample_post.get('id')}")
            print(f"   Message: {sample_post.get('message', 'No message')[:100]}...")
            print(f"   Reactions: {sample_post.get('total_reactions', 0)}")
            print(f"   Comments: {sample_post.get('total_comments', 0)}")
            print(f"   Shares: {sample_post.get('shares_count', 0)}")
            
            # Show reactions breakdown
            reactions = sample_post.get('reactions_breakdown', {})
            if reactions:
                print(f"   Reactions breakdown: {reactions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extractor: {e}")
        logger.error(f"Extractor test error: {e}", exc_info=True)
        return False


def test_facebook_loader():
    """Test the Facebook loader"""
    try:
        print("\n🧪 Testing Facebook Loader...")
        
        # Set backend to file for persistent storage
        os.environ["SECRETS_BACKEND"] = "file"
        
        # Initialize loader
        loader = FacebookLoader()
        print("✅ Facebook loader initialized")
        
        # Check Facebook sources
        sources = loader.load_facebook_sources()
        print(f"📊 Found {len(sources)} Facebook sources in database")
        
        if not sources:
            print("⚠️  No Facebook sources found. The loader needs Facebook sources in the database.")
            return False
        
        # Show sample sources
        for i, source in enumerate(sources[:3]):  # Show first 3
            print(f"   {i+1}. {source.get('name')} (Page ID: {source.get('page_id')})")
        
        # Test extraction and loading (with a short time window for testing)
        print("\n📥 Testing extraction and loading...")
        result = loader.extract_and_load_posts(hours_back=24)
        
        print(f"✅ Loading completed!")
        print(f"📊 Status: {result.get('status')}")
        print(f"📝 Posts loaded: {result.get('total_posts_loaded', 0)}")
        print(f"👍 Reactions loaded: {result.get('total_reactions_loaded', 0)}")
        print(f"💬 Comments loaded: {result.get('total_comments_loaded', 0)}")
        
        if result.get('errors'):
            print(f"⚠️  Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"   - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing loader: {e}")
        logger.error(f"Loader test error: {e}", exc_info=True)
        return False


def test_database_tables():
    """Test if the required database tables exist"""
    try:
        print("\n🧪 Testing Database Tables...")
        
        from config.database import DatabaseManager
        db_manager = DatabaseManager()
        client = db_manager.client
        
        # Test social_media_posts table
        try:
            response = client.table("social_media_posts").select("id").limit(1).execute()
            print("✅ social_media_posts table accessible")
        except Exception as e:
            print(f"❌ social_media_posts table error: {e}")
            return False
        
        # Test social_media_post_reactions table
        try:
            response = client.table("social_media_post_reactions").select("post_id").limit(1).execute()
            print("✅ social_media_post_reactions table accessible")
        except Exception as e:
            print(f"❌ social_media_post_reactions table error: {e}")
            return False
        
        # Test social_media_comments table
        try:
            response = client.table("social_media_comments").select("id").limit(1).execute()
            print("✅ social_media_comments table accessible")
        except Exception as e:
            print(f"❌ social_media_comments table error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database tables: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Facebook Integration Test Suite")
    print("=" * 50)
    
    # Test database tables first
    db_test = test_database_tables()
    
    # Test extractor
    extractor_test = test_facebook_extractor()
    
    # Test loader (only if database and extractor tests pass)
    loader_test = False
    if db_test and extractor_test:
        loader_test = test_facebook_loader()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"   Database Tables: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"   Facebook Extractor: {'✅ PASS' if extractor_test else '❌ FAIL'}")
    print(f"   Facebook Loader: {'✅ PASS' if loader_test else '❌ FAIL'}")
    
    if all([db_test, extractor_test, loader_test]):
        print("\n🎉 All tests passed! Facebook integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return all([db_test, extractor_test, loader_test])


if __name__ == "__main__":
    main()
