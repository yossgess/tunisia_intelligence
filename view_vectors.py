#!/usr/bin/env python3
"""
Simple script to view stored vectors in the database.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager

def view_stored_vectors():
    """View all stored vectors in the database."""
    print("🔍 VIEWING STORED VECTORS")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Your SQL query with proper connection
        query = """
        SELECT 
            content_type,
            content_id,
            vector_dims(content_embedding) as dimensions,
            vector_dims(title_embedding) as title_dimensions,
            vector_dims(entity_embedding) as entity_dimensions,
            language,
            content_hash,
            created_at
        FROM content_embeddings
        ORDER BY created_at DESC
        LIMIT 20;
        """
        
        print("📊 Executing query...")
        result = db.execute_query(query)
        
        if result:
            print(f"✅ Found {len(result)} vectors:")
            print("-" * 80)
            
            for i, row in enumerate(result, 1):
                print(f"{i}. Content Type: {row['content_type']}")
                print(f"   Content ID: {row['content_id']}")
                print(f"   Content Dimensions: {row['dimensions'] or 'None'}")
                print(f"   Title Dimensions: {row['title_dimensions'] or 'None'}")
                print(f"   Entity Dimensions: {row['entity_dimensions'] or 'None'}")
                print(f"   Language: {row['language'] or 'Unknown'}")
                print(f"   Content Hash: {row['content_hash'][:16] if row['content_hash'] else 'None'}...")
                print(f"   Created: {row['created_at']}")
                print("-" * 40)
        else:
            print("❌ No vectors found in the database")
            print("\n💡 This could mean:")
            print("   - No vectorization has been run yet")
            print("   - The content_embeddings table is empty")
            print("   - There might be a connection issue")
        
        # Also check if the table exists
        print("\n🔍 Checking if content_embeddings table exists...")
        table_check = db.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'content_embeddings'
            );
        """)
        
        if table_check and table_check[0]['exists']:
            print("✅ content_embeddings table exists")
            
            # Check total count
            count_result = db.execute_query("SELECT COUNT(*) as total FROM content_embeddings;")
            if count_result:
                print(f"📊 Total records in content_embeddings: {count_result[0]['total']}")
        else:
            print("❌ content_embeddings table does not exist")
            print("💡 You may need to run the database setup first")
        
    except Exception as e:
        print(f"❌ Error viewing vectors: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your .env file has correct database credentials")
        print("2. Ensure you're connected to the internet")
        print("3. Verify your Supabase database is running")
        print("4. Try running: python -c 'from config.database import DatabaseManager; db = DatabaseManager(); print(\"Connection OK\")'")

def check_database_connection():
    """Test database connection."""
    print("\n🔗 TESTING DATABASE CONNECTION")
    print("=" * 40)
    
    try:
        db = DatabaseManager()
        
        # Simple test query
        result = db.execute_query("SELECT 1 as test;")
        if result and result[0]['test'] == 1:
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed - no result")
            return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # First test connection
    if check_database_connection():
        # Then view vectors
        view_stored_vectors()
    else:
        print("\n💡 Fix the database connection first, then try again.")
