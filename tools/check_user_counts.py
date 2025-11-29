#!/usr/bin/env python3
"""Check user counts in SQLite and Supabase projects."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import Settings
from backend.supabase_database import SupabaseDatabase
from backend.database import SQLiteDatabase

def main():
    # Check SQLite
    sqlite_db = SQLiteDatabase()
    sqlite_users = sqlite_db.list_users()
    print(f"SQLite: {len(sqlite_users)} users")
    for u in sqlite_users:
        print(f"  - {u.id}: {u.name}")
    
    print()
    
    # Check Supabase project1
    try:
        s1 = Settings()
        s1.SUPABASE_PROJECT = 'project1'
        db1 = SupabaseDatabase(custom_settings=s1)
        users1 = db1.list_users()
        print(f"Supabase Project1: {len(users1)} users")
        for u in users1:
            print(f"  - {u.id}: {u.name}")
    except Exception as e:
        print(f"Supabase Project1: Error - {e}")
    
    print()
    
    # Check Supabase project2
    try:
        s2 = Settings()
        s2.SUPABASE_PROJECT = 'project2'
        db2 = SupabaseDatabase(custom_settings=s2)
        users2 = db2.list_users()
        print(f"Supabase Project2: {len(users2)} users")
        for u in users2:
            print(f"  - {u.id}: {u.name}")
    except Exception as e:
        print(f"Supabase Project2: Error - {e}")
    
    print()
    
    # Check API endpoint (combined)
    try:
        from backend.api import list_users
        import asyncio
        all_users = asyncio.run(list_users())
        print(f"API /api/users: {len(all_users)} users (after deduplication)")
        for u in all_users:
            print(f"  - {u.id}: {u.name}")
    except Exception as e:
        print(f"API check: Error - {e}")

if __name__ == "__main__":
    main()

