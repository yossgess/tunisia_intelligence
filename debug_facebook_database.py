#!/usr/bin/env python3
"""
Debug script for Facebook database integration issues

This script will help identify why Facebook posts aren't being stored in the database.
"""

import sys
import logging
from datetime import datetime, timedelta
from config.database import DatabaseManager
from facebook_loader import UltraMinimalFacebookLoader

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_schema():
    """Check if social_media_posts table exists and has correct structure"""
    print("🔍 Checking Database Schema")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Check if table exists by trying to query it
        response = db.client.table("social_media_posts").select("*").limit(1).execute()
        print(f"✅ social_media_posts table exists")
        
        # Check existing posts count
        count_response = db.client.table("social_media_posts").select("id", count="exact").execute()
        existing_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
        print(f"📊 Existing posts in database: {existing_count}")
        
        # Show recent posts if any
        if existing_count > 0:
            recent_response = db.client.table("social_media_posts") \
                .select("id,account,content,publish_date,url,created_at") \
                .order("created_at", desc=True) \
                .limit(5) \
                .execute()
            
            print(f"\n📋 Recent posts (last 5):")
            for post in recent_response.data:
                print(f"  - ID: {post.get('id')}, Account: {post.get('account', 'Unknown')}")
                print(f"    Content: {post.get('content', 'No content')[:50]}...")
                print(f"    Date: {post.get('publish_date', 'No date')}")
                print(f"    URL: {post.get('url', 'No URL')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

def test_manual_post_insertion():
    """Test manual insertion of a Facebook post"""
    print("🔍 Testing Manual Post Insertion")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Create test post data
        test_post = {
            "source_id": 1,  # Use a valid source ID
            "social_media": "facebook",
            "account": "Test Account",
            "content": f"Test post created at {datetime.now().isoformat()}",
            "publish_date": datetime.now().isoformat(),
            "url": f"https://facebook.com/test/{int(datetime.now().timestamp())}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"Inserting test post: {test_post}")
        
        # Try to insert
        response = db.client.table("social_media_posts").insert(test_post).execute()
        
        if response.data:
            print(f"✅ Test post inserted successfully: ID {response.data[0].get('id')}")
            
            # Clean up - delete the test post
            db.client.table("social_media_posts").delete().eq("id", response.data[0].get('id')).execute()
            print(f"✅ Test post cleaned up")
            return True
        else:
            print(f"❌ Test post insertion failed: no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error testing manual insertion: {e}")
        return False

def debug_facebook_extraction_with_database():
    """Debug Facebook extraction and database operations"""
    print("🔍 Debugging Facebook Extraction with Database Operations")
    print("=" * 50)
    
    try:
        loader = UltraMinimalFacebookLoader()
        
        # Get a small number of sources for testing
        sources = loader.load_facebook_sources_prioritized()[:3]  # Only test 3 sources
        print(f"Testing with {len(sources)} sources")
        
        # Count posts before
        db = DatabaseManager()
        before_response = db.client.table("social_media_posts").select("id", count="exact").execute()
        posts_before = before_response.count if hasattr(before_response, 'count') else len(before_response.data)
        print(f"Posts in database before: {posts_before}")
        
        # Run extraction with extended time window
        print(f"Running extraction with hours_back=2000...")
        result = loader.extract_and_load_posts_ultra_minimal(hours_back=2000)
        
        # Count posts after
        after_response = db.client.table("social_media_posts").select("id", count="exact").execute()
        posts_after = after_response.count if hasattr(after_response, 'count') else len(after_response.data)
        print(f"Posts in database after: {posts_after}")
        
        # Show results
        print(f"\n📊 Extraction Results:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Sources processed: {result.get('sources_processed', 0)}")
        print(f"Posts loaded (reported): {result.get('total_posts_loaded', 0)}")
        print(f"Posts in database (actual): {posts_after - posts_before}")
        print(f"API calls made: {result.get('api_calls_made', 0)}")
        
        # Check if there's a discrepancy
        reported_posts = result.get('total_posts_loaded', 0)
        actual_posts = posts_after - posts_before
        
        if reported_posts != actual_posts:
            print(f"\n⚠️  DISCREPANCY DETECTED!")
            print(f"Reported posts loaded: {reported_posts}")
            print(f"Actual posts in database: {actual_posts}")
            print(f"Difference: {reported_posts - actual_posts}")
            
            if actual_posts == 0 and reported_posts > 0:
                print(f"\n🔍 Posts were processed but not stored in database!")
                print(f"This indicates a database insertion issue.")
                return False
            elif actual_posts > 0 and reported_posts == 0:
                print(f"\n🔍 Posts were stored but not reported correctly!")
                print(f"This indicates a metrics reporting issue.")
                return True
        else:
            print(f"\n✅ Reported and actual posts match!")
            return True
            
    except Exception as e:
        print(f"❌ Error in Facebook extraction debug: {e}")
        return False

def check_parsing_state():
    """Check parsing state for Facebook sources"""
    print("🔍 Checking Parsing State")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Check parsing states for Facebook sources
        response = db.client.table("parsing_state") \
            .select("*") \
            .execute()
        
        facebook_states = []
        for state in response.data:
            # Get source info
            source_response = db.client.table("sources") \
                .select("name,source_type") \
                .eq("id", state.get("source_id")) \
                .execute()
            
            if source_response.data and source_response.data[0].get("source_type") == "facebook":
                facebook_states.append({
                    "source_name": source_response.data[0].get("name"),
                    "last_processed_id": state.get("last_processed_id"),
                    "last_processed_date": state.get("last_processed_date"),
                    "last_content_hash": state.get("last_content_hash")
                })
        
        print(f"Found {len(facebook_states)} Facebook parsing states")
        
        if facebook_states:
            print("\nFacebook parsing states:")
            for state in facebook_states[:5]:  # Show first 5
                print(f"  - {state['source_name']}")
                print(f"    Last ID: {state['last_processed_id']}")
                print(f"    Last Date: {state['last_processed_date']}")
                print(f"    Last Hash: {state['last_content_hash'][:20] if state['last_content_hash'] else 'None'}...")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking parsing state: {e}")
        return False

def main():
    """Main debug function"""
    print("🐛 Facebook Database Integration Debug Tool")
    print("=" * 60)
    
    # Step 1: Check database schema
    if not check_database_schema():
        print("❌ CRITICAL: Database schema issues detected!")
        return False
    
    print()
    
    # Step 2: Test manual insertion
    if not test_manual_post_insertion():
        print("❌ CRITICAL: Manual database insertion failed!")
        return False
    
    print()
    
    # Step 3: Check parsing state
    check_parsing_state()
    
    print()
    
    # Step 4: Debug extraction with database
    extraction_success = debug_facebook_extraction_with_database()
    
    print("\n" + "=" * 60)
    if extraction_success:
        print("✅ Facebook database integration appears to be working!")
        print("If you're still not seeing posts, it may be due to:")
        print("  - All posts being duplicates (already in database)")
        print("  - Rate limiting preventing post extraction")
        print("  - Posts not meeting content criteria")
    else:
        print("❌ Facebook database integration has issues!")
        print("Check the detailed output above for specific problems.")
    
    return extraction_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
