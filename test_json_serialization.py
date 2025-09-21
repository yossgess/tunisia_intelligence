#!/usr/bin/env python3
"""
Test JSON serialization for dashboard data

This script tests the JSON serialization functionality to ensure
datetime objects are properly handled.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def serialize_for_json(obj):
    """Serialize objects for JSON transmission."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return {k: serialize_for_json(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def test_datetime_serialization():
    """Test datetime serialization."""
    print("Testing datetime serialization...")
    
    # Create test data with datetime objects
    test_data = {
        'timestamp': datetime.now(),
        'system_health': {
            'status': 'healthy',
            'last_check': datetime.now()
        },
        'pipelines': {
            'rss': {
                'enabled': True,
                'last_run': datetime.now(),
                'metrics': {
                    'start_time': datetime.now(),
                    'items_processed': 10
                }
            }
        },
        'alerts': [
            {
                'id': 1,
                'message': 'Test alert',
                'timestamp': datetime.now(),
                'level': 'info'
            }
        ]
    }
    
    print("Original data contains datetime objects:")
    print(f"- timestamp: {test_data['timestamp']}")
    print(f"- system_health.last_check: {test_data['system_health']['last_check']}")
    
    # Test serialization
    try:
        serialized_data = serialize_for_json(test_data)
        print("\n✅ Serialization successful!")
        
        # Test JSON encoding
        json_string = json.dumps(serialized_data)
        print("✅ JSON encoding successful!")
        
        # Test JSON decoding
        decoded_data = json.loads(json_string)
        print("✅ JSON decoding successful!")
        
        print(f"\nSerialized timestamp: {decoded_data['timestamp']}")
        print(f"Serialized last_check: {decoded_data['system_health']['last_check']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        return False

def test_flask_json_encoder():
    """Test Flask JSON encoder."""
    print("\nTesting Flask JSON encoder...")
    
    try:
        # Import the custom encoder
        from web_dashboard.app import DateTimeEncoder
        
        test_data = {
            'timestamp': datetime.now(),
            'message': 'Test message'
        }
        
        # Test encoding
        json_string = json.dumps(test_data, cls=DateTimeEncoder)
        print("✅ Flask DateTimeEncoder works!")
        print(f"Encoded: {json_string}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask encoder test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Tunisia Intelligence Dashboard - JSON Serialization Test")
    print("=" * 60)
    
    success1 = test_datetime_serialization()
    success2 = test_flask_json_encoder()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All JSON serialization tests passed!")
        print("The dashboard should now work without datetime serialization errors.")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
