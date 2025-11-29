import requests
import json

def patch_slot_1():
    plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    
    # 1. Get Plan Detail
    url = f"http://localhost:8000/api/plans/{plan_id}"
    headers = {"X-Current-User-Id": user_id}
    
    print(f"Fetching plan from {url}...")
    response = requests.get(url, headers=headers)
    plan_data = response.json()
    lesson_json = plan_data.get("lesson_json", {})
    
    # 2. Get Slot 2 Data (which we know is good)
    monday_slots = lesson_json["days"]["monday"]["slots"]
    slot2_data = None
    for s in monday_slots:
        if s["slot_number"] == 2:
            slot2_data = s
            break
            
    if not slot2_data:
        print("Error: Could not find Slot 2 data to copy from.")
        return

    print("Found valid data in Slot 2.")
    vocab = slot2_data.get("vocabulary_cognates", [])
    frames = slot2_data.get("sentence_frames", [])
    
    print(f"Copying {len(vocab)} vocab items and {len(frames)} frames to Slot 1...")

    # 3. Update Slot 1 in local JSON
    for s in monday_slots:
        if s["slot_number"] == 1:
            s["vocabulary_cognates"] = vocab
            s["sentence_frames"] = frames
            print("Updated Slot 1 in memory.")
            break
            
    # 4. Save back to server
    # We need to use the update endpoint
    update_url = f"http://localhost:8000/api/plans/{plan_id}"
    
    # Minimal update payload - we just need to send the updated lesson_json
    update_data = {
        "lesson_json": lesson_json,
        "status": "completed" # Ensure it stays completed
    }
    
    print("Sending update to server...")
    update_response = requests.put(update_url, json=update_data, headers=headers)
    
    if update_response.status_code == 200:
        print("Success! Plan updated.")
        
        # 5. Trigger step regeneration for Slot 1
        gen_url = "http://localhost:8000/api/lesson-steps/generate"
        gen_params = {
            "plan_id": plan_id,
            "day": "monday",
            "slot": 1
        }
        print("Regenerating steps for Slot 1...")
        gen_response = requests.post(gen_url, params=gen_params, headers=headers)
        if gen_response.status_code == 200:
            print("Steps regenerated successfully.")
        else:
            print(f"Step regeneration failed: {gen_response.status_code}")
            
    else:
        print(f"Update failed: {update_response.status_code}")
        print(update_response.text)

if __name__ == "__main__":
    patch_slot_1()

