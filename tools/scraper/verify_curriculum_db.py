"""
CLI: verify curriculum.db has tables/columns required by CurriculumDatabase and API,
plus optional data-integrity checks after ingestion.

Usage (from repo root):
  python tools/scraper/verify_curriculum_db.py
  python tools/scraper/verify_curriculum_db.py --db d:/LP/data/curriculum.db
  python tools/scraper/verify_curriculum_db.py --no-data-checks

Second-template smoke (optional; set when you have another representative DOCX):
  CURRICULUM_VERIFY_SECOND_DOCX=path/to/file.docx CURRICULUM_VERIFY_SECOND_UNIT_ID=unit_id \\
    python tools/scraper/verify_curriculum_db.py
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

# Allow running as script from repo root
_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRAPER_DIR))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from backend.database.curriculum_validation import validate_curriculum_db
from backend.database.curriculum import CurriculumDatabase


_STANDARDS_LEAK_PATTERNS = (
    re.compile(r"activity\s+\d+\s*:", re.I),
    re.compile(r"\bmath\s+workshop\b", re.I),
)


def verify_curriculum_data_integrity(db_path: str) -> list[str]:
    """Post-schema checks: standards leaks, structured standards on reference unit."""
    issues: list[str] = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        for row in conn.execute(
            "SELECT code, description FROM standards WHERE description IS NOT NULL"
        ):
            desc = row["description"] or ""
            for pat in _STANDARDS_LEAK_PATTERNS:
                if pat.search(desc):
                    issues.append(
                        f"standards.description may contain procedure heading noise ({row['code']!r})"
                    )
                    break

        row = conn.execute(
            """
            SELECT COUNT(*) AS n, SUM(
              CASE WHEN standards_structured IS NULL OR TRIM(standards_structured) = ''
                OR standards_structured = '[]' THEN 1 ELSE 0 END
            ) AS missing
            FROM lessons l
            JOIN units u ON l.unit_id = u.id
            WHERE u.subject = 'Math' AND u.unit_number = 2
            """
        ).fetchone()
        if row and row["n"] and row["n"] > 0 and row["missing"]:
            issues.append(
                "lessons in Math unit_number=2: some rows lack non-empty standards_structured JSON"
            )

        row = conn.execute(
            """
            SELECT COUNT(*) AS n,
                   SUM(CASE WHEN narrative_html LIKE '%students%compare%' OR narrative_html LIKE '%Students%compare%' THEN 1 ELSE 0 END) AS hit
            FROM lessons l
            JOIN units u ON l.unit_id = u.id
            WHERE u.subject = 'Math' AND u.unit_number = 2 AND narrative_html IS NOT NULL
            """
        ).fetchone()
        if row and row["n"] and row["n"] >= 3 and not row["hit"]:
            issues.append(
                "Math unit 2 narrative_html: no 'students compare' style merge sample detected (soft check)"
            )
    finally:
        conn.close()
    return issues


def maybe_verify_second_template() -> list[str]:
    """Optional ingest smoke when env points at a second DOCX + unit id."""
    docx = os.environ.get("CURRICULUM_VERIFY_SECOND_DOCX")
    unit_id = os.environ.get("CURRICULUM_VERIFY_SECOND_UNIT_ID")
    if not docx or not unit_id:
        return []
    if not os.path.isfile(docx):
        return [f"CURRICULUM_VERIFY_SECOND_DOCX not found: {docx}"]
    sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "scraper"))
    from table_extractor import RecursiveTableParser

    parser = RecursiveTableParser()
    try:
        n = parser.ingest_to_curriculum(docx, unit_id, subject="Math")
    except Exception as e:
        return [f"second-template ingest failed: {e}"]
    if n <= 0:
        return ["second-template ingest produced zero lessons"]
    return []


def main() -> int:
    p = argparse.ArgumentParser(description="Verify curriculum SQLite schema and data integrity.")
    p.add_argument(
        "--db",
        default=os.environ.get("CURRICULUM_DB_PATH", r"d:\LP\data\curriculum.db"),
        help="Path to curriculum.db",
    )
    p.add_argument(
        "--no-data-checks",
        action="store_true",
        help="Skip standards_structured / description leak checks",
    )
    args = p.parse_args()
    CurriculumDatabase(args.db).ensure_provenance_columns()
    issues = validate_curriculum_db(args.db)
    if issues:
        print("Curriculum DB validation FAILED:")
        for line in issues:
            print(f"  - {line}")
        return 1
    if not args.no_data_checks:
        issues = verify_curriculum_data_integrity(args.db)
        if issues:
            print("Curriculum DB data integrity FAILED:")
            for line in issues:
                print(f"  - {line}")
            return 1
        issues = maybe_verify_second_template()
        if issues:
            print("Curriculum second-template verification FAILED:")
            for line in issues:
                print(f"  - {line}")
            return 1
    print("Curriculum DB validation OK:", args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
