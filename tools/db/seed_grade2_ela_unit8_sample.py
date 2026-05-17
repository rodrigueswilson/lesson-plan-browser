"""
Insert the Grade 2 ELA Unit 8 sample unit row (and units_intro shell) before ingest_to_curriculum.

Registry: reference_docs/scraped_registry.json — Grade 2 / Copy_of_02_-_Second_Grade_Unit_Description...

Usage (repo root):
  python tools/db/seed_grade2_ela_unit8_sample.py

Environment:
  CURRICULUM_DB_PATH overrides default d:\\LP\\data\\curriculum.db
"""
from __future__ import annotations

import os
import sqlite3

DB = os.environ.get("CURRICULUM_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curriculum.db"))

UNIT_ID = "ELA_2_U8_sample"
UNIT_ROW = (
    UNIT_ID,
    2,
    "ELA",
    8,
    "Grade 2 Unit 8 (ELA sample)",
    "",
    "seed_grade2_ela_unit8_sample",
)


def main() -> int:
    if not os.path.isfile(DB):
        print(f"ERROR: curriculum DB not found: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO units
            (id, grade, subject, unit_number, title, description, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            UNIT_ROW,
        )
        conn.execute(
            """INSERT OR IGNORE INTO units_intro (unit_id, essential_questions, enduring_understandings)
            VALUES (?, '[]', '[]')""",
            (UNIT_ID,),
        )
        conn.commit()
    finally:
        conn.close()
    print(f"Seeded unit {UNIT_ID} in {DB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
