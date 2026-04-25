"""
Delete the Grade 2 ELA Unit 8 sample unit and re-ingest from an exported teacher-guide DOCX.

Compendium (tabs): export then use the Unit 8 tab file from *_by_tab/:
  python tools/scraper/export_doc_ids_to_docx.py --out reference_docs/scraped/grade2_ela_exports \\
    1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak

Provenance:
  https://docs.google.com/document/d/1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak/edit

Usage (repo root):
  python tools/db/reingest_grade2_ela_unit8_sample.py --docx "reference_docs/scraped/grade2_ela_exports/...Grade 2 Unit 8....docx" \\
    --source-url "https://docs.google.com/document/d/1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak/edit"

Environment:
  CURRICULUM_DB_PATH overrides default d:\\LP\\data\\curriculum.db

After ingest, run:
  python tools/scraper/verify_curriculum_db.py

Structured SSOT: lessons that receive ``ela_lesson_plan_structured`` no longer get
``ela_key_learning_summary`` (matrix text lives only in the structured JSON + UI grid).

Rollout: confirm Lesson 1 in the explorer, then keep this unit ingest; repeat per tab
for other Grade 2 units and Grade 3 using the same parser (add fixtures if layout differs).

Optional: ``python tools/scraper/diagnose_ela_lesson_docx.py <path-to-tab.docx>`` to print
table detection for debugging exports.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UNIT_ID = "ELA_2_U8_sample"
_SOURCE_HINT = (
    "Set SOURCE_URL to the Google Doc URL for provenance when ingesting from an export."
)
_SEED_SCRIPT = os.path.join(_REPO_ROOT, "tools", "db", "seed_grade2_ela_unit8_sample.py")
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
        required=True,
        help="Path to exported Grade 2 ELA Unit 8 teacher-guide DOCX (tab export)",
    )
    ap.add_argument(
        "--source-url",
        default=os.environ.get("CURRICULUM_ELA_G2_U8_SOURCE_URL", ""),
        help="Optional Google Doc URL for unit/lesson provenance",
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

    print("Re-seeding Grade 2 ELA Unit 8 sample unit row + units_intro shell...", flush=True)
    env = {**os.environ, "CURRICULUM_DB_PATH": db_path}
    r = subprocess.run([sys.executable, _SEED_SCRIPT], cwd=_REPO_ROOT, env=env)
    if r.returncode != 0:
        return r.returncode

    print(f"Ingesting ELA from {docx}...", flush=True)
    if not args.source_url:
        print(f"Note: {_SOURCE_HINT}", flush=True)
    sys.path.insert(0, _SCRAPER_DIR)
    sys.path.insert(0, _REPO_ROOT)
    from table_extractor import RecursiveTableParser

    parser = RecursiveTableParser(db_path=db_path)
    count = parser.ingest_to_curriculum(
        docx,
        UNIT_ID,
        subject="ELA",
        source_url=args.source_url or None,
        parser_version="table_extractor@v1",
    )
    print(f"Done. Upserted {count} lesson row(s) for {UNIT_ID}.", flush=True)
    print("Run: python tools/scraper/verify_curriculum_db.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
