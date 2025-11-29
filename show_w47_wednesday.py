import sqlite3
import json
from pathlib import Path

DB = Path('data/lesson_planner.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

week = 'W47'
cur.execute(
    "SELECT id, lesson_json FROM weekly_plans WHERE week_of=? ORDER BY generated_at DESC LIMIT 1",
    (week,)
)
row = cur.fetchone()
if not row:
    print('No plan found for week', week)
    raise SystemExit(0)

plan_id, lesson_json = row
print('Plan ID:', plan_id)
if not lesson_json:
    print('No lesson_json stored')
    raise SystemExit(0)

data = json.loads(lesson_json)
wed = data.get('days', {}).get('wednesday')
if not wed:
    print('No Wednesday data in lesson_json')
    raise SystemExit(0)

slots = wed.get('slots', [])
for idx, slot in enumerate(slots):
    start = slot.get('start_time')
    end = slot.get('end_time')
    subject = slot.get('subject')
    grade = slot.get('grade')
    homeroom = slot.get('homeroom')
    slot_num = slot.get('slot_number')
    print(f"[{idx}] Slot {slot_num}: {subject} Grade {grade} {homeroom} {start}-{end}")
    objective = slot.get('objective', {})
    if objective:
        print('   Student goal:', objective.get('student_goal'))
        print('   WIDA:', objective.get('wida_objective'))
    tailored = slot.get('tailored_instruction', {})
    if isinstance(tailored, dict) and tailored.get('original_content'):
        print('   Tailored:', tailored.get('original_content'))
    print('---')
