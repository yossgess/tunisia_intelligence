#!/usr/bin/env python3
"""
Fix content_embeddings table schema and view stored vectors.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager

def fix_content_embeddings_schema():
    """Check content_embeddings table schema."""
    print("🔧 CHECKING CONTENT_EMBEDDINGS TABLE SCHEMA")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        print("📝 Checking table structure...")
        
        # Check if we can access the table and see what columns exist
        result = db.client.table("content_embeddings").select("*").limit(1).execute()
        
        if result.data:
            print("✅ content_embeddings table exists and is accessible")
            sample_row = result.data[0]
            print("📊 Available columns:")
            for column in sample_row.keys():
                print(f"   - {column}")
            
            # Check if missing columns exist
            missing_columns = []
            if 'language' not in sample_row:
                missing_columns.append('language')
            if 'content_hash' not in sample_row:
                missing_columns.append('content_hash')
            
            if missing_columns:
                print(f"\n⚠️  Missing columns: {', '.join(missing_columns)}")
                print("💡 To add missing columns, run these SQL commands in your Supabase dashboard:")
                print("   ALTER TABLE content_embeddings ADD COLUMN IF NOT EXISTS language character varying;")
                print("   ALTER TABLE content_embeddings ADD COLUMN IF NOT EXISTS content_hash character varying;")
            else:
                print("✅ All expected columns are present")
        else:
            print("⚠️  content_embeddings table is empty")
        
        print("✅ Schema check completed")
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

def view_stored_vectors():
    """View all stored vectors with corrected query."""
    print("\n🔍 VIEWING STORED VECTORS")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        print("📊 Fetching vectors from content_embeddings table...")
        result = db.client.table("content_embeddings").select("*").order("created_at", desc=True).limit(20).execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} vectors:")
            print("-" * 100)
            
            for i, row in enumerate(result.data, 1):
                print(f"{i}. Content Type: {row.get('content_type', 'Unknown')}")
                print(f"   Content ID: {row.get('content_id', 'Unknown')}")
                print(f"   Model: {row.get('embedding_model', 'Unknown')}")
                print(f"   Version: {row.get('embedding_version', 'Unknown')}")
                print(f"   Content Length: {row.get('content_length', 'Unknown')}")
                print(f"   Quality Score: {row.get('embedding_quality_score', 'Unknown')}")
                print(f"   Language: {row.get('language', 'Unknown')}")
                if row.get('content_hash'):
                    print(f"   Content Hash: {row['content_hash'][:16]}...")
                else:
                    print(f"   Content Hash: None")
                print(f"   Created: {row.get('created_at', 'Unknown')}")
                print(f"   Updated: {row.get('updated_at', 'Unknown')}")
                
                # Check if embeddings exist
                has_content = row.get('content_embedding') is not None
                has_title = row.get('title_embedding') is not None
                has_entity = row.get('entity_embedding') is not None
                print(f"   Embeddings: Content={has_content}, Title={has_title}, Entity={has_entity}")
                print("-" * 50)
        else:
            print("❌ No vectors found in the database")
            print("\n💡 This means:")
            print("   - No vectorization has been run yet")
            print("   - You need to run the batch vectorization process")
            print("   - Try running: python batch_vectorize.py")
        
        # Get summary statistics using simple count
        print("\n📈 VECTOR SUMMARY STATISTICS:")
        print("-" * 40)
        
        # Get total count
        count_result = db.client.table("content_embeddings").select("content_type", count="exact").execute()
        print(f"Total records in content_embeddings: {count_result.count}")
        
        # Get count by content type
        if result.data:
            content_types = {}
            for row in result.data:
                ct = row.get('content_type', 'unknown')
                content_types[ct] = content_types.get(ct, 0) + 1
            
            print("\nBy content type (from sample):")
            for ct, count in content_types.items():
                print(f"  {ct}: {count}")
        
    except Exception as e:
        print(f"❌ Error viewing vectors: {e}")
        import traceback
        traceback.print_exc()

def check_vector_indexes():
    """Check if vector indexes exist."""
    print("\n🔍 CHECKING VECTOR INDEXES")
    print("=" * 40)
    
    try:
        db = DatabaseManager()
        
        print("💡 Vector indexes need to be checked via SQL functions.")
        print("   You can use the check_vector_indexes() SQL function")
        print("   Or check manually in your Supabase dashboard")
        
        # Try to check if pgvector extension is enabled
        try:
            # This is a simple way to check if we can access the table
            result = db.client.table("content_embeddings").select("id").limit(1).execute()
            print("✅ content_embeddings table is accessible")
        except Exception as e:
            print(f"⚠️  Issue accessing content_embeddings table: {e}")
        
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")

if __name__ == "__main__":
    # Fix schema first
    fix_content_embeddings_schema()
    
    # Then view vectors
    view_stored_vectors()
    
    # Check indexes
    check_vector_indexes()
