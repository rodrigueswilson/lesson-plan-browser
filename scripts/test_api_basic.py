#!/usr/bin/env python3
"""Basic API tests for user management."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_health():
    """Test API health endpoint."""
    print("[1/5] Testing API Health...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        r.raise_for_status()
        data = r.json()
        print(f"  [OK] API is healthy: {data['status']}")
        return True
    except Exception as e:
        print(f"  [FAIL] API health check failed: {e}")
        return False

def test_list_users():
    """Test listing users."""
    print("[2/5] Testing List Users...")
    try:
        r = requests.get(f"{BASE_URL}/users")
        r.raise_for_status()
        users = r.json()
        print(f"  [OK] Found {len(users)} users")
        for user in users:
            print(f"    - {user['name']} ({user.get('email', 'no email')})")
        return users
    except Exception as e:
        print(f"  [FAIL] Failed to list users: {e}")
        return []

def test_get_user(user_id):
    """Test getting a user by ID."""
    print(f"[3/5] Testing Get User by ID ({user_id[:8]}...)...")
    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}")
        r.raise_for_status()
        user = r.json()
        print(f"  [OK] Retrieved user: {user['name']}")
        return True
    except Exception as e:
        print(f"  [FAIL] Failed to get user: {e}")
        return False

def test_create_user():
    """Test creating a user."""
    print("[4/5] Testing Create User...")
    try:
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@example.com"
        }
        r = requests.post(f"{BASE_URL}/users", json=data)
        r.raise_for_status()
        user = r.json()
        print(f"  [OK] Created user: {user['name']} (ID: {user['id']})")
        
        # Clean up
        print("  Cleaning up test user...")
        try:
            requests.delete(f"{BASE_URL}/users/{user['id']}")
            print("  [OK] Test user deleted")
        except:
            print("  [WARN] Failed to delete test user")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Failed to create user: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"    Error details: {error_data}")
            except:
                print(f"    Error response: {e.response.text}")
        return False

def test_authorization(user_id):
    """Test authorization header."""
    print("[5/5] Testing Authorization...")
    try:
        headers = {"X-Current-User-Id": user_id}
        r = requests.get(f"{BASE_URL}/users/{user_id}", headers=headers)
        r.raise_for_status()
        print("  [OK] Authorization header accepted")
        return True
    except Exception as e:
        print(f"  [WARN] Authorization test: {e}")
        return False

if __name__ == "__main__":
    print("\n=== User Management Workflow Test ===\n")
    
    if not test_health():
        print("\n[FAIL] API is not available. Make sure FastAPI is running.")
        exit(1)
    
    users = test_list_users()
    
    if users:
        test_get_user(users[0]['id'])
        test_authorization(users[0]['id'])
    
    test_create_user()
    
    print("\n=== Test Complete ===\n")

