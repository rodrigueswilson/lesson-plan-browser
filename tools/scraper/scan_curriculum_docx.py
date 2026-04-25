"""
Stream a curriculum DOCX and list paragraph hits for SubjectConfig lesson_title / standards.

Usage (repo root):
  python tools/scraper/scan_curriculum_docx.py path/to/file.docx --subject Science
  python tools/scraper/scan_curriculum_docx.py path/to/file.docx --subject Science --json-out reference_docs/scraped/grade3_science/scan_preview.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRAPER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRAPER_DIR.parent.parent
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from subject_config import SubjectConfig
from table_extractor import RecursiveTableParser


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx", help="Path to .docx")
    ap.add_argument("--subject", default="Science", help="SubjectConfig key (Science, Math, ELA)")
    ap.add_argument("--json-out", default=None, help="Write scan summary JSON to this path")
    args = ap.parse_args()

    docx = Path(args.docx)
    if not docx.is_file():
        print("File not found:", docx, file=sys.stderr)
        return 2

    cfg = SubjectConfig.get_config(args.subject)
    lesson_pat: re.Pattern = cfg["patterns"]["lesson_title"]
    std_pat: re.Pattern = cfg["patterns"]["standards"]

    parser = RecursiveTableParser()
    stream = list(parser.parse_to_stream(str(docx)))

    lesson_hits: list[dict] = []
    std_hits: list[dict] = []
    para_n = 0

    for i, item in enumerate(stream):
        if item.get("type") != "paragraph":
            continue
        para_n += 1
        text = (item.get("text") or "").strip()
        if not text:
            continue
        m = lesson_pat.match(text)
        if m:
            lesson_hits.append(
                {
                    "stream_index": i,
                    "text": text[:500],
                    "groups": m.groups(),
                }
            )
        for std in std_pat.findall(text):
            if std:
                std_hits.append({"stream_index": i, "token": std, "line": text[:240]})

    summary = {
        "docx": str(docx.resolve()),
        "subject": args.subject,
        "stream_items": len(stream),
        "paragraph_items": para_n,
        "lesson_title_hits": len(lesson_hits),
        "standards_token_hits": len(std_hits),
        "lessons": lesson_hits[:200],
        "standards_sample": std_hits[:80],
    }

    print(
        f"Stream items={len(stream)} paragraphs~={para_n} "
        f"lesson_hits={len(lesson_hits)} standards_hits={len(std_hits)}",
        flush=True,
    )
    for h in lesson_hits[:25]:
        print(f"  L  idx={h['stream_index']}: {h['text'][:120]}...", flush=True)
    if len(lesson_hits) > 25:
        print(f"  ... and {len(lesson_hits) - 25} more (see --json-out)", flush=True)

    if args.json_out:
        out_p = Path(args.json_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Wrote", out_p.resolve(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
