
import requests
import sys

def regenerate_steps():
    url = "http://localhost:8000/api/lesson-steps/generate"
    params = {
        "plan_id": "plan_20251122160826",
        "day": "monday",
        "slot": 1
    }
    headers = {
        "X-Current-User-Id": "04fe8898-cb89-4a73-affb-64a97a98f820"
    }
    
    print(f"Sending POST request to {url}...")
    try:
        response = requests.post(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(f"Response: {len(response.json())} steps generated")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    regenerate_steps()
