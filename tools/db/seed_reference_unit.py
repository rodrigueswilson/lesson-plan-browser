"""
Insert a minimal unit row required before ingest_to_curriculum (FK to units).

Usage:
  python tools/db/seed_reference_unit.py
"""
import os
import sqlite3

DB = os.environ.get("CURRICULUM_DB_PATH", r"d:\LP\data\curriculum.db")

UNIT_ID = "Math_3_U2_1hBoK4uk"
UNIT_ROW = (
    UNIT_ID,
    3,
    "Math",
    2,
    "Grade 3 Unit 2: Area and Multiplication",
    "",
    "seed_reference_unit",
)


def main() -> None:
    conn = sqlite3.connect(DB)
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
    conn.close()
    print(f"Seeded unit {UNIT_ID} in {DB}")


if __name__ == "__main__":
    main()
