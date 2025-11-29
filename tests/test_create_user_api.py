"""Test creating a user via API to verify it works."""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Create User API...")
print("=" * 60)

# Create a test user
test_user = {
    "name": "weqwewq",
    "email": "asdeswilson@gmail.com"
}

print(f"Creating user: {test_user}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/users",
        json=test_user,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        user = response.json()
        print("✓ User created successfully!")
        print(f"  ID: {user['id']}")
        print(f"  Name: {user['name']}")
        print(f"  Email: {user['email']}")
        print()
        print("Full response:")
        print(json.dumps(user, indent=2))
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("If this works, the backend API is fine.")
print("The issue is in how Tauri is calling it.")
