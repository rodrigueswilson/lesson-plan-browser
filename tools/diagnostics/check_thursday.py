from backend.database import SQLiteDatabase
db = SQLiteDatabase()
user = db.get_user_by_name('Wilson Rodrigues')
plan = db.get_user_plans(user.id, limit=1)[0]
lesson = plan.lesson_json
thursday = lesson['days']['thursday']
print("Thursday slots in lesson_json:")
for i, slot in enumerate(thursday['slots']):
    print(f"{i}: slot_number={slot['slot_number']} subject={slot['subject']}")
    print(f"   student_goal: {slot.get('objective', {}).get('student_goal', 'N/A')[:80]}")
print("\nThursday schedule entries:")
entries = [e for e in db.get_schedule_entries(user.id) if e.day_of_week=='thursday']
for e in sorted(entries, key=lambda x: x.slot_number):
    print(f"slot {e.slot_number}: {e.subject}")
