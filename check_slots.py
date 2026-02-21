import json

def check_slots():
    with open('d:/LP/latest_lesson.json', 'r') as f:
        data = json.load(f)
    
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day in day_names:
        slots = data['days'].get(day, {}).get('slots', [])
        for slot in slots:
            if slot.get('slot_number') == 6:
                obj = slot.get('objective', {})
                print(f"{day.capitalize()} Slot 6:")
                print(f"  Unit: {slot.get('unit_lesson')}")
                print(f"  Obj: {obj}")
                
if __name__ == '__main__':
    check_slots()
