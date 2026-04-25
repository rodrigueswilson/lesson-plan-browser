"""
Insert the Grade 3 ELA sample unit row (and units_intro shell) before ingest_to_curriculum.

Registry context: Grade 3 ELA-style materials appear under multiple keys in
reference_docs/scraped_registry.json; this seed uses a stable synthetic unit id
for cross-subject gate checks once a teacher-guide DOCX is ingested.

Usage (repo root):
  python tools/db/seed_grade3_ela_sample_unit.py

Environment:
  CURRICULUM_DB_PATH overrides default d:\\LP\\data\\curriculum.db
"""
from __future__ import annotations

import os
import sqlite3

DB = os.environ.get("CURRICULUM_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curriculum.db"))

UNIT_ID = "ELA_3_U8_sample"
UNIT_ROW = (
    UNIT_ID,
    3,
    "ELA",
    8,
    "Grade 3 Unit 8: Reading and Writing (ELA sample)",
    "",
    "seed_grade3_ela_sample_unit",
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
