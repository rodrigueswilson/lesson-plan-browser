"""
Batch ingest for Phase 3 Grade 3 Math corpus (Google Doc export + ingest_to_curriculum).

Requires Drive/Docs OAuth (tools/scraper/credentials/). Run from repo root:

  python tools/db/ingest_g3_math_phase3_corpus.py
  python tools/db/ingest_g3_math_phase3_corpus.py --unit-id Math_3_U6_1VozISaY
  python tools/db/ingest_g3_math_phase3_corpus.py --dry-run

After each unit, runs verify_curriculum_db against the newest ingest_reports/*.json
(unless --no-verify). Set SKIP_VERIFY=1 in the environment to skip verification
only (same as --no-verify).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DB_DIR = Path(__file__).resolve().parent
if str(_DB_DIR) not in sys.path:
    sys.path.insert(0, str(_DB_DIR))


def _newest_ingest_report() -> Path | None:
    root = _REPO_ROOT / "ingest_reports"
    if not root.is_dir():
        return None
    json_files = list(root.glob("*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda p: p.stat().st_mtime)


def _run_verify(report: Path | None) -> int:
    cmd = [
        sys.executable,
        str(_REPO_ROOT / "tools" / "scraper" / "verify_curriculum_db.py"),
    ]
    if report and report.is_file():
        cmd.extend(["--ingest-report", str(report)])
    r = subprocess.run(cmd, cwd=str(_REPO_ROOT))
    return r.returncode


def main() -> int:
    from g3_math_phase3_corpus import G3_MATH_PHASE3_UNITS

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--unit-id",
        help="Ingest only this unit_id (must match a corpus row).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands only.",
    )
    ap.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verify_curriculum_db after each unit.",
    )
    args = ap.parse_args()

    skip_verify = args.no_verify or os.environ.get("SKIP_VERIFY", "").strip() in (
        "1",
        "true",
        "yes",
    )

    units = list(G3_MATH_PHASE3_UNITS)
    if args.unit_id:
        units = [u for u in units if u.unit_id == args.unit_id]
        if not units:
            print("Unknown --unit-id; not in G3_MATH_PHASE3_UNITS.", file=sys.stderr)
            return 2

    ingest_script = _REPO_ROOT / "tools" / "db" / "ingest_wave_unit.py"
    for spec in units:
        cmd = [
            sys.executable,
            str(ingest_script),
            "--unit-id",
            spec.unit_id,
            "--grade",
            "3",
            "--subject",
            "Math",
            "--unit-number",
            str(spec.unit_number),
            "--title",
            spec.title,
            "--doc-id",
            spec.doc_id,
        ]
        if args.dry_run:
            print("Would run:", subprocess.list2cmdline(cmd))
            continue
        r = subprocess.run(cmd, cwd=str(_REPO_ROOT))
        if r.returncode != 0:
            return r.returncode
        if not skip_verify:
            report = _newest_ingest_report()
            if report:
                print(f"Running verify_curriculum_db.py --ingest-report {report}", flush=True)
            vr = _run_verify(report)
            if vr != 0:
                return vr
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
