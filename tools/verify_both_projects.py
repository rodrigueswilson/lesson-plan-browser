"""Verify data in both Supabase projects."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from backend.config import Settings

def check_project(project_num: str, settings: Settings):
    """Check a specific project."""
    if project_num == "1":
        url = settings.SUPABASE_URL_PROJECT1
        key = settings.SUPABASE_KEY_PROJECT1
        name = "Wilson Rodrigues"
    else:
        url = settings.SUPABASE_URL_PROJECT2
        key = settings.SUPABASE_KEY_PROJECT2
        name = "Daniela Silva"
    
    if not url or not key:
        print(f"\nProject {project_num} ({name}): Not configured")
        return
    
    print(f"\n{'='*70}")
    print(f"Project {project_num} ({name})")
    print('='*70)
    print(f"URL: {url[:60]}...")
    
    try:
        client = create_client(url, key)
        response = client.table("users").select("*").execute()
        users = response.data
        
        print(f"\nUsers found: {len(users)}")
        for user in users:
            print(f"  - {user.get('name', 'N/A')} (ID: {user.get('id', 'N/A')[:8]}...)")
            
            # Get related data
            slots_response = client.table("class_slots").select("id").eq("user_id", user['id']).execute()
            plans_response = client.table("weekly_plans").select("id").eq("user_id", user['id']).execute()
            
            print(f"    Class slots: {len(slots_response.data)}")
            print(f"    Weekly plans: {len(plans_response.data)}")
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    settings = Settings()
    
    print("="*70)
    print("VERIFYING BOTH SUPABASE PROJECTS")
    print("="*70)
    
    check_project("1", settings)
    check_project("2", settings)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nTo switch projects, change SUPABASE_PROJECT in .env:")
    print("  SUPABASE_PROJECT=project1  (for Wilson Rodrigues)")
    print("  SUPABASE_PROJECT=project2  (for Daniela Silva)")

if __name__ == "__main__":
    main()

