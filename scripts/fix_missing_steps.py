
import requests
import sys

API_BASE = "http://localhost:8000/api"
PLAN_ID = "plan_20251228152714"
USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820" # Wilson
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
SLOTS = [1, 2, 3, 4, 5]

def regenerate_all_steps():
    print(f"--- Regenerating Steps for Plan: {PLAN_ID} ---")
    
    success_count = 0
    fail_count = 0

    for day in DAYS:
        for slot in SLOTS:
            url = f"{API_BASE}/lesson-steps/generate"
            params = {
                "plan_id": PLAN_ID,
                "day": day,
                "slot": slot
            }
            # Add force flag if endpoint supports it, but standard flow should just work if missing
            headers = {
                "X-Current-User-Id": USER_ID
            }
            
            print(f"Generating {day} slot {slot}...", end=" ")
            try:
                resp = requests.post(url, params=params, headers=headers)
                if resp.status_code == 200:
                    steps = resp.json()
                    print(f"OK ({len(steps)} steps)")
                    success_count += 1
                else:
                    print(f"FAIL ({resp.status_code}): {resp.text}")
                    fail_count += 1
            except Exception as e:
                print(f"ERROR: {e}")
                fail_count += 1

    print(f"\nFinished. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    regenerate_all_steps()
