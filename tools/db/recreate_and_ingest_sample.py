"""
Recreate curriculum.db from SSOT schema, seed reference unit, run DOCX ingestion.

Usage (repo root):
  python tools/db/recreate_and_ingest_sample.py
  python tools/db/recreate_and_ingest_sample.py --full-unit

Optional:
  set CURRICULUM_DB_PATH to use a non-default DB file.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_INIT_SCRIPT = os.path.join(_REPO_ROOT, "tools", "db", "initialize_db.py")
_SEED_SCRIPT = os.path.join(_REPO_ROOT, "tools", "db", "seed_reference_unit.py")
_SCRAPER_DIR = os.path.join(_REPO_ROOT, "tools", "scraper")

DOCX_QUICK = os.path.join(
    _REPO_ROOT,
    "reference_docs",
    "scraped",
    "3rd grade_unit 2_docx",
    "Copy of Unit_2__Area_and_Multiplication.docx",
)
DOCX_FULL_UNIT = os.path.join(
    _REPO_ROOT,
    "reference_docs",
    "scraped",
    "3rd grade_unit 2_docx",
    "Unit_2__Area_and_Multiplication.docx",
)

UNIT_ID = "Math_3_U2_1hBoK4uk"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--full-unit",
        action="store_true",
        help="Ingest full Unit_2 DOCX (all lessons; may call Google APIs for linked docs; slow).",
    )
    args = ap.parse_args()

    docx = DOCX_FULL_UNIT if args.full_unit else DOCX_QUICK
    if not os.path.isfile(docx):
        fallback = DOCX_QUICK if docx == DOCX_FULL_UNIT else DOCX_FULL_UNIT
        docx = fallback if os.path.isfile(fallback) else docx

    print("Step 1: Recreate curriculum.db (initialize_db.py)...")
    r = subprocess.run([sys.executable, _INIT_SCRIPT], cwd=_REPO_ROOT)
    if r.returncode != 0:
        return r.returncode

    print("Step 2: Seed reference unit...")
    r = subprocess.run([sys.executable, _SEED_SCRIPT], cwd=_REPO_ROOT)
    if r.returncode != 0:
        return r.returncode

    if not os.path.isfile(docx):
        print(f"No sample DOCX at expected paths; skipping ingestion.")
        return 0

    print(f"Step 3: Ingest {docx}...")
    sys.path.insert(0, _SCRAPER_DIR)
    from table_extractor import RecursiveTableParser

    parser = RecursiveTableParser()
    count = parser.ingest_to_curriculum(docx, UNIT_ID, subject="Math")
    print(f"Ingested {count} lesson(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
