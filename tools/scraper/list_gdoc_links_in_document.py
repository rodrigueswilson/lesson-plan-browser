"""
List Google Doc file ids linked from a Google Doc (hub / pacing / curriculum guide).

Uses the Docs API via DocsClient (same OAuth as the scraper). Helpful when unit teacher
guides are linked from a parent pacing document but not yet listed in scraped_registry.json.

Usage (repo root, with credentials under tools/scraper/credentials/):

  python tools/scraper/list_gdoc_links_in_document.py --doc-id 1GXG_j596lObLzq78xnMqatXrC145DzVVCX5DZVEL0ko

Optional: --include-self to print the root doc id as well.

Output: one id per line (deduped, sorted) suitable for manual copy into g2_math_corpus /
scraped_registry after you confirm titles in Drive.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRAPER_DIR = Path(__file__).resolve().parent
if str(_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_DIR))

_DOC_ID_IN_URL = re.compile(
    r"https?://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)(?:/|$|\?)",
    re.IGNORECASE,
)


def _collect_doc_ids_from_api_payload(payload: object) -> set[str]:
    """Scan JSON-serialized API tree for docs.google.com/document/d/... URLs."""
    raw = json.dumps(payload, default=str)
    return set(_DOC_ID_IN_URL.findall(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc-id", required=True, help="Google Doc file id (hub / pacing doc).")
    ap.add_argument(
        "--include-self",
        action="store_true",
        help="Include --doc-id in the printed set (default: exclude root).",
    )
    args = ap.parse_args()

    from docs_client import DocsClient

    doc = DocsClient().get_document(args.doc_id)
    if not doc:
        return 1

    found = _collect_doc_ids_from_api_payload(doc)
    if not args.include_self:
        found.discard(args.doc_id)

    for fid in sorted(found):
        print(fid)
    print(f"# count={len(found)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
