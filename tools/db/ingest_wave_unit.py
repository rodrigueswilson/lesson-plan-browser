"""
Seed one unit row, export Google Doc to DOCX, and ingest into curriculum.db.

Usage (repo root):
  python tools/db/ingest_wave_unit.py --unit-id Math_3_U1_13jAzcMR --grade 3 --subject Math --unit-number 1 --title "Grade 3 Unit 1: Introducing Multiplication" --doc-id 13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg

Phase 3 Grade 3 Math batch (all units + verify after each): see ingest_g3_math_phase3_corpus.py
and g3_math_phase3_corpus.py.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRAPER_DIR = _REPO_ROOT / "tools" / "scraper"
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from docs_client import DocsClient
from table_extractor import RecursiveTableParser


def _seed_unit(db_path: str, unit_id: str, grade: int, subject: str, unit_number: int, title: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT OR REPLACE INTO units
        (id, grade, subject, unit_number, title, description, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (unit_id, grade, subject, unit_number, title, "", "ingest_wave_unit"),
    )
    conn.execute(
        """INSERT OR IGNORE INTO units_intro (unit_id, essential_questions, enduring_understandings)
        VALUES (?, '[]', '[]')""",
        (unit_id,),
    )
    conn.commit()
    conn.close()


def _delete_unit_rows(db_path: str, unit_id: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE unit_id = ?", (unit_id,))
    lesson_ids = [r[0] for r in cur.fetchall()]
    for lid in lesson_ids:
        cur.execute("DELETE FROM lesson_resources WHERE lesson_id = ?", (lid,))
        cur.execute("DELETE FROM lesson_standards WHERE lesson_id = ?", (lid,))
        cur.execute("DELETE FROM lesson_vocabulary WHERE lesson_id = ?", (lid,))
    cur.execute("DELETE FROM lessons WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM unit_standards WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM units_intro WHERE unit_id = ?", (unit_id,))
    cur.execute("DELETE FROM units WHERE id = ?", (unit_id,))
    conn.commit()
    conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit-id", required=True)
    ap.add_argument("--grade", type=int, required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--unit-number", type=int, required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--parser-version", default="table_extractor@v1")
    args = ap.parse_args()

    db_path = os.environ.get("CURRICULUM_DB_PATH", str(_REPO_ROOT / "data" / "curriculum.db"))
    source_url = f"https://docs.google.com/document/d/{args.doc_id}/edit"

    print(f"Resetting unit rows for {args.unit_id} in {db_path}...", flush=True)
    _delete_unit_rows(db_path, args.unit_id)
    _seed_unit(db_path, args.unit_id, args.grade, args.subject, args.unit_number, args.title)

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        docx_path = tmp.name

    try:
        print(f"Fetching Drive file {args.doc_id} as DOCX...", flush=True)
        ok, err = DocsClient().fetch_docx_for_curriculum_result(args.doc_id, docx_path)
        if not ok:
            print(f"ERROR: {err}", flush=True)
            return 1

        parser = RecursiveTableParser(db_path=db_path)
        count = parser.ingest_to_curriculum(
            docx_path,
            args.unit_id,
            subject=args.subject,
            source_url=source_url,
            parser_version=args.parser_version,
        )
        print(f"Done. Upserted {count} lesson row(s) for {args.unit_id}.", flush=True)
        return 0
    finally:
        if os.path.exists(docx_path):
            os.remove(docx_path)


if __name__ == "__main__":
    raise SystemExit(main())
