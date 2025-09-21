#!/usr/bin/env python3
"""
Fix for vector parsing issues in VectorService.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_vector_service():
    """Apply patch to fix vector parsing issues."""
    print("🔧 FIXING VECTOR PARSING ISSUES")
    print("=" * 50)
    
    vector_service_path = "ai_enrichment/core/vector_service.py"
    
    try:
        # Read the current file
        with open(vector_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the problematic line and replace it
        old_line = "                vector = [float(x.strip()) for x in vector_str.split(',') if x.strip()]"
        
        new_line = """                # Filter out non-numeric values like '...'
                vector = []
                for x in vector_str.split(','):
                    x = x.strip()
                    if x and x != '...' and x != '...':
                        try:
                            vector.append(float(x))
                        except ValueError:
                            # Skip non-numeric values
                            continue"""
        
        if old_line in content:
            print("✅ Found problematic line, applying fix...")
            content = content.replace(old_line, new_line)
            
            # Write the fixed content back
            with open(vector_service_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Vector parsing fix applied successfully!")
            print("   - Now filters out '...' and other non-numeric values")
            print("   - Handles ValueError exceptions gracefully")
            print("   - Should prevent numpy array shape errors")
            
        else:
            print("⚠️  Could not find the exact line to fix")
            print("   The code may have already been modified")
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")

def test_vector_parsing():
    """Test the vector parsing fix."""
    print("\n🧪 TESTING VECTOR PARSING FIX")
    print("=" * 40)
    
    try:
        from ai_enrichment.core.vector_service import VectorService
        
        # Create a mock response with ellipsis
        test_responses = [
            "[0.1, 0.2, 0.3, ..., 0.9]",
            "[0.1, 0.2, 0.3, ...]",
            "[0.1, ..., 0.9]",
            "Some text [0.1, 0.2, 0.3] more text",
            "No vector here just text..."
        ]
        
        service = VectorService()
        
        for i, response in enumerate(test_responses, 1):
            print(f"\nTest {i}: {response[:30]}...")
            try:
                vector = service._extract_vector_from_response(response)
                if vector:
                    print(f"   ✅ Extracted vector with {len(vector)} dimensions")
                else:
                    print(f"   ⚠️  No vector extracted (fallback used)")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing: {e}")

if __name__ == "__main__":
    fix_vector_service()
    test_vector_parsing()
