import requests
import json

def inspect_steps():
    url = "http://localhost:8000/api/lesson-steps/generate"
    params = {
        "plan_id": "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0",
        "day": "monday",
        "slot": 1
    }
    headers = {
        "X-Current-User-Id": "04fe8898-cb89-4a73-affb-64a97a98f820"
    }
    
    print(f"Fetching steps from {url}...")
    try:
        response = requests.post(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Successfully retrieved {len(data)} steps.")
            print("\n--- Full Step Data ---")
            print(json.dumps(data, indent=2))
            
            print("\n--- Analysis ---")
            vocab_steps = [s for s in data if s.get('vocabulary_cognates')]
            frames_steps = [s for s in data if s.get('sentence_frames')]
            
            print(f"Steps with vocabulary_cognates: {len(vocab_steps)}")
            for s in vocab_steps:
                print(f"  - Step ID: {s.get('id')}")
                print(f"  - Content Type: {s.get('content_type')}")
                print(f"  - Vocab Count: {len(s.get('vocabulary_cognates', []))}")
                
            print(f"Steps with sentence_frames: {len(frames_steps)}")
            for s in frames_steps:
                print(f"  - Step ID: {s.get('id')}")
                print(f"  - Content Type: {s.get('content_type')}")
                print(f"  - Frames Count: {len(s.get('sentence_frames', []))}")
                
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    inspect_steps()

