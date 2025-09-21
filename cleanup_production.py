#!/usr/bin/env python3
"""
Production Cleanup Script for Tunisia Intelligence AI Enrichment System.
Removes test files, debug files, and organizes the production-ready module.
"""

import os
import shutil
from pathlib import Path

def cleanup_production():
    """Clean up test files and organize production files."""
    
    base_dir = Path(__file__).parent
    
    # Files to remove (test/debug files)
    files_to_remove = [
        # Test files
        "test_sentiment_constraint.py",
        "test_direct_update.py",
        "test_unified_enrichment.py",  # Keep the fixed version
        "force_drop_constraint.py",
        "bypass_constraint_with_trigger.py",
        
        # Debug SQL files
        "debug_sentiment_constraints.sql",
        "fix_sentiment_constraint.sql",
        "fix_all_sentiment_constraints.sql",
        "fix_all_table_sentiment_constraints.sql",
        "final_sentiment_fix.sql",
        "verify_and_fix_constraint.sql",
        "check_constraint_status.sql",
        "fix_remaining_comment_constraint.sql",
        "fix_comment_data_and_constraint.sql",
        "force_drop_comment_constraint.sql",
        "force_drop_constraint.sql",
        "root_cause_investigation.sql",
        "debug_content_analysis_constraint.sql",
        "fix_existing_sentiment_data.sql",
        
        # Temporary fix files
        "fix_comment_trigger.sql",
        "standardize_french_sentiment.sql",
    ]
    
    print("🧹 Cleaning up test and debug files...")
    removed_count = 0
    
    for file_name in files_to_remove:
        file_path = base_dir / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Removed: {file_name}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {file_name}: {e}")
        else:
            print(f"⚠️  Not found: {file_name}")
    
    print(f"\n📊 Cleanup Summary: {removed_count} files removed")
    
    # Rename the working unified test to production name
    old_test = base_dir / "test_unified_enrichment_fixed.py"
    new_test = base_dir / "production_enrichment_test.py"
    
    if old_test.exists():
        try:
            shutil.move(str(old_test), str(new_test))
            print(f"✅ Renamed: test_unified_enrichment_fixed.py → production_enrichment_test.py")
        except Exception as e:
            print(f"❌ Failed to rename test file: {e}")
    
    print("\n🎯 Production-ready files:")
    production_files = [
        "run_enhanced_enrichment_simple.py",
        "production_enrichment_test.py",
        "config/database.py",
        "ai_enrichment/",
    ]
    
    for file_name in production_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ Missing: {file_name}")
    
    return removed_count

if __name__ == "__main__":
    removed = cleanup_production()
    print(f"\n🎉 Production cleanup completed! Removed {removed} test/debug files.")
    print("🚀 Tunisia Intelligence AI Enrichment System is production-ready!")
