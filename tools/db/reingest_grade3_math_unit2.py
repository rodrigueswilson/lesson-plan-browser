"""
Delete Grade 3 Math Unit 2 (reference / anchor unit) and re-ingest from the canonical DOCX.

Usage (repo root):
  python tools/db/reingest_grade3_math_unit2.py
  python tools/db/reingest_grade3_math_unit2.py --docx "path/to/Unit_2__Area_and_Multiplication.docx"

Environment:
  CURRICULUM_DB_PATH overrides default d:\\LP\\data\\curriculum.db
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UNIT_ID = "Math_3_U2_1hBoK4uk"
SOURCE_URL = (
    "https://docs.google.com/document/d/1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE/edit"
)
_DEFAULT_DOCX = os.path.join(
    _REPO_ROOT,
    "reference_docs",
    "scraped",
    "3rd grade_unit 2_docx",
    "Unit_2__Area_and_Multiplication.docx",
)
_SEED_SCRIPT = os.path.join(_REPO_ROOT, "tools", "db", "seed_reference_unit.py")
_SCRAPER_DIR = os.path.join(_REPO_ROOT, "tools", "scraper")


def delete_unit_and_lessons(conn: sqlite3.Connection, unit_id: str) -> None:
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE unit_id = ?", (unit_id,))
    lesson_ids = [r[0] for r in cur.fetchall()]

    for lid in lesson_ids:
        cur.execute("DELETE FROM lesson_resources WHERE lesson_id = ?", (lid,))
        cur.execute("DELETE FROM lesson_standards WHERE lesson_id = ?", (lid,))
        cur.execute("DELETE FROM lesson_vocabulary WHERE lesson_id = ?", (lid,))
        cur.execute("DELETE FROM science_lesson_day_segments WHERE lesson_id = ?", (lid,))

    cur.execute("DELETE FROM lessons WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM unit_standards WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM units_intro WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM units WHERE id = ?", (unit_id,))
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--docx",
        default=_DEFAULT_DOCX,
        help="Path to Unit 2 DOCX (default: reference_docs scraped canonical export)",
    )
    args = ap.parse_args()

    db_path = os.environ.get("CURRICULUM_DB_PATH", os.path.join(_REPO_ROOT, "data", "curriculum.db"))
    docx = os.path.abspath(args.docx)

    if not os.path.isfile(db_path):
        print(f"ERROR: curriculum DB not found: {db_path}")
        return 1
    if not os.path.isfile(docx):
        print(f"ERROR: DOCX not found: {docx}")
        return 1

    print(f"Deleting unit {UNIT_ID} and related lesson rows from {db_path}...", flush=True)
    sys.path.insert(0, _REPO_ROOT)
    from backend.database.curriculum import CurriculumDatabase

    CurriculumDatabase(db_path).ensure_science_lesson_day_segments_table()
    conn = sqlite3.connect(db_path)
    try:
        delete_unit_and_lessons(conn, UNIT_ID)
    finally:
        conn.close()

    print("Re-seeding unit row + units_intro shell...", flush=True)
    env = {**os.environ, "CURRICULUM_DB_PATH": db_path}
    r = subprocess.run([sys.executable, _SEED_SCRIPT], cwd=_REPO_ROOT, env=env)
    if r.returncode != 0:
        return r.returncode

    print(f"Ingesting from {docx} (provenance source URL set)...", flush=True)
    sys.path.insert(0, _SCRAPER_DIR)
    sys.path.insert(0, _REPO_ROOT)
    from table_extractor import RecursiveTableParser

    parser = RecursiveTableParser(db_path=db_path)
    count = parser.ingest_to_curriculum(
        docx,
        UNIT_ID,
        subject="Math",
        source_url=SOURCE_URL,
        parser_version="table_extractor@v1",
    )
    print(f"Done. Upserted {count} lesson row(s) for {UNIT_ID}.", flush=True)
    print("Run: python tools/scraper/verify_curriculum_db.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
