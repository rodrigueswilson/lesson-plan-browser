"""
Delete Grade 2 ELA Unit 2 (``ELA_2_U2_final``) and re-ingest from the **Unit 2 tab** DOCX.

The curriculum parser runs per **unit** from one DOCX; it cannot target only lessons 22–23.
Re-ingesting this unit refreshes **all** lessons (including 22–23), vocabulary links, standards,
and structured ELA JSON for that unit.

Export the tab (same compendium as other G2 ELA units):

  python tools/scraper/export_doc_ids_to_docx.py --out reference_docs/scraped/grade2_ela_exports \\
    1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak

Then pick the **Grade 2 Unit 2** .docx from the ``*_by_tab`` folder (or build one tab with
``gdoc_tab_to_docx.py`` — see ``reingest_grade2_ela_unit8_sample.py`` docstring).

Provenance (parent Google Doc):
  https://docs.google.com/document/d/1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak/edit

Usage (repo root):

  python tools/db/reingest_grade2_ela_unit2_final.py --docx "path/to/Grade_2_Unit_2....docx"

Environment:
  CURRICULUM_DB_PATH overrides default ``data/curriculum.db``.

After ingest:

  python tools/scraper/verify_curriculum_db.py
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UNIT_ID = "ELA_2_U2_final"
SOURCE_DOC_ID = "1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak"
SOURCE_URL = f"https://docs.google.com/document/d/{SOURCE_DOC_ID}/edit"
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


def seed_unit_row(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO units
        (id, grade, subject, unit_number, title, description, source)
        VALUES (?, 2, 'ELA', 2, 'Grade 2 Unit 2 (ELA final)', '', 'reingest_grade2_ela_unit2_final')
        """,
        (UNIT_ID,),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO units_intro (unit_id, essential_questions, enduring_understandings)
        VALUES (?, '[]', '[]')
        """,
        (UNIT_ID,),
    )
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--docx",
        required=True,
        help="Path to exported Grade 2 ELA **Unit 2** tab DOCX (not the full compendium unless it contains only this unit).",
    )
    ap.add_argument(
        "--source-url",
        default=os.environ.get("CURRICULUM_ELA_G2_U2_SOURCE_URL", SOURCE_URL),
        help="Google Doc URL stored on lesson/unit provenance fields",
    )
    args = ap.parse_args()

    db_path = os.environ.get("CURRICULUM_DB_PATH", os.path.join(_REPO_ROOT, "data", "curriculum.db"))
    docx = os.path.abspath(args.docx)

    if not os.path.isfile(db_path):
        print(f"ERROR: curriculum DB not found: {db_path}", flush=True)
        return 1
    if not os.path.isfile(docx):
        print(f"ERROR: DOCX not found: {docx}", flush=True)
        return 1

    print(f"Deleting unit {UNIT_ID} and related lesson rows from {db_path}...", flush=True)
    sys.path.insert(0, _REPO_ROOT)
    from backend.database.curriculum import CurriculumDatabase

    CurriculumDatabase(db_path).ensure_science_lesson_day_segments_table()
    conn = sqlite3.connect(db_path)
    try:
        delete_unit_and_lessons(conn, UNIT_ID)
        seed_unit_row(conn)
    finally:
        conn.close()

    print(f"Ingesting ELA from {docx}...", flush=True)
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
