"""
Build a machine-readable inventory of the Grade 2 Inspire Science student PDF.

Default input: Paired Read Aloud / student workbook PDF beside the scraped DOCX.
Output JSON alongside the PDF (git may ignore large binaries; JSON is small).

Usage (repo root):
  python tools/scraper/g2_inspire_science_student_pdf_inventory.py
  python tools/scraper/g2_inspire_science_student_pdf_inventory.py --pdf path/to/file.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_PDF = (
    _REPO
    / "reference_docs/scraped/Copy_of__2nd_Grade_Science/originals"
    / "Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.pdf"
)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _page_head(text: str, max_chars: int = 220) -> str:
    t = _norm((text or "").strip())
    return t[:max_chars]


def _detect_module_line(text: str) -> Optional[str]:
    """Best-effort module id when MODULE OPENER / WRAP-UP appears on the page."""
    u = text.upper()
    if "MODULE OPENER" not in u and "MODULE WRAP" not in u:
        return None
    if re.search(r"Properties\s+of\s+Matter", text, flags=re.I):
        return "PropertiesOfMatter"
    if re.search(r"Changes\s+to\s+Matter", text, flags=re.I):
        return "ChangesToMatter"
    if re.search(r"Plants\s+and\s+Their\s+Needs", text, flags=re.I):
        return "PlantsAndTheirNeeds"
    if re.search(r"Living\s+Things\s+in\s+Habitats", text, flags=re.I):
        return "LivingThingsInHabitats"
    if re.search(r"Earth.{0,3}s\s+Surface\s+Changes", text, flags=re.I):
        return "EarthSurfaceChanges"
    if re.search(r"Earth.{0,3}s\s+Surface", text, flags=re.I):
        return "EarthSurface"
    return None


def run_inventory(pdf_path: Path) -> Dict[str, Any]:
    import pdfplumber  # local import so --help works if missing

    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    page_summaries: List[Dict[str, Any]] = []
    module_signals: List[Dict[str, Any]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        n = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text() or ""
            head = _page_head(raw)
            page_summaries.append(
                {
                    "page": i + 1,
                    "char_count": len(raw),
                    "head": head,
                }
            )
            mod = _detect_module_line(raw)
            if mod:
                module_signals.append(
                    {"page": i + 1, "module_hint": mod, "head": head}
                )

    return {
        "pdf": str(pdf_path.as_posix()),
        "page_count": len(page_summaries),
        "extractor": "pdfplumber",
        "module_signals": module_signals,
        "page_summaries": page_summaries,
    }


def run_workbook_patterns(pdf_path: Path) -> Dict[str, Any]:
    """Count recurring workbook surface patterns (for comparing to DOCX lesson flow)."""
    import pdfplumber

    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))
    from tools.db.g2_science_canonical_ssot import g2_science_modules

    kw_counts: Counter[str] = Counter()
    title_hits: Dict[str, int] = {}
    titles: List[str] = []
    for mod in g2_science_modules():
        for les in mod.lessons:
            titles.append(les.title)

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            raw = page.extract_text() or ""
            u = raw.upper()
            if "MODULE OPENER" in u:
                kw_counts["MODULE_OPENER"] += 1
            if "MODULE WRAP" in u:
                kw_counts["MODULE_WRAP_UP"] += 1
            if "ASSESS" in u and "READINESS" in u:
                kw_counts["ASSESS_LESSON_READINESS"] += 1
            if "INQUIRY" in u:
                kw_counts["PAGE_WITH_INQUIRY"] += 1
            if "PERFORMANCE TASK" in u:
                kw_counts["PERFORMANCE_TASK"] += 1
            if "EVALUATE" in u and "NAME" in u:
                kw_counts["EVALUATE_HEADER"] += 1
            if "OBTAIN" in u and "COMMUNICATE" in u:
                kw_counts["OBTAIN_COMMUNICATE_BAND"] += 1
            head = raw[:480]
            for t in titles:
                if t and t in head:
                    title_hits[t] = title_hits.get(t, 0) + 1

    return {
        "pdf": str(pdf_path.as_posix()),
        "page_count": len(pdf.pages),
        "keyword_counts": dict(kw_counts),
        "lesson_title_appearances_in_page_head": title_hits,
        "notes": (
            "lesson_title_appearances counts pages where canonical SSOT title appears in first ~480 chars; "
            "use with seed script for page spans. PDF print order of modules != canonical unit_number."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pdf",
        type=Path,
        default=_DEFAULT_PDF,
        help="Path to Inspire Grade 2 student / paired read PDF",
    )
    ap.add_argument(
        "--only-patterns",
        action="store_true",
        help="Write book_patterns JSON only (skip full per-page inventory)",
    )
    args = ap.parse_args()
    pdf_path = args.pdf.resolve()
    if args.only_patterns:
        pdata = run_workbook_patterns(pdf_path)
        out = pdf_path.with_name(pdf_path.stem + ".book_patterns.json")
        out.write_text(json.dumps(pdata, indent=2), encoding="utf-8")
        print(f"Wrote {out}")
        return 0
    data = run_inventory(pdf_path)
    out = pdf_path.with_name(pdf_path.stem + ".inventory.json")
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({data['page_count']} pages, {len(data['module_signals'])} module signals)")
    pout = pdf_path.with_name(pdf_path.stem + ".book_patterns.json")
    pout.write_text(json.dumps(run_workbook_patterns(pdf_path), indent=2), encoding="utf-8")
    print(f"Wrote {pout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
