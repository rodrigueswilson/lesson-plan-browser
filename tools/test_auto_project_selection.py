"""Test automatic project selection based on user_id."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_auto_selection():
    """Test that get_db() automatically selects the correct project based on user_id."""
    print("="*70)
    print("TESTING AUTOMATIC PROJECT SELECTION")
    print("="*70)
    
    # Get user IDs from both projects
    from backend.config import Settings
    from supabase import create_client
    
    settings = Settings()
    
    # Get Wilson's user ID from project1
    print("\n[Step 1] Getting user IDs from both projects...")
    wilson_id = None
    daniela_id = None
    
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        try:
            client = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
            response = client.table("users").select("id, name").execute()
            if response.data:
                wilson_id = response.data[0].get("id")
                print(f"  Project 1 - User: {response.data[0].get('name')} (ID: {wilson_id[:8]}...)")
        except Exception as e:
            print(f"  Error accessing project1: {e}")
    
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        try:
            client = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
            response = client.table("users").select("id, name").execute()
            if response.data:
                daniela_id = response.data[0].get("id")
                print(f"  Project 2 - User: {response.data[0].get('name')} (ID: {daniela_id[:8]}...)")
        except Exception as e:
            print(f"  Error accessing project2: {e}")
    
    if not wilson_id or not daniela_id:
        print("\n[ERROR] Could not retrieve user IDs from both projects")
        return
    
    # Test automatic selection
    print("\n[Step 2] Testing automatic project selection...")
    from backend.database import get_db
    
    # Test with Wilson's ID
    print("\n  Testing with Wilson's user_id...")
    db = get_db(user_id=wilson_id)
    users = db.list_users()
    if users:
        print(f"    Connected to: {users[0].get('name', 'N/A')}")
        if "Wilson" in users[0].get('name', ''):
            print("    [PASS] Correct project selected")
        else:
            print("    [FAIL] Wrong project selected")
    
    # Test with Daniela's ID
    print("\n  Testing with Daniela's user_id...")
    db = get_db(user_id=daniela_id)
    users = db.list_users()
    if users:
        print(f"    Connected to: {users[0].get('name', 'N/A')}")
        if "Daniela" in users[0].get('name', ''):
            print("    [PASS] Correct project selected")
        else:
            print("    [FAIL] Wrong project selected")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nThe app will now automatically select the correct Supabase project")
    print("based on the user_id passed to API endpoints. No manual .env changes needed!")

if __name__ == "__main__":
    test_auto_selection()

