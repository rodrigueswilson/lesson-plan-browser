import json
import os

def parse_and_check():
    path = r'd:\LP\latest_lesson.json'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        lesson = json.load(f)
    
    days = lesson.get('days', {})
    friday = days.get('friday', {})
    slots = friday.get('slots', [])
    
    print("Friday Math Slots:")
    for s in slots:
        subject = s.get('subject', '')
        if 'Math' in str(subject):
            grade = s.get('grade', '')
            homeroom = s.get('homeroom', '')
            start_time = s.get('start_time', '')
            slot_num = s.get('slot_number', '')
            print(f"  {subject} | Grade {grade} | {homeroom} | {start_time} | Slot {slot_num}")

if __name__ == "__main__":
    parse_and_check()
