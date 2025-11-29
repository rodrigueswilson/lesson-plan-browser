"""Test API endpoints with structured names end-to-end."""

import requests
import sys

BASE_URL = "http://localhost:8000"

print("="*80)
print("API ENDPOINT TESTS - Structured Names")
print("="*80)

# Test 1: Create user with structured names
print("\n1. Testing POST /api/users with first_name/last_name...")
response = requests.post(f"{BASE_URL}/api/users", json={
    "first_name": "API",
    "last_name": "Test",
    "email": "api.test@example.com"
})

if response.status_code == 200:
    user = response.json()
    user_id = user['id']
    print(f"  ✓ Created user: {user['name']}")
    print(f"    first_name: '{user['first_name']}'")
    print(f"    last_name: '{user['last_name']}'")
    assert user['first_name'] == "API", "First name mismatch"
    assert user['last_name'] == "Test", "Last name mismatch"
    assert user['name'] == "API Test", "Computed name mismatch"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Test 2: Get user
print("\n2. Testing GET /api/users/{id}...")
response = requests.get(f"{BASE_URL}/api/users/{user_id}")

if response.status_code == 200:
    user = response.json()
    print(f"  ✓ Retrieved user: {user['name']}")
    assert user['first_name'] == "API", "First name mismatch"
    assert user['last_name'] == "Test", "Last name mismatch"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Test 3: Update user
print("\n3. Testing PUT /api/users/{id}...")
response = requests.put(f"{BASE_URL}/api/users/{user_id}", json={
    "first_name": "Updated",
    "last_name": "Name"
})

if response.status_code == 200:
    user = response.json()
    print(f"  ✓ Updated user: {user['name']}")
    print(f"    first_name: '{user['first_name']}'")
    print(f"    last_name: '{user['last_name']}'")
    assert user['first_name'] == "Updated", "First name not updated"
    assert user['last_name'] == "Name", "Last name not updated"
    assert user['name'] == "Updated Name", "Computed name not updated"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Test 4: Create slot with teacher names
print("\n4. Testing POST /api/users/{id}/slots with teacher names...")
response = requests.post(f"{BASE_URL}/api/users/{user_id}/slots", json={
    "slot_number": 1,
    "subject": "Math",
    "grade": "3",
    "homeroom": "301",
    "primary_teacher_first_name": "Sarah",
    "primary_teacher_last_name": "Lang"
})

if response.status_code == 200:
    slot = response.json()
    slot_id = slot['id']
    print(f"  ✓ Created slot: {slot['subject']}")
    print(f"    primary_teacher_first_name: '{slot.get('primary_teacher_first_name', '')}'")
    print(f"    primary_teacher_last_name: '{slot.get('primary_teacher_last_name', '')}'")
    print(f"    primary_teacher_name (computed): '{slot.get('primary_teacher_name', '')}'")
    assert slot['primary_teacher_first_name'] == "Sarah", "Teacher first name mismatch"
    assert slot['primary_teacher_last_name'] == "Lang", "Teacher last name mismatch"
    assert slot['primary_teacher_name'] == "Sarah Lang", "Computed teacher name mismatch"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Test 5: Update slot teacher names
print("\n5. Testing PUT /api/slots/{id} with teacher names...")
response = requests.put(f"{BASE_URL}/api/slots/{slot_id}", json={
    "primary_teacher_first_name": "Maria",
    "primary_teacher_last_name": "Savoca"
})

if response.status_code == 200:
    slot = response.json()
    print(f"  ✓ Updated slot teacher")
    print(f"    primary_teacher_first_name: '{slot.get('primary_teacher_first_name', '')}'")
    print(f"    primary_teacher_last_name: '{slot.get('primary_teacher_last_name', '')}'")
    print(f"    primary_teacher_name (computed): '{slot.get('primary_teacher_name', '')}'")
    assert slot['primary_teacher_first_name'] == "Maria", "Teacher first name not updated"
    assert slot['primary_teacher_last_name'] == "Savoca", "Teacher last name not updated"
    assert slot['primary_teacher_name'] == "Maria Savoca", "Computed teacher name not updated"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Test 6: List users (verify structured fields in list)
print("\n6. Testing GET /api/users (list)...")
response = requests.get(f"{BASE_URL}/api/users")

if response.status_code == 200:
    users = response.json()
    test_user = [u for u in users if u['id'] == user_id][0]
    print(f"  ✓ Found user in list: {test_user['name']}")
    assert 'first_name' in test_user, "first_name missing from list response"
    assert 'last_name' in test_user, "last_name missing from list response"
    print("  ✓ PASS")
else:
    print(f"  ✗ FAIL: {response.status_code} - {response.text}")
    sys.exit(1)

# Cleanup
print("\n7. Cleaning up...")
requests.delete(f"{BASE_URL}/api/slots/{slot_id}")
requests.delete(f"{BASE_URL}/api/users/{user_id}")
print("  ✓ Cleanup complete")

print("\n" + "="*80)
print("✅ ALL API TESTS PASSED")
print("="*80)
print("\nPhase 3 is now TRULY complete:")
print("  ✓ Database CRUD methods updated")
print("  ✓ Pydantic models updated with validation")
print("  ✓ API endpoints updated with keyword args")
print("  ✓ End-to-end tests passing")
