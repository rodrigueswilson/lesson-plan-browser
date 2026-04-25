"""
Delete the Grade 3 ELA sample unit and re-ingest from an exported teacher-guide DOCX.

Fetch from Google (OAuth required; see tools/scraper/SETUP.md):
  python tools/scraper/export_doc_ids_to_docx.py --preset grade3-ela-all-units --out reference_docs/scraped/grade3_ela_exports

The Grade 3 ELA compendium often exceeds the Drive API DOCX/PDF export limit. Prefer:
  python tools/scraper/export_doc_ids_to_docx.py --preset grade3-ela-all-units --out reference_docs/scraped/grade3_ela_exports
then pass the Unit 8 tab file from the generated *_by_tab/ folder (name contains "Grade 3 Unit 8").

Alternatives: browser File > Download > Microsoft Word (.docx), or synthesize from a *.docs-api.json snapshot:
  python tools/scraper/gdoc_tab_to_docx.py --json-path .../Grade_3_ELA_All_Units_including_8_1_yHvguD.docs-api.json ^
    --tab-title "Grade 3 Unit 8" --out .../Grade3_ELA_Unit8_from_api_tab.docx

Provenance (Grade 3 ELA compendium, all units incl. Unit 8):
  https://docs.google.com/document/d/1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY/edit

When Drive DOCX export works, filenames look like *_<docid8>.docx; the compendium usually only yields *.docs-api.json.

Usage (repo root):
  python tools/db/reingest_grade3_ela_sample.py --docx "reference_docs/scraped/grade3_ela_exports/Grade3_ELA_Unit8_from_api_tab.docx" ^
    --source-url "https://docs.google.com/document/d/1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY/edit"

Environment:
  CURRICULUM_DB_PATH overrides default d:\\LP\\data\\curriculum.db

After ingest, run:
  python tools/scraper/verify_curriculum_db.py
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UNIT_ID = "ELA_3_U8_sample"
_SOURCE_HINT = (
    "Set SOURCE_URL to the Google Doc URL for provenance when ingesting from an export."
)
_SEED_SCRIPT = os.path.join(_REPO_ROOT, "tools", "db", "seed_grade3_ela_sample_unit.py")
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
        help="Path to exported Grade 3 ELA unit teacher-guide DOCX",
    )
    ap.add_argument(
        "--source-url",
        default=os.environ.get("CURRICULUM_ELA_SAMPLE_SOURCE_URL", ""),
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

    print("Re-seeding ELA sample unit row + units_intro shell...", flush=True)
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
