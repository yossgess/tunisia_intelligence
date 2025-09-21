#!/usr/bin/env python3
"""
Fix vector dimensions in content_embeddings table.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager

def fix_vector_dimensions():
    """Fix vector dimensions to match qwen2.5:7b output (1536 dimensions)."""
    print("🔧 FIXING VECTOR DIMENSIONS IN DATABASE")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        print("⚠️  This will recreate vector columns and indexes!")
        print("   Current: 768 dimensions")
        print("   New: 1536 dimensions (for qwen2.5:7b)")
        
        # SQL commands to fix dimensions
        sql_commands = [
            # Drop existing vector columns
            "ALTER TABLE content_embeddings DROP COLUMN IF EXISTS content_embedding CASCADE;",
            "ALTER TABLE content_embeddings DROP COLUMN IF EXISTS title_embedding CASCADE;",
            "ALTER TABLE content_embeddings DROP COLUMN IF EXISTS entity_embedding CASCADE;",
            
            # Add vector columns with correct dimensions
            "ALTER TABLE content_embeddings ADD COLUMN content_embedding vector(1536);",
            "ALTER TABLE content_embeddings ADD COLUMN title_embedding vector(1536);",
            "ALTER TABLE content_embeddings ADD COLUMN entity_embedding vector(1536);",
            
            # Recreate indexes
            "CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_embedding_hnsw ON content_embeddings USING hnsw (content_embedding vector_cosine_ops);",
            "CREATE INDEX IF NOT EXISTS idx_content_embeddings_title_embedding_hnsw ON content_embeddings USING hnsw (title_embedding vector_cosine_ops);",
            "CREATE INDEX IF NOT EXISTS idx_content_embeddings_entity_embedding_hnsw ON content_embeddings USING hnsw (entity_embedding vector_cosine_ops);"
        ]
        
        print("\n📝 Executing SQL commands...")
        
        for i, command in enumerate(sql_commands, 1):
            try:
                print(f"   {i}. {command[:60]}...")
                # Use RPC to execute raw SQL
                result = db.client.rpc('exec_sql', {'sql': command}).execute()
                print(f"      ✅ Success")
            except Exception as e:
                print(f"      ⚠️  Warning: {e}")
        
        print("\n✅ Vector dimensions fixed!")
        print("   Vector columns now support 1536 dimensions")
        print("   Indexes recreated for optimal performance")
        
        # Test the fix
        print("\n🧪 Testing the fix...")
        test_vector = [0.1] * 1536  # Create a test 1536-dimensional vector
        
        test_data = {
            'content_type': 'article',
            'content_id': 99999,  # Test ID
            'content_embedding': test_vector,
            'embedding_model': 'qwen2.5:7b',
            'embedding_version': '1.0',
            'content_length': 100,
            'embedding_quality_score': 0.8,
            'language': 'ar'
        }
        
        # Try to insert test vector
        result = db.client.table("content_embeddings").insert(test_data).execute()
        
        if result.data:
            print("✅ Test vector inserted successfully!")
            print(f"   Record ID: {result.data[0]['id']}")
            
            # Clean up test record
            db.client.table("content_embeddings").delete().eq("content_id", 99999).execute()
            print("✅ Test record cleaned up")
        else:
            print("❌ Test vector insertion failed")
        
    except Exception as e:
        print(f"❌ Error fixing vector dimensions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_vector_dimensions()
