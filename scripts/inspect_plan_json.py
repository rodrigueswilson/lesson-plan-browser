import requests
import json

def inspect_plan_data():
    plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    
    # 1. Get Plan Detail
    url = f"http://localhost:8000/api/plans/{plan_id}"
    headers = {"X-Current-User-Id": user_id}
    
    print(f"Fetching plan from {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching plan: {response.status_code}")
        return

    plan_data = response.json()
    lesson_json = plan_data.get("lesson_json", {})
    
    # 2. Inspect Monday Slot 1
    monday_data = lesson_json.get("days", {}).get("monday", {})
    slots = monday_data.get("slots", [])
    
    print(f"\n--- Monday Data Analysis ---")
    print(f"Total Slots: {len(slots)}")
    
    # Find Slot 1
    slot1 = None
    for s in slots:
        if s.get("slot_number") == 1:
            slot1 = s
            break
            
    if slot1:
        print("\n--- Slot 1 Data ---")
        vocab = slot1.get("vocabulary_cognates")
        frames = slot1.get("sentence_frames")
        
        print(f"Vocabulary present: {bool(vocab)}")
        print(f"Vocabulary type: {type(vocab)}")
        print(f"Vocabulary count: {len(vocab) if isinstance(vocab, list) else 'N/A'}")
        if vocab:
            print(json.dumps(vocab, indent=2))
            
        print(f"\nSentence Frames present: {bool(frames)}")
        print(f"Frames type: {type(frames)}")
        print(f"Frames count: {len(frames) if isinstance(frames, list) else 'N/A'}")
        if frames:
            print(json.dumps(frames, indent=2))
    else:
        print("Slot 1 not found!")

if __name__ == "__main__":
    inspect_plan_data()

