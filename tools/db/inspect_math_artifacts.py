"""
Inspect equation/math representation around a standards code in Docs JSON and DOCX XML.

Usage:
  python tools/db/inspect_math_artifacts.py --doc-id 1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4 --code NJSLS-MATH.CONTENT.4.NF.B.4
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRAPER_DIR = _REPO_ROOT / "tools" / "scraper"
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))

from docs_client import DocsClient


def _collect_paragraph_elements(node: Any):
    if isinstance(node, dict):
        pe = node.get("paragraphElement")
        if isinstance(pe, dict):
            yield pe
        for v in node.values():
            yield from _collect_paragraph_elements(v)
    elif isinstance(node, list):
        for it in node:
            yield from _collect_paragraph_elements(it)


def _count_key(node: Any, key: str) -> int:
    if isinstance(node, dict):
        n = 1 if key in node else 0
        return n + sum(_count_key(v, key) for v in node.values())
    if isinstance(node, list):
        return sum(_count_key(it, key) for it in node)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--code", required=True)
    args = ap.parse_args()

    client = DocsClient()
    doc = client.get_document(args.doc_id)
    if not doc:
        raise RuntimeError("Failed to fetch Docs JSON")

    elements = list(_collect_paragraph_elements(doc))
    eq_count = _count_key(doc, "equation")
    inline_obj_count = _count_key(doc, "inlineObjectElement")

    # Locate first code occurrence in text runs and inspect nearby paragraphElements.
    code_idx = -1
    for i, e in enumerate(elements):
        tr = e.get("textRun")
        if isinstance(tr, dict) and args.code in str(tr.get("content", "")):
            code_idx = i
            break

    nearby = []
    if code_idx >= 0:
        start = max(0, code_idx - 40)
        end = min(len(elements), code_idx + 120)
        for e in elements[start:end]:
            if "equation" in e:
                nearby.append("equation:{}")
            tr = e.get("textRun")
            if isinstance(tr, dict):
                txt = str(tr.get("content", "")).strip()
                if txt:
                    nearby.append(txt[:140])

    doc_json_text = json.dumps(doc, ensure_ascii=False)
    code_pos_json = doc_json_text.find(args.code)
    json_snippet = ""
    if code_pos_json >= 0:
        s = max(0, code_pos_json - 1600)
        e = min(len(doc_json_text), code_pos_json + 3600)
        json_snippet = doc_json_text[s:e]

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        docx_path = tmp.name
    try:
        ok = client.export_document(
            args.doc_id,
            docx_path,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        if not ok:
            raise RuntimeError("Failed to export DOCX")

        with zipfile.ZipFile(docx_path, "r") as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        omml_count = xml.count("<m:oMath")
        drawing_count = xml.count("<w:drawing")
        pict_count = xml.count("<w:pict")
        code_pos = xml.find(args.code)
        snippet = ""
        if code_pos >= 0:
            s = max(0, code_pos - 800)
            e = min(len(xml), code_pos + 2400)
            snippet = xml[s:e]

        result = {
            "doc_id": args.doc_id,
            "code": args.code,
            "docs_json_equation_elements": eq_count,
            "docs_json_inline_object_elements": inline_obj_count,
            "code_found_in_docs_json_nearby": code_idx >= 0,
            "docs_json_nearby_excerpt": nearby[:80],
            "code_found_in_docs_json_raw": code_pos_json >= 0,
            "docs_json_snippet_around_code": json_snippet,
            "docx_document_xml_omml_count": omml_count,
            "docx_document_xml_drawing_count": drawing_count,
            "docx_document_xml_pict_count": pict_count,
            "code_found_in_docx_xml": code_pos >= 0,
            "docx_xml_snippet_around_code": snippet[:4000],
        }
        out_dir = _REPO_ROOT / "docs" / "curriculum" / "research-notes" / "export-vs-parser"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"math-artifacts-{args.doc_id}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(out_path)
        return 0
    finally:
        if os.path.exists(docx_path):
            os.remove(docx_path)


if __name__ == "__main__":
    raise SystemExit(main())
