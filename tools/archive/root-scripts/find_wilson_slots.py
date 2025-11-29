"""
Search for Wilson's missing slots in all possible locations.
"""

import sqlite3
import os
import sys
from pathlib import Path
from backend.config import Settings
from supabase import create_client

WILSON_USER_ID = "8d3154dc-1d16-4b9c-9b30-07397630465e"
WILSON_NAME = "Wilson Rodrigues"

print("=" * 60)
print("Searching for Wilson's Missing Slots")
print("=" * 60)

# 1. Check all SQLite databases
print("\n[1] Checking SQLite Databases")
data_dir = Path("data")
db_files = list(data_dir.glob("*.db"))

for db_file in db_files:
    print(f"\n  Checking {db_file.name}...")
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Find Wilson by name or ID
        cursor.execute("""
            SELECT id, name, first_name, last_name 
            FROM users 
            WHERE id = ? OR name LIKE ? OR (first_name || ' ' || last_name) LIKE ?
        """, (WILSON_USER_ID, f"%Wilson%", f"%Wilson%"))
        users = cursor.fetchall()
        
        for user in users:
            user_id = user[0]
            user_name = user[1] or f"{user[2]} {user[3]}"
            print(f"    Found user: {user_name} (ID: {user_id})")
            
            # Get slots for this user
            cursor.execute("""
                SELECT slot_number, subject, grade, homeroom 
                FROM class_slots 
                WHERE user_id = ?
                ORDER BY slot_number
            """, (user_id,))
            slots = cursor.fetchall()
            
            if slots:
                print(f"    Found {len(slots)} slot(s):")
                for slot in slots:
                    print(f"      Slot {slot[0]}: {slot[1]} - Grade {slot[2]} (Homeroom: {slot[3] or 'N/A'})")
            else:
                print(f"    No slots found")
        
        conn.close()
    except Exception as e:
        print(f"    Error: {e}")

# 2. Check Supabase Project 1
print("\n[2] Checking Supabase Project 1")
settings = Settings()
try:
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
        
        # Search for Wilson by name
        user_response = client1.table("users").select("*").or_("name.ilike.%Wilson%,first_name.ilike.%Wilson%").execute()
        
        if user_response.data:
            print(f"  Found {len(user_response.data)} user(s) matching 'Wilson':")
            for user in user_response.data:
                user_id = user['id']
                user_name = user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                print(f"    User: {user_name} (ID: {user_id})")
                
                # Get slots
                slots_response = client1.table("class_slots").select("*").eq("user_id", user_id).order("slot_number").execute()
                slots = slots_response.data
                
                if slots:
                    print(f"    Found {len(slots)} slot(s):")
                    for slot in slots:
                        print(f"      Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
                else:
                    print(f"    No slots found")
        else:
            print("  No users found matching 'Wilson'")
    else:
        print("  Project 1 credentials not configured")
except Exception as e:
    print(f"  Error: {e}")

# 3. Check Supabase Project 2
print("\n[3] Checking Supabase Project 2")
try:
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
        
        # Search for Wilson by name
        user_response = client2.table("users").select("*").or_("name.ilike.%Wilson%,first_name.ilike.%Wilson%").execute()
        
        if user_response.data:
            print(f"  Found {len(user_response.data)} user(s) matching 'Wilson':")
            for user in user_response.data:
                user_id = user['id']
                user_name = user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                print(f"    User: {user_name} (ID: {user_id})")
                
                # Get slots
                slots_response = client2.table("class_slots").select("*").eq("user_id", user_id).order("slot_number").execute()
                slots = slots_response.data
                
                if slots:
                    print(f"    Found {len(slots)} slot(s):")
                    for slot in slots:
                        print(f"      Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['subject']} - Grade {slot['grade']} (Homeroom: {slot.get('homeroom') or 'N/A'})")
                else:
                    print(f"    No slots found")
        else:
            print("  No users found matching 'Wilson'")
    else:
        print("  Project 2 credentials not configured")
except Exception as e:
    print(f"  Error: {e}")

# 4. Check if slots might be associated with a different user_id
print("\n[4] Checking for orphaned slots (slots without matching user)")
try:
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
        # Get all slots and check if user exists
        all_slots = client1.table("class_slots").select("*").execute()
        print(f"  Project 1: Found {len(all_slots.data)} total slot(s)")
        
        for slot in all_slots.data:
            user_check = client1.table("users").select("id").eq("id", slot['user_id']).execute()
            if not user_check.data:
                print(f"    Orphaned slot: Slot {slot['slot_number']} - {slot['subject']} (user_id: {slot['user_id']})")
except Exception as e:
    print(f"  Error: {e}")

try:
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
        all_slots = client2.table("class_slots").select("*").execute()
        print(f"  Project 2: Found {len(all_slots.data)} total slot(s)")
        
        for slot in all_slots.data:
            user_check = client2.table("users").select("id").eq("id", slot['user_id']).execute()
            if not user_check.data:
                print(f"    Orphaned slot: Slot {slot['slot_number']} - {slot['subject']} (user_id: {slot['user_id']})")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("Search Complete")
print("=" * 60)

