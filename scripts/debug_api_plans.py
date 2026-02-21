import requests
import json

user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
url = f"http://localhost:8000/api/users/{user_id}/plans"
headers = {
    "X-Current-User-Id": user_id,
    "Content-Type": "application/json"
}

try:
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        plans = response.json()
        print(f"Plan Count: {len(plans)}")
        # print first few IDs to verify
        for p in plans[:3]:
           print(f" - Plan {p.get('id')} User: {p.get('user_id')} Week: {p.get('week_of')}")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Failed to connect: {e}")
