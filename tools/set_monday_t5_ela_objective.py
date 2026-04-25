#!/usr/bin/env python3
"""
Set the Monday ELA (Kelsey Lang) student_goal to the first version:
  I will describe rhyme and rhythm in a poem (reading, writing).

Matches Monday + ELA + Kelsey Lang (slot 1 in the data). Updates the plan
in the main DB. Run from project root. After running, re-export to tablet
from the app so the tablet gets the updated plan.

Usage:
  python tools/set_monday_t5_ela_objective.py [--plan-id PLAN_ID] [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from backend.config import settings
from backend.services.objectives_utils import normalize_objectives_in_lesson

TARGET_STUDENT_GOAL = "I will describe rhyme and rhythm in a poem (reading, writing)."
USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"
WEEK_OF = "03-02-03-06"
DEFAULT_PLAN_ID = "plan_20260228104538_fe3ce909"


def main() -> int:
    parser = argparse.ArgumentParser(description="Set Monday T5 ELA student_goal to first version.")
    parser.add_argument("--plan-id", default=DEFAULT_PLAN_ID, help="Plan ID to update.")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be changed.")
    args = parser.parse_args()

    db_path = Path(settings.SQLITE_DB_PATH).resolve()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, lesson_json FROM weekly_plans WHERE id = ?", (args.plan_id,)
    ).fetchone()
    if not row:
        print(f"Plan not found: {args.plan_id}")
        conn.close()
        return 1

    lesson_json = row["lesson_json"]
    if isinstance(lesson_json, str):
        lesson_json = json.loads(lesson_json)
    if not lesson_json or "days" not in lesson_json:
        print("Plan has no lesson_json or days.")
        conn.close()
        return 1

    days = lesson_json["days"]
    monday = days.get("monday") if isinstance(days, dict) else None
    if not monday or not isinstance(monday, dict):
        print("No monday in days.")
        conn.close()
        return 1

    slots = monday.get("slots")
    if not isinstance(slots, list):
        print("Monday has no slots list.")
        conn.close()
        return 1

    updated = False
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        subject = (slot.get("subject") or "").strip().upper()
        teacher = (slot.get("teacher_name") or slot.get("primary_teacher_name") or "").strip()
        if "ELA" not in subject and "LANGUAGE" not in subject:
            continue
        if "KELSEY" not in teacher.upper():
            continue
        obj = slot.get("objective") or {}
        if not isinstance(obj, dict):
            obj = {}
        old_goal = (obj.get("student_goal") or "").strip()
        if old_goal == TARGET_STUDENT_GOAL:
            print(f"Monday ELA (Kelsey Lang) already has the target student_goal.")
            conn.close()
            return 0
        slot["objective"] = {**obj, "student_goal": TARGET_STUDENT_GOAL}
        if "content_objective" not in slot["objective"] or not slot["objective"]["content_objective"]:
            slot["objective"]["content_objective"] = obj.get("content_objective") or "Students will describe rhyme and rhythm in a poem."
        if "wida_objective" not in slot["objective"] or not slot["objective"]["wida_objective"]:
            slot["objective"]["wida_objective"] = obj.get("wida_objective") or ""
        updated = True
        print(f"Monday ELA Kelsey Lang (slot_number={slot.get('slot_number')}):")
        print(f"  Old student_goal: {old_goal or '(empty)'}")
        print(f"  New student_goal: {TARGET_STUDENT_GOAL}")
        break

    if not updated:
        print("No matching Monday ELA / Kelsey Lang slot found. Slots on Monday:")
        for slot in slots:
            if isinstance(slot, dict):
                print(f"  slot_number={slot.get('slot_number')} subject={slot.get('subject')} teacher={slot.get('teacher_name') or slot.get('primary_teacher_name')}")
        conn.close()
        return 1

    normalize_objectives_in_lesson(lesson_json)

    if args.dry_run:
        print("\n[DRY RUN] No changes written. Run without --dry-run to update the database.")
        conn.close()
        return 0

    conn.execute(
        "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?",
        (json.dumps(lesson_json), args.plan_id),
    )
    conn.commit()
    conn.close()
    print("\nPlan updated. Re-export to tablet from the app to send the change to the tablet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
