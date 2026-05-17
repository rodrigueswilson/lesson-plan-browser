"""
Dump hyperlink runs from RecursiveTableParser.parse_to_stream for apples-to-apples
comparison with Docling Markdown (e.g. docling_test_hyperlink.md).

Usage (repo root):
  python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py
  python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py path/to/file.docx --json-out out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

_SPIKE_DIR = Path(__file__).resolve().parent
# Spike lives at docs/research/spikes/<this_dir>/; parents[3] == repo root.
_REPO_ROOT = _SPIKE_DIR.parents[3]
_SCRAPER_DIR = _REPO_ROOT / "tools" / "scraper"
for p in (_SCRAPER_DIR, _REPO_ROOT):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from table_extractor import RecursiveTableParser  # noqa: E402


def walk_stream_shapes(item: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Yield paragraph dicts from parse_to_stream items (paragraph, property, nested table)."""
    t = item.get("type")
    if t == "paragraph":
        yield item
        return
    if t == "property":
        for sub in item.get("content") or []:
            if isinstance(sub, dict):
                yield from walk_stream_shapes(sub)
        return
    if t == "table":
        for row in item.get("rows") or []:
            for cell in row.get("cells") or []:
                for sub in cell.get("content") or []:
                    if isinstance(sub, dict):
                        yield from walk_stream_shapes(sub)


def link_runs_from_paragraph(p: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, run in enumerate(p.get("runs") or []):
        style = run.get("style") or {}
        if not (style.get("link") and style.get("url")):
            continue
        out.append(
            {
                "run_index": i,
                "text": run.get("text") or "",
                "url": style.get("url"),
                "google_id": style.get("google_id"),
            }
        )
    return out


def main() -> int:
    default_docx = (
        _REPO_ROOT / "docs" / "archive" / "test-files" / "test_hyperlink_robustness.docx"
    )
    default_out = _REPO_ROOT / "docs" / "research" / "repos" / "lp_hyperlink_dump_test_hyperlink.json"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "docx",
        nargs="?",
        default=str(default_docx),
        help="Path to .docx (default: test_hyperlink_robustness.docx)",
    )
    ap.add_argument("--json-out", default=str(default_out), help="Write JSON here")
    args = ap.parse_args()

    docx = Path(args.docx)
    if not docx.is_file():
        print("File not found:", docx, file=sys.stderr)
        return 2

    parser = RecursiveTableParser(db_path=str(_REPO_ROOT / "data" / "curriculum.db"))
    parser.enrich_leading_cell_labels = False

    stream: List[Dict[str, Any]] = list(parser.parse_to_stream(str(docx)))
    occurrences: List[Dict[str, Any]] = []
    links_flat: List[Dict[str, Any]] = []

    for si, raw in enumerate(stream):
        for para in walk_stream_shapes(raw):
            runs_with_links = link_runs_from_paragraph(para)
            if not runs_with_links:
                continue
            html = parser.json_to_html(para).strip()
            rec: Dict[str, Any] = {
                "stream_index": si,
                "paragraph_text": para.get("text") or "",
                "runs_with_links": runs_with_links,
                "paragraph_html": html,
            }
            occurrences.append(rec)
            for r in runs_with_links:
                links_flat.append(
                    {
                        "stream_index": si,
                        "text": r["text"],
                        "url": r["url"],
                        "google_id": r.get("google_id"),
                    }
                )

    payload = {
        "source_docx": str(docx.resolve()),
        "parser": "RecursiveTableParser.parse_to_stream + walk_stream_shapes",
        "stream_top_level_items": len(stream),
        "paragraphs_with_hyperlinks": len(occurrences),
        "hyperlink_run_count": len(links_flat),
        "occurrences": occurrences,
        "links_flat": links_flat,
    }

    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({payload['hyperlink_run_count']} hyperlink runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
