"""Test the project switching mechanism."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Clear database cache
import backend.database
backend.database._db_instance = None

def test_switch():
    """Test switching between projects."""
    print("="*70)
    print("TESTING PROJECT SWITCHING MECHANISM")
    print("="*70)
    
    # Test Project 1
    print("\n[TEST 1] Setting SUPABASE_PROJECT=project1")
    os.environ['SUPABASE_PROJECT'] = 'project1'
    backend.database._db_instance = None
    
    # Reload settings
    from backend.config import Settings
    settings = Settings()
    print(f"  SUPABASE_PROJECT: {settings.SUPABASE_PROJECT}")
    print(f"  Active URL: {settings.supabase_url[:50] if settings.supabase_url else 'None'}...")
    
    try:
        from backend.database import get_db
        db = get_db()
        users = db.list_users()
        print(f"  Connection: SUCCESS")
        print(f"  Users: {len(users)}")
        if users:
            print(f"    - {users[0].get('name', 'N/A')}")
            expected = "Wilson Rodrigues"
            actual = users[0].get('name', '')
            if expected in actual:
                print(f"  [PASS] Correct user ({expected})")
            else:
                print(f"  [FAIL] Expected {expected}, got {actual}")
    except Exception as e:
        print(f"  Connection: FAILED - {e}")
    
    # Test Project 2
    print("\n[TEST 2] Setting SUPABASE_PROJECT=project2")
    os.environ['SUPABASE_PROJECT'] = 'project2'
    backend.database._db_instance = None
    
    # Reload settings
    settings = Settings()
    print(f"  SUPABASE_PROJECT: {settings.SUPABASE_PROJECT}")
    print(f"  Active URL: {settings.supabase_url[:50] if settings.supabase_url else 'None'}...")
    
    try:
        from backend.database import get_db
        db = get_db()
        users = db.list_users()
        print(f"  Connection: SUCCESS")
        print(f"  Users: {len(users)}")
        if users:
            print(f"    - {users[0].get('name', 'N/A')}")
            expected = "Daniela Silva"
            actual = users[0].get('name', '')
            if expected in actual:
                print(f"  [PASS] Correct user ({expected})")
            else:
                print(f"  [FAIL] Expected {expected}, got {actual}")
    except Exception as e:
        print(f"  Connection: FAILED - {e}")
    
    print("\n" + "="*70)
    print("SWITCHING TEST COMPLETE")
    print("="*70)
    print("\nNote: In production, change SUPABASE_PROJECT in .env and restart backend")

if __name__ == "__main__":
    test_switch()

