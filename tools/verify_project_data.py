"""Verify which user is in each project."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from backend.config import Settings

def main():
    settings = Settings()
    
    print("="*70)
    print("VERIFYING PROJECT DATA")
    print("="*70)
    
    # Check Project 1
    print("\nProject 1 (Wilson Rodrigues):")
    print(f"  URL: {settings.SUPABASE_URL_PROJECT1[:50] if settings.SUPABASE_URL_PROJECT1 else 'Not set'}...")
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        try:
            client = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
            response = client.table("users").select("name, id").execute()
            users = response.data
            if users:
                print(f"  User: {users[0].get('name', 'N/A')}")
                print(f"  ID: {users[0].get('id', 'N/A')[:8]}...")
            else:
                print("  No users found")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Check Project 2
    print("\nProject 2 (Daniela Silva):")
    print(f"  URL: {settings.SUPABASE_URL_PROJECT2[:50] if settings.SUPABASE_URL_PROJECT2 else 'Not set'}...")
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        try:
            client = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
            response = client.table("users").select("name, id").execute()
            users = response.data
            if users:
                print(f"  User: {users[0].get('name', 'N/A')}")
                print(f"  ID: {users[0].get('id', 'N/A')[:8]}...")
            else:
                print("  No users found")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*70)
    print("SWITCHING TEST")
    print("="*70)
    
    # Test switching
    import os
    import backend.database
    
    for project in ["project1", "project2"]:
        print(f"\nTesting {project}:")
        os.environ['SUPABASE_PROJECT'] = project
        
        # Clear both caches
        backend.database._db_instance = None
        backend.database._current_project = None
        
        # Reload global settings
        import backend.config
        backend.config.settings = Settings()
        test_settings = backend.config.settings
        
        print(f"  SUPABASE_PROJECT: {test_settings.SUPABASE_PROJECT}")
        print(f"  Active URL: {test_settings.supabase_url[:50] if test_settings.supabase_url else 'None'}...")
        
        try:
            from backend.database import get_db
            db = get_db()
            users = db.list_users()
            if users:
                print(f"  Connected to: {users[0].get('name', 'N/A')}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()

