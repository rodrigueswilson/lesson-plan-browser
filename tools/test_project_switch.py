"""Test switching between Supabase projects."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Clear any cached database instance
import backend.database
backend.database._db_instance = None

def test_project(project_name: str):
    """Test connecting to a specific project."""
    print(f"\n{'='*70}")
    print(f"Testing {project_name.upper()}")
    print('='*70)
    
    # Set environment variable for this test
    os.environ['SUPABASE_PROJECT'] = project_name
    
    # Reload settings
    from backend.config import Settings
    test_settings = Settings()
    
    print(f"\nSUPABASE_PROJECT: {test_settings.SUPABASE_PROJECT}")
    
    # Check if credentials are set
    url = test_settings.supabase_url
    key = test_settings.supabase_key
    
    if not url or not key:
        print(f"  ERROR: Credentials not set for {project_name}")
        print(f"  URL: {'Set' if url else 'Not set'}")
        print(f"  Key: {'Set' if key else 'Not set'}")
        return False
    
    print(f"  URL: {url[:60]}...")
    print(f"  Key: Set (length: {len(key)})")
    
    # Try to connect
    try:
        from backend.supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        users = db.list_users()
        print(f"\n  Connection: SUCCESS")
        print(f"  Users found: {len(users)}")
        if users:
            for user in users:
                print(f"    - {user.get('name', 'N/A')}")
        return True
    except Exception as e:
        print(f"\n  Connection: FAILED")
        print(f"  Error: {e}")
        return False

def main():
    print("="*70)
    print("SUPABASE PROJECT SWITCHING TEST")
    print("="*70)
    
    # Test project1
    result1 = test_project("project1")
    
    # Clear cache
    backend.database._db_instance = None
    
    # Test project2
    result2 = test_project("project2")
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    print(f"Project 1 (Wilson): {'PASS' if result1 else 'FAIL'}")
    print(f"Project 2 (Daniela): {'PASS' if result2 else 'FAIL'}")
    
    if result1 and result2:
        print("\n[SUCCESS] Both projects are configured and accessible!")
    elif result1:
        print("\n[WARNING] Only Project 1 is configured")
    elif result2:
        print("\n[WARNING] Only Project 2 is configured")
    else:
        print("\n[ERROR] Neither project is properly configured")

if __name__ == "__main__":
    main()

