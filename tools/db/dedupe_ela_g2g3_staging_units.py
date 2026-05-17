"""
Remove duplicate Grade 2/3 ELA units 5-8: staging ids (wave/sample) vs final ingest.

Keeps *_final rows (newer ingested_at). Safe to re-run: no-op if staging ids absent.

Usage (repo root):
  python tools/db/dedupe_ela_g2g3_staging_units.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "curriculum.db"

STAGING_UNIT_IDS = (
    "ELA_2_U5_wave4",
    "ELA_2_U6_wave3",
    "ELA_2_U7_wave2",
    "ELA_2_U8_sample",
    "ELA_3_U5_wave4",
    "ELA_3_U6_wave3",
    "ELA_3_U7_wave2",
    "ELA_3_U8_sample",
)


def main() -> int:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    if not db_path.is_file():
        print(f"Missing database: {db_path}", file=sys.stderr)
        return 1
    ph = ",".join("?" * len(STAGING_UNIT_IDS))
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM units WHERE id IN ({ph})", STAGING_UNIT_IDS)
    found = {r[0] for r in cur.fetchall()}
    if not found:
        print("No staging unit ids present; nothing to do.")
        return 0
    missing = set(STAGING_UNIT_IDS) - found
    if missing:
        print(f"Warning: expected ids not in DB: {sorted(missing)}", file=sys.stderr)
    to_remove = tuple(sorted(found))
    ph2 = ",".join("?" * len(to_remove))
    conn.execute("BEGIN")
    try:
        cur.execute(
            f"DELETE FROM lesson_resources WHERE lesson_id IN "
            f"(SELECT id FROM lessons WHERE unit_id IN ({ph2}))",
            to_remove,
        )
        cur.execute(
            f"DELETE FROM lesson_vocabulary WHERE lesson_id IN "
            f"(SELECT id FROM lessons WHERE unit_id IN ({ph2}))",
            to_remove,
        )
        cur.execute(
            f"DELETE FROM lesson_standards WHERE lesson_id IN "
            f"(SELECT id FROM lessons WHERE unit_id IN ({ph2}))",
            to_remove,
        )
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='science_lesson_day_segments'"
        )
        if cur.fetchone():
            cur.execute(
                f"DELETE FROM science_lesson_day_segments WHERE lesson_id IN "
                f"(SELECT id FROM lessons WHERE unit_id IN ({ph2}))",
                to_remove,
            )
        cur.execute(
            f"DELETE FROM lessons_fts WHERE lesson_id IN "
            f"(SELECT id FROM lessons WHERE unit_id IN ({ph2}))",
            to_remove,
        )
        cur.execute(f"DELETE FROM lessons WHERE unit_id IN ({ph2})", to_remove)
        cur.execute(f"DELETE FROM units_intro WHERE unit_id IN ({ph2})", to_remove)
        cur.execute(f"DELETE FROM unit_standards WHERE unit_id IN ({ph2})", to_remove)
        cur.execute(
            f"DELETE FROM unit_semantic_links WHERE from_unit_id IN ({ph2}) "
            f"OR to_unit_id IN ({ph2})",
            to_remove + to_remove,
        )
        cur.execute(f"DELETE FROM units WHERE id IN ({ph2})", to_remove)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    print(f"Removed {len(to_remove)} staging unit(s): {to_remove}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
