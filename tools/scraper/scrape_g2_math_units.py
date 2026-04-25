"""
Re-scrape all Grade 2 Math unit Google Docs in g2_math_corpus (depth 4, --force).

Uses the same output layout as the Unit 1 PowerShell helper. Run from repo root:

  python tools/scraper/scrape_g2_math_units.py
  python tools/scraper/scrape_g2_math_units.py --dry-run

Does not run ingest; use tools/db/ingest_g2_math_corpus.py or grade2_math_scrape_and_ingest.ps1.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DB_DIR = _REPO_ROOT / "tools" / "db"
if str(_DB_DIR) not in sys.path:
    sys.path.insert(0, str(_DB_DIR))


def main() -> int:
    from g2_math_corpus import G2_MATH_UNITS

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print scrape commands only.")
    ap.add_argument(
        "--unit-id",
        help="Scrape only this corpus unit_id (e.g. Math_2_U4_1x8ll9eW).",
    )
    args = ap.parse_args()

    units = list(G2_MATH_UNITS)
    if args.unit_id:
        units = [u for u in units if u.unit_id == args.unit_id]
        if not units:
            print("Unknown --unit-id; not in G2_MATH_UNITS.", file=sys.stderr)
            return 2

    for spec in units:
        cmd = [
            sys.executable,
            "-m",
            "tools.scraper.main",
            spec.doc_id,
            "--depth",
            "4",
            "--out",
            "reference_docs/scraped",
            "--force",
        ]
        label = f"Unit {spec.unit_number} ({spec.registry_key})"
        if args.dry_run:
            print(f"Would scrape {label}: {subprocess.list2cmdline(cmd)}")
            continue
        print(f"Scraping {label} doc {spec.doc_id}...", flush=True)
        r = subprocess.run(cmd, cwd=str(_REPO_ROOT))
        if r.returncode != 0:
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
