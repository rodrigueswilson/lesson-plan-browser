"""
Seed g2_science_book_lesson_supplement for all 20 canonical Grade 2 Science lessons.

Joins:
- SQLite lessons (unit_number, lesson_number, id, title)
- Teacher export Tab_1.md (snippets around lesson title + paired-read wording)
- Student workbook PDF (pdfplumber): estimated page span where worksheet title appears in page header

Usage (repo root, API may be running — stop if DB locked):
  python tools/db/seed_g2_science_book_lesson_supplement.py
  python tools/db/seed_g2_science_book_lesson_supplement.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from backend.database.curriculum import CurriculumDatabase
from tools.db.g2_science_book_pdf_common import (
    SOURCE_PDF_LABEL,
    head_limit_for_title,
    norm_apostrophe as _norm_apostrophe,
    title_variants,
)

_DEFAULT_PDF = (
    _REPO
    / "reference_docs/scraped/Copy_of__2nd_Grade_Science/originals"
    / "Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.pdf"
)
_TAB1 = _REPO / "reference_docs/scraped/Copy_of__2nd_Grade_Science/Tab_1/Tab_1.md"
_ISBN = "9780021344871"
_SOURCE_LABEL = SOURCE_PDF_LABEL

# Curated paired-read / explain block titles (teacher guide); empty string = none named in seed pass.
_PAIRED_HEADING_BY_LESSON_ID: Dict[str, str] = {
    "Science_2_Mod1_PropertiesOfMatter_L1": "Matter Is All Around Us; Irene's Exploration (teacher Days 2-7)",
    "Science_2_Mod1_PropertiesOfMatter_L2": "From Nature or From People",
    "Science_2_Mod1_PropertiesOfMatter_L3": "Science Paired Read Aloud + Science File (states of matter)",
    "Science_2_Mod1_PropertiesOfMatter_L4": "Material Matters; Matter, Properties, and Making Things",
    "Science_2_Mod2_ChangesToMatter_L1": "Rearranging matter / blocks (digital + notebook tasks)",
    "Science_2_Mod2_ChangesToMatter_L2": "Mixtures video; Types of Mixtures digital interactive; Science File",
    "Science_2_Mod2_ChangesToMatter_L3": "Abe and Abby's Big Surprise; Matter, Temperature, and Change",
    "Science_2_Mod3_PlantsAndTheirNeeds_L1": "Which Way to Sprout?",
    "Science_2_Mod3_PlantsAndTheirNeeds_L2": "How Plants Use Their Parts to Live and Grow",
    "Science_2_Mod3_PlantsAndTheirNeeds_L3": "Little Seed's Journey; Making New Plants",
    "Science_2_Mod4_LivingThingsInHabitats_L1": "Plant and Animal Habitats; The Dream Home",
    "Science_2_Mod4_LivingThingsInHabitats_L2": "Forest Habitats; rainfall / Forest digital resources",
    "Science_2_Mod4_LivingThingsInHabitats_L3": "A Home For Maggie",
    "Science_2_Mod4_LivingThingsInHabitats_L4": "Extreme Habitats; The Mystery of the Sphinx",
    "Science_2_Mod5_EarthSurfaceChanges_L1": "Landforms / weathering context (Explain paired selections)",
    "Science_2_Mod5_EarthSurfaceChanges_L2": "Volcanoes / quick changes (simulation + notebook)",
    "Science_2_Mod5_EarthSurfaceChanges_L3": "Beach erosion; slowing changes (design solutions)",
    "Science_2_Mod6_EarthSurface_L1": "Maps Show Earth's Features; land/water models",
    "Science_2_Mod6_EarthSurface_L2": "Ocean research; Oceans and Ponds video / Living Things in Oceans and Ponds",
    "Science_2_Mod6_EarthSurface_L3": "Fresh water; glacier model; Fresh Water Changes simulation",
}


def _teacher_snippet(tab: str, title: str) -> str:
    """Longest window around an occurrence of title that mentions paired read (case-insensitive)."""
    tab_n = _norm_apostrophe(tab)
    title_n = _norm_apostrophe(title)
    best = ""
    start = 0
    needle = title_n
    while True:
        i = tab_n.find(needle, start)
        if i < 0:
            break
        lo = max(0, i - 500)
        hi = min(len(tab_n), i + 1200)
        win = tab_n[lo:hi]
        if re.search(r"paired\s+read|science\s+paired", win, flags=re.I):
            if len(win) > len(best):
                best = win
        start = i + max(1, len(needle) // 2)
    if not best:
        lo = max(0, tab_n.find(needle))
        if lo >= 0:
            best = tab_n[lo : min(len(tab_n), lo + 900)]
    return " ".join(best.split())[:1800]


def _workbook_pattern(page_text: str) -> str:
    u = (page_text or "").upper()
    if "MODULE OPENER" in u:
        return "MODULE_OPENER"
    if "MODULE WRAP" in u:
        return "MODULE_WRAP_UP"
    if "ASSESS" in u and "READINESS" in u:
        return "ASSESS_LESSON_READINESS"
    if "INQUIRY" in u:
        return "INQUIRY_WORKSHEET"
    if "PERFORMANCE" in u and "TASK" in u:
        return "PERFORMANCE_TASK"
    return "OTHER_WORKSHEET"


def _pdf_hits_for_titles(
    pdf_path: Path, titles: List[str]
) -> Dict[str, Tuple[Optional[int], Optional[int], int, Optional[str]]]:
    """One pdfplumber pass: map lesson title -> (page_start, page_end, hit_count, first_pattern)."""
    import pdfplumber

    variants: Dict[str, Tuple[str, ...]] = {t: title_variants(t) for t in titles}
    head_limits: Dict[str, int] = {t: head_limit_for_title(t) for t in titles}

    per_title: Dict[str, List[int]] = {t: [] for t in titles}
    first_pat: Dict[str, Optional[str]] = {t: None for t in titles}

    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages):
            raw = _norm_apostrophe(page.extract_text() or "")
            for t in titles:
                head_limit = head_limits[t]
                head = raw[:head_limit]
                if any(v and v in head for v in variants[t]):
                    per_title[t].append(idx + 1)
                    if first_pat[t] is None:
                        first_pat[t] = _workbook_pattern(raw)

    out: Dict[str, Tuple[Optional[int], Optional[int], int, Optional[str]]] = {}
    for t, hits in per_title.items():
        if not hits:
            out[t] = (None, None, 0, None)
            continue
        runs: List[Tuple[int, int]] = []
        a = hits[0]
        b = hits[0]
        for p in hits[1:]:
            if p <= b + 3:
                b = p
            else:
                runs.append((a, b))
                a = b = p
        runs.append((a, b))
        best = max(runs, key=lambda x: x[1] - x[0])
        out[t] = (best[0], best[1], len(hits), first_pat[t])
    return out


def _format_notes(unit_number: int, lesson_number: int) -> str:
    return (
        "Student PDF module order differs from canonical unit_number; "
        f"canonical=Mod{unit_number} L{lesson_number}. "
        "See docs/scrapers/grade2-science-paired-read-aloud-qaa-inventory.md."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=None, help="curriculum.db path")
    ap.add_argument("--pdf", type=Path, default=_DEFAULT_PDF)
    ap.add_argument("--tab1", type=Path, default=_TAB1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db_path = args.db or Path(os.environ.get("CURRICULUM_DB_PATH", _REPO / "data" / "curriculum.db"))
    pdf_path = args.pdf.resolve()
    tab1_path = args.tab1.resolve()

    if not db_path.is_file():
        print(f"ERROR: db not found: {db_path}", file=sys.stderr)
        return 1
    if not pdf_path.is_file():
        print(f"ERROR: pdf not found: {pdf_path}", file=sys.stderr)
        return 1
    if not tab1_path.is_file():
        print(f"ERROR: Tab_1.md not found: {tab1_path}", file=sys.stderr)
        return 1

    tab_text = tab1_path.read_text(encoding="utf-8", errors="replace")

    CurriculumDatabase(str(db_path)).ensure_g2_science_book_lesson_supplement_table()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id, l.title, u.unit_number, l.lesson_number
        FROM lessons l
        JOIN units u ON u.id = l.unit_id
        WHERE u.grade = 2 AND u.subject = 'Science' AND u.id LIKE 'Science_2_Mod%'
        ORDER BY u.unit_number, l.lesson_number
        """
    )
    rows = cur.fetchall()
    if len(rows) != 20:
        print(f"WARN: expected 20 G2 Science lessons, got {len(rows)}", file=sys.stderr)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    upsert_sql = """
        INSERT INTO g2_science_book_lesson_supplement (
            lesson_id, source_pdf_label, isbn13, pdf_page_start, pdf_page_end,
            pdf_title_hit_count, first_page_workbook_pattern, paired_read_block_title,
            teacher_curriculum_cue, format_notes, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(lesson_id) DO UPDATE SET
            source_pdf_label=excluded.source_pdf_label,
            isbn13=excluded.isbn13,
            pdf_page_start=excluded.pdf_page_start,
            pdf_page_end=excluded.pdf_page_end,
            pdf_title_hit_count=excluded.pdf_title_hit_count,
            first_page_workbook_pattern=excluded.first_page_workbook_pattern,
            paired_read_block_title=excluded.paired_read_block_title,
            teacher_curriculum_cue=excluded.teacher_curriculum_cue,
            format_notes=excluded.format_notes,
            updated_at=excluded.updated_at
    """

    titles_order = [str(r["title"]) for r in rows]
    pdf_map = _pdf_hits_for_titles(pdf_path, titles_order)

    for r in rows:
        lid = str(r["id"])
        title = str(r["title"])
        un = int(r["unit_number"])
        ln = int(r["lesson_number"])
        p0, p1, nhit, pat = pdf_map.get(title, (None, None, 0, None))
        cue = _teacher_snippet(tab_text, title)
        paired = _PAIRED_HEADING_BY_LESSON_ID.get(lid, "")
        fn = _format_notes(un, ln)
        tup = (
            lid,
            _SOURCE_LABEL,
            _ISBN,
            p0,
            p1,
            nhit,
            pat,
            paired or None,
            cue or None,
            fn,
            now,
        )
        print(
            lid,
            title,
            f"pdf={p0}-{p1}",
            f"hits={nhit}",
            f"pat={pat}",
            sep=" | ",
        )
        if not args.dry_run:
            cur.execute(upsert_sql, tup)
    if not args.dry_run:
        conn.commit()
    conn.close()
    print("Done." + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
