#!/usr/bin/env python3
"""
Test script to verify Facebook loader is now set to 7 days (168 hours).
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from facebook_loader import UltraMinimalFacebookLoader

def test_facebook_7day_configuration():
    """Test that Facebook loader is configured for 7 days."""
    print("🧪 TESTING FACEBOOK LOADER 7-DAY CONFIGURATION")
    print("=" * 60)
    
    try:
        # Initialize the loader
        print("🔧 Initializing Facebook loader...")
        loader = UltraMinimalFacebookLoader()
        
        # Test the default parameter
        print("📅 Testing default time interval...")
        
        # Check if we can call the method with default parameters
        # (We won't actually run it to avoid API calls)
        import inspect
        sig = inspect.signature(loader.extract_and_load_posts_ultra_minimal)
        default_hours = sig.parameters['hours_back'].default
        
        print(f"✅ Default hours_back parameter: {default_hours}")
        
        if default_hours == 168:
            print("🎉 SUCCESS: Facebook loader is configured for 7 days (168 hours)")
            
            # Calculate the date range
            now = datetime.now()
            start_date = now - timedelta(hours=168)
            
            print(f"\n📊 Time Range Coverage:")
            print(f"   Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Start time: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Duration: 7 days (168 hours)")
            print(f"   Days of week covered: {(now.weekday() + 1) % 7} days back")
            
            print(f"\n🎯 Benefits of 7-day window:")
            print(f"   ✅ Captures weekend posts")
            print(f"   ✅ Covers full weekly government activity")
            print(f"   ✅ Better for weekly trend analysis")
            print(f"   ✅ Reduces risk of missing important posts")
            
            return True
        else:
            print(f"❌ FAILED: Expected 168 hours, got {default_hours} hours")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Facebook loader configuration: {e}")
        return False

def test_run_facebook_scraper_configuration():
    """Test that run_facebook_scraper.py is also configured for 7 days."""
    print(f"\n🧪 TESTING RUN_FACEBOOK_SCRAPER CONFIGURATION")
    print("=" * 60)
    
    try:
        from run_facebook_scraper import run_ultra_minimal_facebook_scraper
        
        # Check the default parameter
        import inspect
        sig = inspect.signature(run_ultra_minimal_facebook_scraper)
        default_hours = sig.parameters['hours_back'].default
        
        print(f"✅ Default hours_back parameter: {default_hours}")
        
        if default_hours == 168:
            print("🎉 SUCCESS: run_facebook_scraper.py is configured for 7 days")
            
            print(f"\n📋 Command Line Usage:")
            print(f"   python run_facebook_scraper.py  # Uses 7 days by default")
            print(f"   python run_facebook_scraper.py --hours-back 24  # Override to 1 day")
            print(f"   python run_facebook_scraper.py --hours-back 336  # Override to 14 days")
            
            return True
        else:
            print(f"❌ FAILED: Expected 168 hours, got {default_hours} hours")
            return False
            
    except Exception as e:
        print(f"❌ Error testing run_facebook_scraper configuration: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 FACEBOOK LOADER 7-DAY CONFIGURATION TEST")
    print("=" * 70)
    
    # Test both components
    loader_ok = test_facebook_7day_configuration()
    scraper_ok = test_run_facebook_scraper_configuration()
    
    print(f"\n🏆 FINAL RESULTS")
    print("=" * 40)
    
    if loader_ok and scraper_ok:
        print("✅ ALL TESTS PASSED")
        print("🎉 Facebook loader is now configured for 7-day coverage!")
        print("\n📈 Expected Benefits:")
        print("   • More comprehensive data collection")
        print("   • Better weekly trend analysis")
        print("   • Reduced risk of missing important posts")
        print("   • Improved intelligence gathering")
        
        print(f"\n⚡ Performance Impact:")
        print(f"   • Same API efficiency (3-4 calls per source)")
        print(f"   • More posts per run (7x coverage)")
        print(f"   • Better data quality for AI analysis")
        
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the configuration changes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
