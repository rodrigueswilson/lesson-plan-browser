import requests
import json

def check_api():
    url = "http://localhost:8000/api/lesson-steps/plan_20251228152714/wednesday/6"
    headers = {"X-Current-User-Id": "04fe8898-cb89-4a73-affb-64a97a98f820"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        steps = response.json()
        
        print(f"--- API Response for Science (Wed, Slot 6) ---")
        for step in steps:
            name = step.get("step_name")
            if "Sentence Frames" in name:
                frames = step.get("sentence_frames")
                if isinstance(frames, str):
                    frames = json.loads(frames)
                
                print(f"Step: {name}")
                for i, frame in enumerate(frames):
                    eng = frame.get("english", "")
                    pt = frame.get("portuguese", "")
                    print(f"  Frame {i+1} ENG: '{eng[-1]}' | PT: '{pt[-1]}'")
                    if not eng.endswith(".") and not eng.endswith("?"):
                        print(f"    MISSING PUNCTUATION in ENG: {eng}")
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    check_api()
