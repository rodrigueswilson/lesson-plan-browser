"""
Ingest Grade 2 Inspire student workbook PDF text into g2_science_book_lesson_extract.

Per-page plain text aligned to canonical lesson_id via title-in-head heuristics + optional
g2_science_book_page_overrides.json. Does not modify lesson SSOT HTML (ADR-003).

Usage (repo root; stop API if DB locked for long writes):
  python tools/db/ingest_g2_science_book_pdf.py --dry-run
  python tools/db/ingest_g2_science_book_pdf.py --force
  python tools/db/ingest_g2_science_book_pdf.py --lesson-id Science_2_Mod1_PropertiesOfMatter_L1
  (single-lesson mode clears that lesson's extract rows before insert; full run needs --force)
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from backend.database.curriculum import CurriculumDatabase

from tools.db.g2_science_book_pdf_common import (
    BOOK_EXTRACT_PARSER_VERSION,
    SOURCE_PDF_LABEL,
    load_page_overrides,
    match_titles_in_head,
    norm_apostrophe,
    override_lesson_for_page,
    sha256_text,
)

_DEFAULT_PDF = (
    _REPO
    / "reference_docs/scraped/Copy_of__2nd_Grade_Science/originals"
    / "Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.pdf"
)
_DEFAULT_OVERRIDES = _REPO / "tools/db/g2_science_book_page_overrides.json"


def _load_lessons(conn: sqlite3.Connection, lesson_id: Optional[str]) -> List[Tuple[str, str]]:
    cur = conn.cursor()
    if lesson_id:
        cur.execute(
            """
            SELECT l.id, l.title FROM lessons l
            JOIN units u ON u.id = l.unit_id
            WHERE l.id = ? AND u.grade = 2 AND u.subject = 'Science'
            """,
            (lesson_id,),
        )
        row = cur.fetchone()
        return [(row[0], row[1])] if row else []
    cur.execute(
        """
        SELECT l.id, l.title FROM lessons l
        JOIN units u ON u.id = l.unit_id
        WHERE u.grade = 2 AND u.subject = 'Science' AND u.id LIKE 'Science_2_Mod%'
        ORDER BY u.unit_number, l.lesson_number
        """
    )
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


def _extract_pages(pdf_path: Path) -> List[Tuple[int, str]]:
    import pdfplumber

    out: List[Tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text() or ""
            out.append((i + 1, norm_apostrophe(raw)))
    return out


def _assign_page(
    page_number: int,
    body: str,
    lessons: Sequence[Tuple[str, str]],
    overrides: Sequence[Dict[str, Any]],
) -> Tuple[Optional[str], str, int]:
    oid = override_lesson_for_page(page_number, overrides)
    if oid:
        return oid, "high", 0
    return match_titles_in_head(body, lessons)


def ingest(
    db_path: Path,
    pdf_path: Path,
    overrides_path: Path,
    *,
    lesson_id: Optional[str],
    dry_run: bool,
    force: bool,
) -> int:
    if not db_path.is_file():
        print(f"ERROR: db not found: {db_path}", file=sys.stderr)
        return 1
    if not pdf_path.is_file():
        print(f"ERROR: pdf not found: {pdf_path}", file=sys.stderr)
        return 1

    db = CurriculumDatabase(str(db_path))
    db.ensure_g2_science_book_lesson_extract_table()

    conn = sqlite3.connect(str(db_path))
    lessons = _load_lessons(conn, lesson_id)
    conn.close()
    if not lessons:
        print("ERROR: no lessons to process", file=sys.stderr)
        return 1

    overrides = load_page_overrides(overrides_path)
    pages = _extract_pages(pdf_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows_by_lesson: Dict[str, List[Dict[str, Any]]] = {lid: [] for lid, _ in lessons}
    low_quality = 0
    for page_number, body in pages:
        if len(body.strip()) < 20:
            low_quality += 1
        lid, conf, amb = _assign_page(page_number, body, lessons, overrides)
        if not lid:
            continue
        if lesson_id and lid != lesson_id:
            continue
        h = sha256_text(body)
        row_id = f"{lid}_bkp{page_number:04d}"
        rows_by_lesson.setdefault(lid, []).append(
            {
                "id": row_id,
                "lesson_id": lid,
                "page_number": page_number,
                "body_text": body,
                "char_count": len(body),
                "content_sha256": h,
                "alignment_confidence": conf,
                "alignment_ambiguous": amb,
                "source_pdf_label": SOURCE_PDF_LABEL,
                "ingest_parser_version": BOOK_EXTRACT_PARSER_VERSION,
                "ingested_at": now,
            }
        )

    total = sum(len(v) for v in rows_by_lesson.values())
    print(
        f"pages={len(pages)} low_text_pages~={low_quality} assigned_rows={total} lessons_with_rows={sum(1 for v in rows_by_lesson.values() if v)}"
    )
    for lid, rows in sorted(rows_by_lesson.items()):
        if rows:
            pnums = [r["page_number"] for r in rows]
            print(f"  {lid}: {len(rows)} pages min={min(pnums)} max={max(pnums)}")

    if dry_run:
        print("Dry-run: no DB writes.")
        return 0

    if not lesson_id and not force:
        print(
            "ERROR: full workbook ingest requires --force (deletes existing workbook extract rows).",
            file=sys.stderr,
        )
        return 1

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    if force:
        if lesson_id:
            cur.execute(
                "DELETE FROM g2_science_book_lesson_extract WHERE lesson_id = ?",
                (lesson_id,),
            )
        else:
            cur.execute(
                "DELETE FROM g2_science_book_lesson_extract WHERE source_pdf_label = ?",
                (SOURCE_PDF_LABEL,),
            )
    ins = """
        INSERT INTO g2_science_book_lesson_extract (
            id, lesson_id, page_number, body_text, char_count, content_sha256,
            alignment_confidence, alignment_ambiguous, source_pdf_label,
            ingest_parser_version, ingested_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(lesson_id, page_number) DO UPDATE SET
            body_text=excluded.body_text,
            char_count=excluded.char_count,
            content_sha256=excluded.content_sha256,
            alignment_confidence=excluded.alignment_confidence,
            alignment_ambiguous=excluded.alignment_ambiguous,
            source_pdf_label=excluded.source_pdf_label,
            ingest_parser_version=excluded.ingest_parser_version,
            ingested_at=excluded.ingested_at
    """
    for lid, rows in rows_by_lesson.items():
        for r in rows:
            cur.execute(
                ins,
                (
                    r["id"],
                    r["lesson_id"],
                    r["page_number"],
                    r["body_text"],
                    r["char_count"],
                    r["content_sha256"],
                    r["alignment_confidence"],
                    r["alignment_ambiguous"],
                    r["source_pdf_label"],
                    r["ingest_parser_version"],
                    r["ingested_at"],
                ),
            )
    conn.commit()
    conn.close()
    print("Ingest complete.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=None)
    ap.add_argument("--pdf", type=Path, default=_DEFAULT_PDF)
    ap.add_argument("--overrides", type=Path, default=_DEFAULT_OVERRIDES)
    ap.add_argument("--lesson-id", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Delete existing extract rows (all workbook or single --lesson-id) before insert",
    )
    args = ap.parse_args()
    db_path = args.db or Path(os.environ.get("CURRICULUM_DB_PATH", _REPO / "data" / "curriculum.db"))
    return ingest(
        db_path.resolve(),
        args.pdf.resolve(),
        args.overrides.resolve(),
        lesson_id=args.lesson_id,
        dry_run=args.dry_run,
        force=args.force or bool(args.lesson_id),
    )


if __name__ == "__main__":
    raise SystemExit(main())
