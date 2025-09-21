#!/usr/bin/env python3
"""
Script to check stored vectors in the Tunisia Intelligence database.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager

def check_vector_storage():
    """Check all vector storage locations in the database."""
    print("🔍 CHECKING VECTOR STORAGE IN DATABASE")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Check content_embeddings table (primary vector storage)
        print("\n📊 CONTENT EMBEDDINGS TABLE:")
        print("-" * 40)
        
        result = db.execute_query("""
            SELECT 
                content_type,
                COUNT(*) as count,
                COUNT(content_embedding) as content_vectors,
                COUNT(title_embedding) as title_vectors,
                COUNT(entity_embedding) as entity_vectors,
                AVG(vector_dims(content_embedding)) as avg_content_dims,
                AVG(vector_dims(title_embedding)) as avg_title_dims,
                MIN(created_at) as oldest_vector,
                MAX(created_at) as newest_vector
            FROM content_embeddings 
            GROUP BY content_type
            ORDER BY count DESC;
        """)
        
        if result:
            for row in result:
                print(f"Content Type: {row['content_type']}")
                print(f"  Total Records: {row['count']}")
                print(f"  Content Vectors: {row['content_vectors']}")
                print(f"  Title Vectors: {row['title_vectors']}")
                print(f"  Entity Vectors: {row['entity_vectors']}")
                if row['avg_content_dims']:
                    print(f"  Avg Content Dimensions: {row['avg_content_dims']:.0f}")
                if row['avg_title_dims']:
                    print(f"  Avg Title Dimensions: {row['avg_title_dims']:.0f}")
                print(f"  Date Range: {row['oldest_vector']} to {row['newest_vector']}")
                print()
        else:
            print("❌ No vectors found in content_embeddings table")
        
        # Check total vector statistics using the SQL function
        print("\n📈 VECTOR STATISTICS (using SQL function):")
        print("-" * 40)
        
        stats_result = db.execute_query("SELECT * FROM get_vector_statistics();")
        if stats_result and stats_result[0]:
            stats = stats_result[0]
            print(f"Total Vectors: {stats['total_vectors']}")
            print(f"Average Dimensions: {stats['avg_dimensions']:.0f}")
            print(f"Storage Size: {stats['storage_size_mb']:.2f} MB")
            print(f"By Content Type: {stats['by_content_type']}")
        
        # Check vectors in other tables
        print("\n🗂️  VECTORS IN OTHER TABLES:")
        print("-" * 40)
        
        # Check articles table
        articles_result = db.execute_query("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(embedding) as articles_with_vectors,
                AVG(vector_dims(embedding)) as avg_dimensions
            FROM articles 
            WHERE embedding IS NOT NULL;
        """)
        
        if articles_result and articles_result[0]:
            row = articles_result[0]
            print(f"News Articles with Vectors: {row['articles_with_vectors']}/{row['total_articles'] or 0}")
            if row['avg_dimensions']:
                print(f"  Average Dimensions: {row['avg_dimensions']:.0f}")
        
        # Check social_media_posts table
        posts_result = db.execute_query("""
            SELECT 
                COUNT(*) as total_posts,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as posts_with_vectors
            FROM social_media_posts;
        """)
        
        if posts_result and posts_result[0]:
            row = posts_result[0]
            print(f"Social Media Posts with Vectors: {row['posts_with_vectors'] or 0}/{row['total_posts'] or 0}")
        
        # Check entities table
        entities_result = db.execute_query("""
            SELECT 
                COUNT(*) as total_entities,
                COUNT(embedding) as entities_with_vectors,
                AVG(vector_dims(embedding)) as avg_dimensions
            FROM entities 
            WHERE embedding IS NOT NULL;
        """)
        
        if entities_result and entities_result[0]:
            row = entities_result[0]
            print(f"Entities with Vectors: {row['entities_with_vectors'] or 0}/{row['total_entities'] or 0}")
            if row['avg_dimensions']:
                print(f"  Average Dimensions: {row['avg_dimensions']:.0f}")
        
        # Check pgvector extension and indexes
        print("\n🔧 PGVECTOR EXTENSION & INDEXES:")
        print("-" * 40)
        
        extension_result = db.execute_query("SELECT * FROM check_pgvector_extension();")
        if extension_result:
            print(f"pgvector Extension Enabled: {extension_result[0]['enabled']}")
        
        indexes_result = db.execute_query("SELECT * FROM check_vector_indexes();")
        if indexes_result and indexes_result[0]:
            row = indexes_result[0]
            print(f"All Vector Indexes Exist: {row['all_exist']}")
            if row['missing_indexes']:
                print(f"Missing Indexes: {row['missing_indexes']}")
        
        # Show sample vectors
        print("\n📝 SAMPLE VECTORS:")
        print("-" * 40)
        
        sample_result = db.execute_query("""
            SELECT 
                content_type,
                content_id,
                language,
                vector_dims(content_embedding) as dimensions,
                LEFT(content_hash, 8) as hash_preview,
                created_at
            FROM content_embeddings 
            WHERE content_embedding IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        
        if sample_result:
            for i, row in enumerate(sample_result, 1):
                print(f"{i}. {row['content_type']} {row['content_id']}")
                print(f"   Language: {row['language']}, Dimensions: {row['dimensions']}")
                print(f"   Hash: {row['hash_preview']}..., Created: {row['created_at']}")
        else:
            print("No sample vectors found")
        
        print(f"\n✅ Vector storage check completed at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Error checking vector storage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vector_storage()
