"""
Populate science_lesson_day_segments from existing lessons.science_li_sc_day_structured JSON.

Use when the relational table was added after ingest (no full Science re-ingest required).

Usage (repo root):
  python tools/db/backfill_science_lesson_day_segments.py
  python tools/db/backfill_science_lesson_day_segments.py --dry-run

Environment:
  CURRICULUM_DB_PATH overrides default data/curriculum.db
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.database.curriculum import CurriculumDatabase


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List lesson ids that would be updated, do not write",
    )
    args = ap.parse_args()

    db_path = os.environ.get(
        "CURRICULUM_DB_PATH",
        str(_REPO_ROOT / "data" / "curriculum.db"),
    )
    if not os.path.isfile(db_path):
        print(f"ERROR: database not found: {db_path}", flush=True)
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, science_li_sc_day_structured
            FROM lessons
            WHERE science_li_sc_day_structured IS NOT NULL
              AND TRIM(science_li_sc_day_structured) != ''
            ORDER BY id
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No lessons with non-empty science_li_sc_day_structured; nothing to do.", flush=True)
        return 0

    print(f"Found {len(rows)} lesson(s) with Science structured JSON.", flush=True)
    if args.dry_run:
        for r in rows[:50]:
            print(f"  would backfill: {r['id']}", flush=True)
        if len(rows) > 50:
            print(f"  ... and {len(rows) - 50} more", flush=True)
        return 0

    db = CurriculumDatabase(db_path)
    n = 0
    for r in rows:
        db.replace_science_lesson_day_segments(
            str(r["id"]),
            r["science_li_sc_day_structured"],
        )
        n += 1
    print(f"Backfilled science_lesson_day_segments for {n} lesson(s).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
