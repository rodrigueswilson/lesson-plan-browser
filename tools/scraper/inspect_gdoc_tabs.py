"""
Inspect Google Docs tab structure (navigation tabs) for export / split planning.

Uses a saved Docs API JSON snapshot (from export_doc_ids_to_docx fallback) or a live
documents.get(includeTabsContent=true) call.

Usage (repo root):
  python tools/scraper/inspect_gdoc_tabs.py --json-path reference_docs/scraped/grade3_ela_exports/*.docs-api.json
  python tools/scraper/inspect_gdoc_tabs.py 1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY

Options:
  --chars   Approximate character count of visible text per tab (paragraph + table cells)
  --write-json  With live fetch, also write full API response to PATH (large)

See tools/scraper/gdoc_tab_to_docx.py to emit a .docx for a single tab from the JSON snapshot.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.scraper.docs_client import DocsClient


def _text_len_in_structural_elements(elements: List[Dict[str, Any]]) -> int:
    n = 0
    for el in elements or []:
        para = el.get("paragraph")
        if para:
            for item in para.get("elements") or []:
                tr = item.get("textRun")
                if tr and tr.get("content"):
                    n += len(tr["content"])
        tbl = el.get("table")
        if tbl:
            for row in tbl.get("tableRows") or []:
                for cell in row.get("tableCells") or []:
                    n += _text_len_in_structural_elements(cell.get("content") or [])
    return n


def _tab_stats(tab: Dict[str, Any], count_chars: bool) -> Tuple[int, int, int]:
    """Returns (structural_element_count, approx_chars, json_serial_size)."""
    body = (tab.get("documentTab") or {}).get("body") or {}
    content = body.get("content") or []
    n_el = len(content)
    chars = _text_len_in_structural_elements(content) if count_chars else 0
    blob = json.dumps(tab, ensure_ascii=False)
    return n_el, chars, len(blob.encode("utf-8"))


def _walk_tabs(
    tabs: List[Dict[str, Any]],
    depth: int,
    count_chars: bool,
    lines: List[str],
) -> None:
    ind = "  " * depth
    for i, tab in enumerate(tabs or []):
        props = tab.get("tabProperties") or {}
        tid = props.get("tabId", "?")
        title = props.get("title", "(untitled)")
        n_el, chars, jbytes = _tab_stats(tab, count_chars)
        char_part = f" approx_chars={chars}" if count_chars else ""
        lines.append(
            f"{ind}{i + 1}. tabId={tid} title={title!r} elements={n_el}{char_part} json_bytes~={jbytes}"
        )
        _walk_tabs(tab.get("childTabs") or [], depth + 1, count_chars, lines)


def inspect_document(doc: Dict[str, Any], count_chars: bool) -> str:
    lines: List[str] = []
    lines.append(f"documentId: {doc.get('documentId')}")
    lines.append(f"title: {doc.get('title')}")
    tabs = doc.get("tabs")
    if not tabs:
        lines.append("tabs: (empty or missing; try includeTabsContent=true on documents.get)")
        body = doc.get("body")
        if body:
            content = body.get("content") or []
            lines.append(f"legacy body.content elements: {len(content)}")
        return "\n".join(lines)
    lines.append(f"tabs (top-level count): {len(tabs)}")
    _walk_tabs(tabs, 0, count_chars, lines)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("document_id", nargs="?", help="Google Doc ID (if not using --json-path)")
    ap.add_argument(
        "--json-path",
        metavar="PATH",
        help="Path to a .docs-api.json file from export_doc_ids_to_docx fallback",
    )
    ap.add_argument(
        "--chars",
        action="store_true",
        help="Approximate visible text length per tab (slower on huge JSON)",
    )
    ap.add_argument(
        "--write-json",
        metavar="PATH",
        help="With live fetch: write full API response to this path",
    )
    args = ap.parse_args()

    if args.json_path:
        p = Path(args.json_path)
        if not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            return 1
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif args.document_id:
        client = DocsClient()
        doc = client.get_document(args.document_id)
        if not doc:
            print("Failed to fetch document.", file=sys.stderr)
            return 1
        if args.write_json:
            out = Path(args.write_json)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Wrote {out}", file=sys.stderr)
    else:
        ap.print_help()
        print("\nProvide --json-path or DOCUMENT_ID.", file=sys.stderr)
        return 2

    print(inspect_document(doc, args.chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
