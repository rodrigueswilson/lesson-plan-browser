"""
Spike: walk Grade 2 Science Unit 1 DOCX tables and dump Learning Intention / Success
Criteria grids that use flexible day labels (Day 1:, Days 2&3:, etc.).

Uses the same table JSON model as RecursiveTableParser (nested tables in cells).

Usage (repo root):
  python tools/scraper/diagnose_science_g2_unit1_tables.py --docx path/to/unit1.docx
  python tools/scraper/diagnose_science_g2_unit1_tables.py --docx u.docx --json-out spike.json

Default --docx (if file exists): after running ``python tools/scraper/main.py <G2 Science doc id> ...``
(see ``tools/db/g2_science_corpus.py``), use the exported root DOCX under e.g.
``reference_docs/scraped/Copy_of__2nd_Grade_Science/originals/Copy_of__2nd_Grade_Science.docx``
(title-derived folder names vary with the source Doc).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from docx import Document

_SCRAPER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRAPER_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))

from tools.scraper.science_day_labels import day_labels_in_text
from tools.scraper.table_extractor import RecursiveTableParser

_DEFAULT_DOCX = (
    _REPO_ROOT
    / "reference_docs"
    / "scraped"
    / "Copy_of__2nd_Grade_Science"
    / "originals"
    / "Copy_of__2nd_Grade_Science.docx"
)

_LI_RE = re.compile(r"learning\s+intentions?", re.I)
_SC_RE = re.compile(r"success\s+criteria", re.I)

# Rough "Lesson 1 / Describe Matter" module band (paragraph-order, before Lesson 2: …).
_MODULE_LESSON1_START = re.compile(
    r"(?i)lesson\s+1\s*:.*describe\s+matter",
)
_MODULE_LESSON2_START = re.compile(r"(?i)^lesson\s+2\s*:")

# Table body often contains the module title (preceding paragraphs may still be pacing text).
_LESSON1_DESCRIBE_MATTER_IN_TABLE = re.compile(
    r"(?i)lesson\s+1\s*:.*describe\s+matter",
)


def _xml_local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _flatten_cell_content(content: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Plain text from cell elements; return nested tables separately."""
    parts: List[str] = []
    nested: List[Dict[str, Any]] = []
    for item in content:
        if item.get("type") == "paragraph":
            t = (item.get("text") or "").strip()
            if t:
                parts.append(t)
        elif item.get("type") == "table":
            nested.append(item)
            parts.append(_flatten_table_plain(item))
    return " ".join(parts), nested


