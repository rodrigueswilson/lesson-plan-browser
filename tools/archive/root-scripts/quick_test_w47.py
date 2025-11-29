"""Quick test - generate W47 plan for Wilson Rodrigues"""
import requests
import json

API = "http://localhost:8000/api"

# Get users
users = requests.get(f"{API}/users").json()
wilson = next((u for u in users if 'wilson' in u.get('first_name', '').lower() and 'rodrigues' in u.get('last_name', '').lower()), None)

if not wilson:
    print("Wilson Rodrigues not found")
    exit(1)

print(f"Found: {wilson['id']} - {wilson['first_name']} {wilson['last_name']}")

# Get slots
slots = requests.get(f"{API}/users/{wilson['id']}/slots").json()
slot_ids = [s['id'] for s in slots]
print(f"Slots: {len(slot_ids)}")

# Generate W47
result = requests.post(f"{API}/process-week", json={
    "user_id": wilson['id'],
    "week_of": "W47",
    "provider": "openai",
    "slot_ids": slot_ids
}).json()

print(f"Result: {json.dumps(result, indent=2)}")

