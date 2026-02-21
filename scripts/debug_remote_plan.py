
import requests
import json
import sys

API_BASE = "http://localhost:8000/api"
PLAN_ID = "plan_20251228152714"
USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820" # Wilson

def check_remote_plan():
    print(f"--- Checking Remote Plan: {PLAN_ID} ---")
    
    # 1. Get Plan Detail
    url = f"{API_BASE}/plans/{PLAN_ID}"
    print(f"GET {url}")
    try:
        resp = requests.get(url, headers={"X-Current-User-Id": USER_ID})
        resp.raise_for_status()
        data = resp.json()
        print(f"Status: {data.get('status')}")
        print(f"Total Slots: {data.get('total_slots')}")
        
        lj = data.get('lesson_json')
        if lj:
            days = lj.get('days', {})
            print(f"JSON Days: {list(days.keys())}")
            for d, d_data in days.items():
                print(f"  {d}: {len(d_data.get('slots', []))} JSON slots")
    except Exception as e:
        print(f"ERROR fetching plan: {e}")
        return

    # 2. Get Steps
    # We need to guess the day/slot to query steps, or query all.
    # We'll try Monday Slot 1
    day = "monday"
    slot = 1
    url_steps = f"{API_BASE}/lesson-steps/{PLAN_ID}/{day}/{slot}"
    print(f"\nGET {url_steps}")
    try:
        resp = requests.get(url_steps, headers={"X-Current-User-Id": USER_ID})
        resp.raise_for_status()
        steps = resp.json()
        print(f"Steps returned: {len(steps)}")
        for s in steps:
            print(f"  - [{s.get('step_number')}] {s.get('step_name')} ({s.get('content_type')})")
    except Exception as e:
        print(f"ERROR fetching steps: {e}")

if __name__ == "__main__":
    check_remote_plan()
