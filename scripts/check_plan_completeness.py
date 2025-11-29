import requests
import json

def check_entire_plan():
    plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    
    url = f"http://localhost:8000/api/plans/{plan_id}"
    headers = {"X-Current-User-Id": user_id}
    
    print(f"Fetching plan {plan_id}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    plan_data = response.json()
    lesson_json = plan_data.get("lesson_json", {})
    days = lesson_json.get("days", {})
    
    print(f"Week: {plan_data.get('week_of')}")
    
    for day_name, day_data in days.items():
        slots = day_data.get("slots", [])
        print(f"\n{day_name.upper()} ({len(slots)} slots):")
        
        for slot in slots:
            s_num = slot.get("slot_number")
            vocab = slot.get("vocabulary_cognates")
            frames = slot.get("sentence_frames")
            
            has_vocab = bool(vocab and len(vocab) > 0)
            has_frames = bool(frames and len(frames) > 0)
            
            status = "[OK]" if has_vocab and has_frames else "[MISSING]"
            print(f"  Slot {s_num}: Vocab={has_vocab}, Frames={has_frames} -> {status}")

if __name__ == "__main__":
    check_entire_plan()
