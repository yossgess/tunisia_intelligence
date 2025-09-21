#!/usr/bin/env python3
"""
Check the actual schema of content_embeddings table.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseManager

def check_table_schema():
    """Check the actual schema of content_embeddings table."""
    print("🔍 CHECKING CONTENT_EMBEDDINGS TABLE SCHEMA")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Check if table exists and get its schema
        schema_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'content_embeddings'
        ORDER BY ordinal_position;
        """
        
        result = db.execute_query(schema_query)
        
        if result:
            print("✅ content_embeddings table schema:")
            print("-" * 50)
            for row in result:
                nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {row['column_default']}" if row['column_default'] else ""
                print(f"  {row['column_name']:<20} {row['data_type']:<15} {nullable}{default}")
        else:
            print("❌ content_embeddings table not found")
            
            # Check what tables do exist
            print("\n🔍 Available tables:")
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
            
            tables_result = db.execute_query(tables_query)
            if tables_result:
                for table in tables_result:
                    print(f"  - {table['table_name']}")
            
        # Also check for any vector-related tables
        print(f"\n🔍 Checking for vector-related tables...")
        vector_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (table_name LIKE '%vector%' OR table_name LIKE '%embedding%')
        ORDER BY table_name;
        """
        
        vector_tables = db.execute_query(vector_tables_query)
        if vector_tables:
            print("Vector-related tables found:")
            for table in vector_tables:
                print(f"  - {table['table_name']}")
        else:
            print("No vector-related tables found")
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_table_schema()
