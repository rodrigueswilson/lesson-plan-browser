
import json
from pathlib import Path

def inspect_times():
    json_path = Path("d:/LP/latest_lesson.json")
    if not json_path.exists():
        print("latest_lesson.json not found")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Week: {data.get('metadata', {}).get('week_of')}")
    
    if 'days' not in data:
        print("No 'days' key found")
        return

    for day_name, day_data in data['days'].items():
        print(f"\n--- {day_name.upper()} ---")
        if 'slots' in day_data:
            for i, slot in enumerate(day_data['slots']):
                print(f"Slot {slot.get('slot_number', '?')} ({slot.get('subject')}): {slot.get('start_time')} - {slot.get('end_time')}")
        else:
            print("No 'slots' array/list found (flattened?)")
            print(f"Start time: {day_data.get('start_time')}")

if __name__ == "__main__":
    inspect_times()
