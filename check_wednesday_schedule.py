"""Check if Wednesday has different schedule times than other days."""
import sys
from backend.database import get_db

def check_wednesday_schedule(user_id: str):
    """Check schedule entries for each day."""
    print(f"Checking schedule for user: {user_id}")
    print("=" * 80)
    
    db = get_db(user_id=user_id)
    schedule_entries = db.get_user_schedule(user_id)
    
    if not schedule_entries:
        print("No schedule entries found")
        return
    
    # Group by day
    by_day = {}
    for entry in schedule_entries:
        day = entry.day_of_week.lower()
        if day not in by_day:
            by_day[day] = []
        by_day[day].append({
            'slot_number': entry.slot_number,
            'subject': entry.subject,
            'start_time': entry.start_time,
            'end_time': entry.end_time,
        })
    
    # Show schedule for each day
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    for day in days:
        if day not in by_day:
            print(f"\n{day.upper()}: No schedule entries")
            continue
        
        entries = by_day[day]
        # Sort by slot_number
        entries.sort(key=lambda x: x['slot_number'])
        
        print(f"\n{day.upper()}:")
        for entry in entries:
            print(f"  Slot {entry['slot_number']} ({entry['subject']}): {entry['start_time']}-{entry['end_time']}")

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_wednesday_schedule(user_id)
