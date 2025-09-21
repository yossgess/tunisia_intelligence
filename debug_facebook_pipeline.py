#!/usr/bin/env python3
"""
Debug script for Facebook pipeline issues

This script will help identify why the Facebook pipeline is processing 0 items.
"""

import sys
import logging
from pathlib import Path
from config.database import DatabaseManager
from config.secrets import SecretManager
from facebook_loader import UltraMinimalFacebookLoader
from extractors.facebook_extractor import UltraMinimalFacebookExtractor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_facebook_sources():
    """Debug Facebook sources in database"""
    print("🔍 Debugging Facebook Sources")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Check Facebook sources
        response = db.client.table("sources") \
            .select("*") \
            .eq("source_type", "facebook") \
            .eq("is_active", True) \
            .execute()
        
        facebook_sources = response.data
        print(f"✅ Found {len(facebook_sources)} active Facebook sources")
        
        if facebook_sources:
            print("\nFirst 5 Facebook sources:")
            for i, source in enumerate(facebook_sources[:5]):
                print(f"  {i+1}. {source.get('name', 'Unknown')}")
                print(f"     Page ID: {source.get('page_id', 'Missing')}")
                print(f"     Active: {source.get('is_active', False)}")
                print(f"     URL: {source.get('url', 'N/A')}")
                print()
        
        return facebook_sources
        
    except Exception as e:
        print(f"❌ Error checking Facebook sources: {e}")
        return []

def debug_facebook_token():
    """Debug Facebook token configuration"""
    print("🔍 Debugging Facebook Token")
    print("=" * 50)
    
    try:
        secret_manager = SecretManager(backend="file")
        app_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
        
        if app_token:
            print(f"✅ Facebook token found: {app_token[:20]}...")
            api_version = secret_manager.get_secret("FACEBOOK_API_VERSION", "v18.0")
            print(f"✅ API version: {api_version}")
            return app_token, api_version
        else:
            print("❌ Facebook token not found")
            return None, None
            
    except Exception as e:
        print(f"❌ Error checking Facebook token: {e}")
        return None, None

def test_facebook_api_direct(app_token, api_version, page_id):
    """Test Facebook API directly"""
    print(f"🔍 Testing Facebook API for page: {page_id}")
    print("=" * 50)
    
    try:
        import requests
        
        # Test basic page info
        url = f"https://graph.facebook.com/{api_version}/{page_id}"
        params = {
            'fields': 'id,name',
            'access_token': app_token
        }
        
        print(f"Making API call to: {url}")
        print(f"Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful")
            print(f"Page name: {data.get('name', 'Unknown')}")
            print(f"Page ID: {data.get('id', 'Unknown')}")
            return True
        else:
            print(f"❌ API call failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Facebook API: {e}")
        return False

def debug_facebook_extractor(app_token, api_version, page_ids):
    """Debug Facebook extractor"""
    print("🔍 Debugging Facebook Extractor")
    print("=" * 50)
    
    try:
        extractor = UltraMinimalFacebookExtractor(app_token, api_version)
        
        # Test with first page
        if page_ids:
            test_page_id = page_ids[0]
            print(f"Testing extractor with page: {test_page_id}")
            
            # Test page info
            page_info = extractor.get_ultra_minimal_page_info(test_page_id)
            if page_info:
                print(f"✅ Page info retrieved: {page_info.get('name', 'Unknown')}")
            else:
                print("❌ Failed to retrieve page info")
                return False
            
            # Test posts extraction
            print("Testing posts extraction...")
            results = extractor.extract_posts_ultra_minimal([test_page_id], hours_back=168, max_pages=1)
            
            if results and 'results' in results:
                page_result = results['results'].get(test_page_id, {})
                if 'error' in page_result:
                    print(f"❌ Extraction error: {page_result['error']}")
                    return False
                else:
                    posts = page_result.get('posts', [])
                    print(f"✅ Extracted {len(posts)} posts")
                    return True
            else:
                print("❌ No results from extraction")
                return False
        else:
            print("❌ No page IDs to test")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Facebook extractor: {e}")
        return False

def debug_facebook_loader():
    """Debug Facebook loader"""
    print("🔍 Debugging Facebook Loader")
    print("=" * 50)
    
    try:
        loader = UltraMinimalFacebookLoader()
        
        # Test source loading
        sources = loader.load_facebook_sources_prioritized()
        print(f"Loader found {len(sources)} sources")
        
        if not sources:
            print("❌ No sources loaded by loader")
            return False
        
        # Test extraction
        print("Testing loader extraction...")
        result = loader.extract_and_load_posts_ultra_minimal(hours_back=168)
        
        print(f"Extraction result status: {result.get('status', 'unknown')}")
        print(f"Sources processed: {result.get('sources_processed', 0)}")
        print(f"Posts loaded: {result.get('total_posts_loaded', 0)}")
        print(f"API calls made: {result.get('api_calls_made', 0)}")
        
        if result.get('status') == 'completed' and result.get('total_posts_loaded', 0) > 0:
            print("✅ Loader working correctly")
            return True
        else:
            print("❌ Loader not processing posts")
            if 'message' in result:
                print(f"Message: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Facebook loader: {e}")
        return False

def main():
    """Main debug function"""
    print("🐛 Facebook Pipeline Debug Tool")
    print("=" * 60)
    
    # Step 1: Check Facebook sources
    facebook_sources = debug_facebook_sources()
    if not facebook_sources:
        print("❌ CRITICAL: No Facebook sources found!")
        return False
    
    print()
    
    # Step 2: Check Facebook token
    app_token, api_version = debug_facebook_token()
    if not app_token:
        print("❌ CRITICAL: No Facebook token configured!")
        return False
    
    print()
    
    # Step 3: Test Facebook API directly
    page_ids = [source.get('page_id') for source in facebook_sources[:3] if source.get('page_id')]
    if page_ids:
        api_success = test_facebook_api_direct(app_token, api_version, page_ids[0])
        if not api_success:
            print("❌ CRITICAL: Facebook API not working!")
            return False
    
    print()
    
    # Step 4: Test Facebook extractor
    extractor_success = debug_facebook_extractor(app_token, api_version, page_ids)
    if not extractor_success:
        print("❌ CRITICAL: Facebook extractor not working!")
        return False
    
    print()
    
    # Step 5: Test Facebook loader
    loader_success = debug_facebook_loader()
    if not loader_success:
        print("❌ CRITICAL: Facebook loader not working!")
        return False
    
    print()
    print("=" * 60)
    print("✅ All Facebook pipeline components working correctly!")
    print("The issue may be in the unified pipeline controller integration.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
