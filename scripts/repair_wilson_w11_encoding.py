"""
One-time repair of Wilson Rodrigues Week 11 lesson_json encoding corruption.

Removes NULL/control chars from all strings and applies known bad->correct
string fixes for vocabulary_cognates and sentence_frames. Use --dry-run to
preview without writing.
"""

import argparse
import json
import sqlite3
import sys
from copy import deepcopy
from pathlib import Path

# Ensure project root is on path for backend/tools imports
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.docx_renderer.style import sanitize_xml_text

# Known bad -> correct (Portuguese/vocab and sentence frame strings)
_KNOWN_FIXES = [
    ("evideancia", "evidência"),
    ("evideAncia", "evidência"),
    ("histf3ria", "história"),
    ("ninada", "ninhada"),
    ("care1ter", "carácter"),
    ("car\u0000e1ter", "carácter"),
]
# Word-boundary style: " e9 " -> " é ", "Isto e9 " -> "Isto é "
_E9_FIX = (" e9 ", " é ")
_E9_FIX_START = ("Isto e9 ", "Isto é ")


def get_db_path() -> Path:
    """SQLite DB path under project root (same as extract script)."""
    return (_ROOT / "data" / "lesson_planner.db").absolute()


def fetch_user_id(conn: sqlite3.Connection, name: str) -> str | None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
    row = cursor.fetchone()
    return str(row[0]) if row else None


def fetch_weekly_plans_for_user(conn: sqlite3.Connection, user_id: str, limit: int = 50):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, week_of, lesson_json
        FROM weekly_plans
        WHERE user_id = ?
        ORDER BY generated_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    return [
        {"id": plan_id, "week_of": week_of, "lesson_json": raw}
        for plan_id, week_of, raw in cursor.fetchall()
    ]


def is_week_11(week_of: str) -> bool:
    if not week_of:
        return False
    text = week_of.strip().lower()
    candidates = ["w11", "week 11", "03-09", "03/09", "03-09-03-13", "03/09-03/13"]
    return any(t in text for t in candidates)


def _walk_strings(obj, fn):
    """Apply fn to every string value in obj (mutates in place)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                obj[k] = fn(v)
            else:
                _walk_strings(v, fn)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                obj[i] = fn(item)
            else:
                _walk_strings(item, fn)


def _apply_known_fixes(s: str) -> str:
    out = s
    for bad, good in _KNOWN_FIXES:
        out = out.replace(bad, good)
    out = out.replace(_E9_FIX_START[0], _E9_FIX_START[1])
    out = out.replace(_E9_FIX[0], _E9_FIX[1])
    return out


def repair_lesson_json_encoding(lesson: dict) -> dict:
    """
    Pass 1: strip NULL and control chars from all strings.
    Pass 2: apply known bad->correct string fixes to all string values.
    Returns a new dict (does not mutate input).
    """
    repaired = deepcopy(lesson)

    def pass1(s: str) -> str:
        return sanitize_xml_text(s)

    def pass2(s: str) -> str:
        return _apply_known_fixes(s)

    _walk_strings(repaired, pass1)
    _walk_strings(repaired, pass2)
    return repaired


def main():
    parser = argparse.ArgumentParser(description="Repair Wilson W11 lesson_json encoding.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write; print what would be updated.")
    args = parser.parse_args()

    db_path = get_db_path()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        user_id = fetch_user_id(conn, "Wilson Rodrigues")
        if not user_id:
            print("User 'Wilson Rodrigues' not found.")
            return 1

        plans = fetch_weekly_plans_for_user(conn, user_id)
        w11_plans = [p for p in plans if is_week_11(str(p.get("week_of") or ""))]
        if not w11_plans:
            print("No Week 11 plans found for Wilson Rodrigues.")
            return 0

        updates = []
        for p in w11_plans:
            plan_id = p["id"]
            raw = p["lesson_json"]
            if isinstance(raw, str):
                try:
                    lesson = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(f"Skip plan {plan_id}: invalid JSON ({e})")
                    continue
            elif isinstance(raw, dict):
                lesson = raw
            else:
                continue

            repaired = repair_lesson_json_encoding(lesson)
            if repaired != lesson:
                updates.append((plan_id, p.get("week_of"), repaired))

        if not updates:
            print("No plans needed repair.")
            return 0

        print(f"Plans that would be updated: {len(updates)}")
        for plan_id, week_of, repaired in updates:
            print(f"  {plan_id} (week_of={week_of})")

        if args.dry_run:
            print("\n[DRY RUN] No changes written. Run without --dry-run to update the database.")
            return 0

        try:
            from backend.services.objectives_utils import normalize_objectives_in_lesson
        except ImportError:
            normalize_objectives_in_lesson = None

        cursor = conn.cursor()
        for plan_id, _week_of, repaired in updates:
            if normalize_objectives_in_lesson:
                normalize_objectives_in_lesson(repaired)
            cursor.execute(
                "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?",
                (json.dumps(repaired, ensure_ascii=False), plan_id),
            )
        conn.commit()
        print(f"\nUpdated {len(updates)} plan(s).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