def _flatten_table_plain(table: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for row in table.get("rows", []):
        for cell in row.get("cells", []):
            txt, _ = _flatten_cell_content(cell.get("content", []))
            if txt:
                chunks.append(txt)
    return " ".join(chunks)


def _table_shape(table: Dict[str, Any]) -> Tuple[int, int]:
    rows = table.get("rows") or []
    nrows = len(rows)
    ncols = max((len(r.get("cells") or []) for r in rows), default=0)
    return nrows, ncols


def _walk_nested_tables(
    table: Dict[str, Any],
    path: str,
    events: List[Dict[str, Any]],
    preceding_context: str,
    in_lesson1_module: bool,
) -> None:
    """Record one row per table node (including nested) with LI/SC + day label signals."""
    flat = _flatten_table_plain(table)
    nrows, ncols = _table_shape(table)
    labels = day_labels_in_text(flat)
    has_li = bool(_LI_RE.search(flat))
    has_sc = bool(_SC_RE.search(flat))
    events.append(
        {
            "path": path,
            "depth": table.get("depth", 0),
            "shape_rows": nrows,
            "shape_cols_max": ncols,
            "has_learning_intention": has_li,
            "has_success_criteria": has_sc,
            "day_labels_ordered": labels,
            "plain_text_preview": flat[:1200] + ("..." if len(flat) > 1200 else ""),
            "preceding_context_tail": preceding_context[-700:] if preceding_context else "",
            "in_lesson1_describe_matter_band": in_lesson1_module,
            "table_contains_lesson1_describe_matter_header": bool(
                _LESSON1_DESCRIBE_MATTER_IN_TABLE.search(flat)
            ),
            "science_li_sc_day_candidate": bool(labels and has_li and has_sc),
        }
    )
    for ri, row in enumerate(table.get("rows") or []):
        for ci, cell in enumerate(row.get("cells") or []):
            _, nested = _flatten_cell_content(cell.get("content", []))
            for ti, nt in enumerate(nested):
                _walk_nested_tables(
                    nt,
                    f"{path}/r{ri}c{ci}/t{ti}",
                    events,
                    preceding_context,
                    in_lesson1_module,
                )


def run_diagnosis(docx_path: Path) -> Dict[str, Any]:
    doc = Document(str(docx_path))
    parser = RecursiveTableParser()
    parser.doc = doc

    context_lines: deque[str] = deque(maxlen=24)
    in_l1 = False
    top_table_index = 0
    table_events: List[Dict[str, Any]] = []
    order_log: List[Dict[str, Any]] = []

    for element in doc.element.body:
        tag = _xml_local_name(element.tag)
        if tag == "p":
            p_json = parser._parse_paragraph(element)
            text = (p_json.get("text") or "").strip()
            if text:
                context_lines.append(text)
                if _MODULE_LESSON1_START.search(text):
                    in_l1 = True
                if in_l1 and _MODULE_LESSON2_START.match(text):
                    in_l1 = False
            continue

        if tag != "tbl":
            continue

        top_table_index += 1
        ctx = " ".join(context_lines)
        table_json = parser._parse_table(element, 0)
        nrows, ncols = _table_shape(table_json)
        flat_top = _flatten_table_plain(table_json)
        labels_top = day_labels_in_text(flat_top)
        order_log.append(
            {
                "top_table_index": top_table_index,
                "shape_rows": nrows,
                "shape_cols_max": ncols,
                "day_labels_top_level": labels_top,
                "has_li": bool(_LI_RE.search(flat_top)),
                "has_sc": bool(_SC_RE.search(flat_top)),
                "in_lesson1_band": in_l1,
                "context_tail": ctx[-500:] if ctx else "",
            }
        )
        _walk_nested_tables(
            table_json,
            f"t{top_table_index}",
            table_events,
            ctx,
            in_l1,
        )

    candidates = [e for e in table_events if e.get("science_li_sc_day_candidate")]
    l1_focus = [e for e in candidates if e.get("in_lesson1_describe_matter_band")]
    l1_header_tables = [
        e
        for e in candidates
        if e.get("table_contains_lesson1_describe_matter_header")
    ]

    return {
        "docx": str(docx_path.resolve()),
        "top_level_table_count": top_table_index,
        "nested_table_nodes_total": len(table_events),
        "li_sc_day_candidates": len(candidates),
        "li_sc_day_candidates_in_lesson1_band": len(l1_focus),
        "li_sc_day_candidates_lesson1_describe_matter_header": len(l1_header_tables),
        "order_log_sample": order_log[:40],
        "order_log_total": len(order_log),
        "candidates": candidates,
        "candidates_lesson1_band_only": l1_focus,
        "candidates_lesson1_describe_matter_header": l1_header_tables,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--docx",
        default="",
        help=f"Path to .docx (default: {_DEFAULT_DOCX} if that file exists)",
    )
    ap.add_argument(
        "--json-out",
        default="",
        help="Write full diagnosis JSON to this path",
    )
    ap.add_argument(
        "--print-candidates",
        action="store_true",
        help="Print candidate table paths and day labels to stdout",
    )
    args = ap.parse_args()

    docx = Path(args.docx) if args.docx else _DEFAULT_DOCX
    if not docx.is_file():
        print(
            "DOCX not found:",
            docx,
            "\nExport the unit tab with DocsClient or pass --docx.",
            file=sys.stderr,
        )
        return 2

    report = run_diagnosis(docx)

    print(
        f"docx={report['docx']}\n"
        f"top_level_tables={report['top_level_table_count']} "
        f"nested_nodes={report['nested_table_nodes_total']}\n"
        f"LI+SC+day_label candidates={report['li_sc_day_candidates']} "
        f"(paragraph band L1={report['li_sc_day_candidates_in_lesson1_band']}; "
        f"table header 'Lesson 1: … Describe Matter'={report['li_sc_day_candidates_lesson1_describe_matter_header']})"
    )

    if args.print_candidates:
        focus = report["candidates_lesson1_describe_matter_header"]
        if not focus:
            focus = report["candidates_lesson1_band_only"] or report["candidates"]
        for c in focus:
            print(
                f"\n--- path={c['path']} depth={c['depth']} "
                f"rows={c['shape_rows']} cols={c['shape_cols_max']} ---"
            )
            print("day_labels:", c["day_labels_ordered"])
            print("preview:", c["plain_text_preview"][:400].replace("\n", " "))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
