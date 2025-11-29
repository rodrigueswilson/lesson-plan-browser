"""
Check for duplicate users and help clean them up.
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def list_all_users():
    """List all users from the API."""
    try:
        response = requests.get(f"{BASE_URL}/api/users", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def find_duplicates(users):
    """Find duplicate users by name."""
    from collections import defaultdict
    
    by_name = defaultdict(list)
    
    for user in users:
        name = user.get('name', '') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        by_name[name.lower()].append(user)
    
    duplicates = {name: users_list for name, users_list in by_name.items() if len(users_list) > 1}
    return duplicates

def main():
    print("=" * 60)
    print("Checking for Duplicate Users")
    print("=" * 60)
    
    users = list_all_users()
    
    if not users:
        print("No users found.")
        return
    
    print(f"\nFound {len(users)} total users:\n")
    
    for user in users:
        name = user.get('name', '') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        user_id = user.get('id', 'N/A')
        email = user.get('email', 'N/A')
        print(f"  - {name}")
        print(f"    ID: {user_id}")
        print(f"    Email: {email}")
        print()
    
    # Find duplicates
    duplicates = find_duplicates(users)
    
    if duplicates:
        print("\n" + "=" * 60)
        print("DUPLICATE USERS FOUND:")
        print("=" * 60)
        
        for name, users_list in duplicates.items():
            print(f"\n{name.upper()}:")
            for i, user in enumerate(users_list, 1):
                user_id = user.get('id', 'N/A')
                email = user.get('email', 'N/A')
                print(f"  {i}. ID: {user_id}")
                print(f"     Email: {email}")
                
                # Check slots for this user
                try:
                    slots_response = requests.get(f"{BASE_URL}/api/users/{user_id}/slots", timeout=10)
                    if slots_response.status_code == 200:
                        slots = slots_response.json()
                        print(f"     Slots: {len(slots)}")
                        for slot in slots:
                            print(f"       - Slot {slot.get('slot_number')}: {slot.get('subject')} - Grade {slot.get('grade')}")
                except Exception as e:
                    print(f"     Error checking slots: {e}")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATION:")
        print("=" * 60)
        print("\nTo fix duplicates:")
        print("1. Identify which user to keep (usually the one with more data)")
        print("2. If needed, migrate slots from duplicate to main user")
        print("3. Delete the duplicate user via API or Supabase dashboard")
        print("\nTo delete a user via API:")
        print("  DELETE http://127.0.0.1:8000/api/users/{user_id}")
        print("\nNote: Deleting a user will also delete all their slots and plans!")
    else:
        print("\nNo duplicates found. All users are unique.")

if __name__ == "__main__":
    main()

