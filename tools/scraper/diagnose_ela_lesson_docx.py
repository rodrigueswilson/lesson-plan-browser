"""
Debug helper: walk a teacher-guide DOCX and report ELA table detection.

Usage (repo root):
  python tools/scraper/diagnose_ela_lesson_docx.py path/to/Grade_2_Unit_8.docx
"""
from __future__ import annotations

import argparse
import os
import sys

_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRAPER_DIR))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _SCRAPER_DIR not in sys.path:
    sys.path.insert(0, _SCRAPER_DIR)

from docx import Document  # noqa: E402

try:
    from tools.scraper.ela_lesson_plan_table import (  # noqa: E402
        find_ela_lesson_plan_anchor,
        is_ela_lesson_plan_table,
        parse_ela_lesson_plan_table,
    )
    from tools.scraper.ela_summary_table import is_summary_key_learning_table  # noqa: E402
    from tools.scraper.table_extractor import RecursiveTableParser  # noqa: E402
except ImportError:
    from ela_lesson_plan_table import (  # noqa: E402
        find_ela_lesson_plan_anchor,
        is_ela_lesson_plan_table,
        parse_ela_lesson_plan_table,
    )
    from ela_summary_table import is_summary_key_learning_table  # noqa: E402
    from table_extractor import RecursiveTableParser  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx", help="Path to ELA teacher-guide DOCX")
    args = ap.parse_args()
    path = os.path.abspath(args.docx)
    if not os.path.isfile(path):
        print(f"Not found: {path}", file=sys.stderr)
        return 1

    parser = RecursiveTableParser(db_path=os.path.join(_REPO_ROOT, "data", "curriculum.db"))
    doc = Document(path)
    tbl_idx = 0
    for element in doc.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag != "tbl":
            continue
        table_json = parser._parse_table(element, 0)
        rows = table_json.get("rows") or []
        summary = is_summary_key_learning_table(table_json)
        plan = is_ela_lesson_plan_table(table_json)
        anchor = find_ela_lesson_plan_anchor(rows)
        preview = []
        for ri, row in enumerate(rows[:3]):
            cells = row.get("cells") or []
            bits = []
            for ci, c in enumerate(cells[:4]):
                plain = " ".join(
                    (p.get("text") or "") for p in c.get("content", []) if p.get("type") == "paragraph"
                ).strip()
                bits.append(f"c{ci}={plain[:80]!r}")
            preview.append(f"  r{ri}: " + " | ".join(bits))
        print(f"--- table {tbl_idx} rows={len(rows)} summary={summary} lesson_plan={plan} anchor={anchor}")
        print("\n".join(preview))
        if plan:
            def _htmlize(content: list) -> str:
                return parser.json_to_html(content)

            parsed = parse_ela_lesson_plan_table(table_json, _htmlize)
            ln = parsed.get("lesson_number") if parsed else None
            keys = sorted(k for k in (parsed or {}) if k.endswith("_html") or k in ("lesson_number", "lesson_title"))
            print(f"  parsed lesson_number={ln} keys={keys}")
        tbl_idx += 1
    print(f"Total tables: {tbl_idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
