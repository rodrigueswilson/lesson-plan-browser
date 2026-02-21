
import json

def inspect_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # The file might contain sqlite output formatting (escaping, etc.)
        # But since I redirected stdout, it should be the raw string.
        # However, SQLite might wrap it or escape it.
        try:
            # Try parsing directly
            data = json.loads(content)
        except Exception:
            # sqlite3 redirect might include some noise or be formatted
            # Let's try to find the JSON start
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(content[start:end])
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    return
            else:
                print("No JSON found in file.")
                return

    days = data.get('days', {})
    monday = days.get('monday', {})
    slots = monday.get('slots', [])
    
    print(f"Plan Metadata: {data.get('metadata', {})}")
    print(f"\nMonday Slots ({len(slots)}):")
    for i, slot in enumerate(slots):
        print(f"Slot {i+1}:")
        print(f"  Slot Number: {slot.get('slot_number')}")
        print(f"  Subject: {slot.get('subject')}")
        print(f"  Start Time: {slot.get('start_time')}")
        print(f"  End Time: {slot.get('end_time')}")
        print(f"  Unit Lesson: {slot.get('unit_lesson', '')[:50]}...")

if __name__ == "__main__":
    inspect_json('d:/LP/plan_content.json')
