"""
Inspect one lesson standard across DB and (optionally) source Docs JSON text.

Usage:
  python tools/db/inspect_standard_fidelity.py --unit-id Math_3_U3_1W1IBU71 --lesson-number 1 --code NJSLS-MATH.CONTENT.4.NF.B.4 --doc-id 1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRAPER_DIR = _REPO_ROOT / "tools" / "scraper"
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))

from docs_client import DocsClient


def _iter_text_runs(node: Any):
    if isinstance(node, dict):
        tr = node.get("textRun")
        if isinstance(tr, dict) and isinstance(tr.get("content"), str):
            yield tr.get("content")
        for v in node.values():
            yield from _iter_text_runs(v)
    elif isinstance(node, list):
        for it in node:
            yield from _iter_text_runs(it)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit-id", required=True)
    ap.add_argument("--lesson-number", type=int, required=True)
    ap.add_argument("--code", required=True)
    ap.add_argument("--doc-id", default=None)
    ap.add_argument("--db", default=str(_REPO_ROOT / "data" / "curriculum.db"))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    q = """
    SELECT l.id, s.code, s.description
    FROM lesson_standards ls
    JOIN standards s ON s.code = ls.standard_code
    JOIN lessons l ON l.id = ls.lesson_id
    WHERE l.unit_id = ? AND l.lesson_number = ? AND s.code = ?
    """
    rows = cur.execute(q, (args.unit_id, args.lesson_number, args.code)).fetchall()
    conn.close()

    print("DB rows:", len(rows))
    for lesson_id, code, desc in rows:
        desc = desc or ""
        print("lesson_id:", lesson_id)
        print("code:", code)
        print("desc_len:", len(desc))
        print("desc_sample:", desc[:900])

    if args.doc_id:
        doc = DocsClient().get_document(args.doc_id)
        text = "".join(_iter_text_runs(doc))
        idx = text.find(args.code)
        print("docs_json_text_len:", len(text))
        print("code_index_in_docs_json_text:", idx)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(text), idx + 1200)
            print("docs_json_context:", text[start:end])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
