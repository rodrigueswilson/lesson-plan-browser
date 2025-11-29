"""Test API connection and endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Testing API Connection")
print("=" * 70)
print()

# Test 1: Health check
print("1. Testing Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    if response.status_code == 200:
        print(f"   ✓ Health check passed: {response.json()}")
    else:
        print(f"   ✗ Health check failed: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("   ✗ Cannot connect to backend!")
    print("   Make sure the backend is running: python -m uvicorn backend.api:app --reload")
    exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print()

# Test 2: List users
print("2. Testing List Users Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/users", timeout=5)
    if response.status_code == 200:
        users = response.json()
        print(f"   ✓ Found {len(users)} users")
        for user in users[:5]:  # Show first 5
            print(f"     - {user['name']} ({user['id'][:8]}...)")
        if len(users) > 5:
            print(f"     ... and {len(users) - 5} more")
    else:
        print(f"   ✗ Failed: {response.status_code}")
        print(f"     {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test 3: Create user
print("3. Testing Create User Endpoint...")
try:
    test_user = {
        "name": "API Test User",
        "email": "apitest@example.com"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/users",
        json=test_user,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"   ✓ User created successfully!")
        print(f"     ID: {user['id'][:8]}...")
        print(f"     Name: {user['name']}")
        print(f"     Email: {user['email']}")
    else:
        print(f"   ✗ Failed: {response.status_code}")
        print(f"     {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test 4: CORS headers
print("4. Testing CORS Headers...")
try:
    response = requests.options(
        f"{BASE_URL}/api/users",
        headers={"Origin": "tauri://localhost"},
        timeout=5
    )
    
    cors_headers = {
        k: v for k, v in response.headers.items() 
        if k.lower().startswith('access-control')
    }
    
    if cors_headers:
        print("   ✓ CORS headers present:")
        for header, value in cors_headers.items():
            print(f"     {header}: {value}")
    else:
        print("   ⚠️  No CORS headers found")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()
print("=" * 70)
print("API Connection Test Complete")
print("=" * 70)
print()
print("If all tests passed, the backend is working correctly.")
print("If the frontend can't connect, check:")
print("  1. Backend is running on port 8000")
print("  2. Frontend is configured to use http://localhost:8000")
print("  3. CORS settings allow tauri://localhost")
print()
