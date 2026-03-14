"""
Diagnose Wilson W11 lesson_json encoding: inspect raw bytes of Portuguese
field values to verify whether corruption is "UTF-8 saved, read as ANSI"
or literal hex substitution (e7, e3, ...) stored as ASCII.

Run from project root: python scripts/diagnose_wilson_w11_encoding.py
"""

import json
import sqlite3
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def get_db_path() -> Path:
    return (_ROOT / "data" / "lesson_planner.db").absolute()


def is_week_11(week_of: str) -> bool:
    if not week_of:
        return False
    text = week_of.strip().lower()
    candidates = ["w11", "week 11", "03-09", "03/09", "03-09-03-13", "03/09-03/13"]
    return any(t in text for t in candidates)


def find_portuguese_strings_with_hex_pattern(obj, path: str = ""):
    """Yield (path, value) for string values under 'portuguese' key that contain e7/e3/etc."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, str):
                if k == "portuguese" and any(
                    x in v.lower() for x in ("e7", "e3", "e9", "trae7o", "conspirae7e3o")
                ):
                    yield (p, v)
            else:
                yield from find_portuguese_strings_with_hex_pattern(v, p)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from find_portuguese_strings_with_hex_pattern(item, f"{path}[{i}]")


def main():
    db_path = get_db_path()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id FROM users WHERE name = ?", ("Wilson Rodrigues",)
        )
        row = cur.fetchone()
        if not row:
            print("User 'Wilson Rodrigues' not found.")
            return 1
        user_id = row[0]

        cur = conn.execute(
            """
            SELECT id, week_of, lesson_json
            FROM weekly_plans
            WHERE user_id = ?
            ORDER BY generated_at DESC
            LIMIT 50
            """,
            (user_id,),
        )
        plans = list(cur.fetchall())
        w11 = [p for p in plans if is_week_11(str(p["week_of"] or ""))]
        if not w11:
            print("No Week 11 plans found for Wilson Rodrigues.")
            return 0

        raw_lesson = w11[0]["lesson_json"]
        if isinstance(raw_lesson, bytes):
            text = raw_lesson.decode("utf-8", errors="replace")
        else:
            text = raw_lesson if isinstance(raw_lesson, str) else json.dumps(raw_lesson)
        lesson = json.loads(text)

        matches = list(find_portuguese_strings_with_hex_pattern(lesson))
        if not matches:
            print("No Portuguese fields with e7/e3/e9/trae7o/conspirae7e3o found in first W11 plan.")
            print("Corruption may already be fixed or not present in this plan.")
            return 0

        print("Encoding diagnostic: raw bytes of corrupted Portuguese values\n")
        for path, value in matches[:5]:
            b = value.encode("utf-8")
            hex_bytes = " ".join(f"{x:02x}" for x in b)
            snippet = value[:60] + "..." if len(value) > 60 else value
            print(f"Path: {path}")
            print(f"Value (snippet): {snippet!r}")
            print(f"UTF-8 bytes (hex): {hex_bytes}")
            if "e7" in value or "e3" in value:
                idx = value.find("e7") if "e7" in value else value.find("e3")
                sub = value[max(0, idx - 2) : idx + 4]
                sub_bytes = sub.encode("utf-8")
                print(f"  Around 'e7'/'e3': {sub!r} -> bytes {sub_bytes.hex()}")
                print(
                    "  -> Those are ASCII 'e' (0x65) and '7' (0x37) or '3' (0x33),"
                    " not the single byte 0xE7/0xE3 (Latin-1 c/a-tilde)."
                )
            print()
        print(
            "Conclusion: Stored values are literal ASCII 'e7'/'e3', not UTF-8 vs ANSI misread."
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
