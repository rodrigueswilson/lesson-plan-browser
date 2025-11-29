"""Check which database is currently configured."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.database import get_db

def main():
    print("=" * 70)
    print("DATABASE CONFIGURATION")
    print("=" * 70)
    
    print(f"\nUSE_SUPABASE: {settings.USE_SUPABASE}")
    print(f"SUPABASE_PROJECT: {settings.SUPABASE_PROJECT}")
    
    print("\nProject 1 (Wilson Rodrigues):")
    if settings.SUPABASE_URL_PROJECT1:
        print(f"  URL: {settings.SUPABASE_URL_PROJECT1[:60]}...")
    else:
        print("  URL: Not set")
    print(f"  Key: {'Set' if settings.SUPABASE_KEY_PROJECT1 else 'Not set'}")
    
    print("\nProject 2 (Daniela Silva):")
    if settings.SUPABASE_URL_PROJECT2:
        print(f"  URL: {settings.SUPABASE_URL_PROJECT2[:60]}...")
    else:
        print("  URL: Not set")
    print(f"  Key: {'Set' if settings.SUPABASE_KEY_PROJECT2 else 'Not set'}")
    
    print("\nActive Project (based on SUPABASE_PROJECT):")
    if settings.supabase_url:
        print(f"  URL: {settings.supabase_url[:60]}...")
    else:
        print("  URL: Not set")
    print(f"  Key: {'Set' if settings.supabase_key else 'Not set'}")
    
    print("\n" + "=" * 70)
    print("ACTIVE DATABASE")
    print("=" * 70)
    
    try:
        db = get_db()
        db_type = type(db).__name__
        print(f"\nDatabase Type: {db_type}")
        
        if "Supabase" in db_type:
            print("Status: Using Supabase PostgreSQL (Cloud)")
            print("\nCurrent Supabase Project Data:")
            users = db.list_users()
            print(f"  Users: {len(users)}")
            if users:
                for user in users:
                    print(f"    - {user.get('name', 'N/A')}")
        else:
            print("Status: Using SQLite (Local)")
            print("\nCurrent SQLite Database:")
            users = db.list_users()
            print(f"  Users: {len(users)}")
            if users:
                for user in users[:5]:  # Show first 5
                    print(f"    - {user.get('name', 'N/A')}")
                if len(users) > 5:
                    print(f"    ... and {len(users) - 5} more")
    except Exception as e:
        print(f"\nError: {e}")
        print("Cannot determine active database")

if __name__ == "__main__":
    main()

