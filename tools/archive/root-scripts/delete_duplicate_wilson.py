"""
Delete the duplicate Wilson Rodrigues user.

This script deletes the duplicate Wilson user created during testing,
keeping the original one that has the Math slot.
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

# The duplicate user ID (created during test)
DUPLICATE_USER_ID = "2721e7df-a5d7-4c78-ba41-b9caad4c51bd"

# The original user ID (has the Math slot)
ORIGINAL_USER_ID = "8d3154dc-1d16-4b9c-9b30-07397630465e"

def main():
    print("=" * 60)
    print("Deleting Duplicate Wilson Rodrigues User")
    print("=" * 60)
    
    # Verify the duplicate exists
    print(f"\nChecking duplicate user: {DUPLICATE_USER_ID}")
    try:
        response = requests.get(f"{BASE_URL}/api/users/{DUPLICATE_USER_ID}", timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f"Found: {user.get('name')} ({user.get('email')})")
        else:
            print(f"User not found (status: {response.status_code})")
            print("Duplicate may have already been deleted.")
            return 0
    except Exception as e:
        print(f"Error checking user: {e}")
        return 1
    
    # Verify original exists
    print(f"\nChecking original user: {ORIGINAL_USER_ID}")
    try:
        response = requests.get(f"{BASE_URL}/api/users/{ORIGINAL_USER_ID}", timeout=10)
        if response.status_code == 200:
            user = response.json()
            slots_response = requests.get(f"{BASE_URL}/api/users/{ORIGINAL_USER_ID}/slots", timeout=10)
            slots_count = len(slots_response.json()) if slots_response.status_code == 200 else 0
            print(f"Found: {user.get('name')} ({user.get('email')})")
            print(f"Has {slots_count} slot(s) - this is the one to keep")
        else:
            print(f"ERROR: Original user not found!")
            return 1
    except Exception as e:
        print(f"Error checking original user: {e}")
        return 1
    
    # Confirm deletion
    print("\n" + "=" * 60)
    print("WARNING: This will delete the duplicate user and ALL associated data!")
    print("=" * 60)
    print(f"\nWill delete: {DUPLICATE_USER_ID}")
    print(f"Will keep: {ORIGINAL_USER_ID}")
    
    confirm = input("\nType 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("Cancelled.")
        return 0
    
    # Delete the duplicate
    print(f"\nDeleting duplicate user...")
    try:
        response = requests.delete(f"{BASE_URL}/api/users/{DUPLICATE_USER_ID}", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] {result.get('message', 'User deleted successfully')}")
            
            # Verify deletion
            print("\nVerifying deletion...")
            verify_response = requests.get(f"{BASE_URL}/api/users/{DUPLICATE_USER_ID}", timeout=10)
            if verify_response.status_code == 404:
                print("[OK] Duplicate user successfully deleted")
            else:
                print("[WARN] User may still exist (status: {verify_response.status_code})")
            
            # List remaining users
            print("\nRemaining users:")
            users_response = requests.get(f"{BASE_URL}/api/users", timeout=10)
            if users_response.status_code == 200:
                users = users_response.json()
                for user in users:
                    name = user.get('name', '') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                    print(f"  - {name} ({user.get('id')})")
            
            return 0
        else:
            print(f"[ERROR] Failed to delete user: {response.status_code}")
            print(f"Response: {response.text}")
            return 1
    except Exception as e:
        print(f"[ERROR] Error deleting user: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

