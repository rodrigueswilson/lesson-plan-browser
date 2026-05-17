"""
Find which of the two weekly_plans for week_of '02-23-02-27' contains the given
student_goal text (e.g. on ELA, Kelsey, Monday). Returns the plan id to KEEP;
the other should be deleted.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import settings
import sqlite3

# ELA poem goal: exact or partial (poem + reading, writing)
TARGET_GOAL = "I will read and write about the poem (reading, writing)."
TARGET_PARTIALS = ("read and write about the poem", "poems use repetition (reading, writing)")
# Prefer exact goal so we identify the plan to KEEP (with "read and write about the poem")
WEEK_OF = "02-23-02-27"
PLAN_IDS = ("plan_20260220172447", "plan_20260220174959")


def search_json(obj, target: str, path: str = "") -> bool:
    """Return True if target string appears anywhere in obj (dict/list/str)."""
    if isinstance(obj, str):
        return target in obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            if search_json(v, target, f"{path}.{k}"):
                return True
        return False
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            if search_json(v, target, f"{path}[{i}]"):
                return True
        return False
    return False


def main():
    p = Path(settings.SQLITE_DB_PATH).resolve()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        "SELECT id, user_id, week_of, generated_at, lesson_json FROM weekly_plans WHERE week_of = ? ORDER BY generated_at ASC",
        (WEEK_OF,),
    )
    rows = c.fetchall()
    conn.close()

    if len(rows) != 2:
        print(f"Expected 2 plans for week_of={WEEK_OF}, got {len(rows)}", file=sys.stderr)
        sys.exit(1)

    for row in rows:
        plan_id = row["id"]
        lesson_json_raw = row["lesson_json"]
        if lesson_json_raw is None:
            continue
        if isinstance(lesson_json_raw, str):
            try:
                lesson_json = json.loads(lesson_json_raw)
            except json.JSONDecodeError:
                continue
        else:
            lesson_json = lesson_json_raw

        if search_json(lesson_json, TARGET_GOAL):
            print(plan_id)
            return
        for partial in TARGET_PARTIALS:
            if search_json(lesson_json, partial):
                print(plan_id)
                return

    # Debug: list all student_goal values from Monday slots
    for row in rows:
        plan_id = row["id"]
        lesson_json_raw = row["lesson_json"]
        if lesson_json_raw is None:
            continue
        if isinstance(lesson_json_raw, str):
            try:
                lesson_json = json.loads(lesson_json_raw)
            except json.JSONDecodeError:
                continue
        else:
            lesson_json = lesson_json_raw
        monday = (lesson_json or {}).get("days", {}).get("monday", {})
        slots = monday.get("slots", [])
        for s in slots if isinstance(slots, list) else []:
            if not isinstance(s, dict):
                continue
            obj = s.get("objectives") or s.get("objective")
            if isinstance(obj, dict) and "student_goal" in obj:
                print(f"[{plan_id}] slot {s.get('slot_number')} student_goal: {obj['student_goal'][:80]!r}", file=sys.stderr)
            if isinstance(obj, list):
                for o in obj:
                    if isinstance(o, dict) and o.get("student_goal"):
                        print(f"[{plan_id}] student_goal: {o['student_goal'][:80]!r}", file=sys.stderr)

    print("NOT_FOUND", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
