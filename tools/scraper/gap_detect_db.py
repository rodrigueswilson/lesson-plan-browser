import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.services.curriculum_gaps import (  # noqa: E402
    compute_planned_and_gaps,
    gap_summary_lines,
)


def detect_gaps(
    db_path: str,
    registry_path: str,
    planned_out: str,
    gap_out: str,
    scrapped_doc_ids_path: str,
) -> None:
    print(f"Connecting to {db_path}...")
    print(f"Loading scraped registry from {registry_path}...")
    if os.path.isfile(scrapped_doc_ids_path):
        print(f"Loading scrapped doc ids from {scrapped_doc_ids_path}...")
    planned, gaps, total_found, new_gaps = compute_planned_and_gaps(
        db_path, registry_path, scrapped_doc_ids_path
    )
    print(f"Total planned documents found in DB: {total_found}")
    print(f"New gaps identified (not yet scraped): {new_gaps}")

    print("\n" + "=" * 80)
    print(f"{'GRADE':<15} | {'SUBJECT':<20} | {'UNIQUE GAPS':<12} | {'KEY UNITS'}")
    print("-" * 80)
    for line in gap_summary_lines(gaps):
        print(line)
    print("=" * 80 + "\n")

    with open(planned_out, "w", encoding="utf-8") as f:
        json.dump(planned, f, indent=2)
    with open(gap_out, "w", encoding="utf-8") as f:
        json.dump(gaps, f, indent=2)
    print(f"Planned registry saved to: {planned_out}")
    print(f"Gap list saved to: {gap_out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(_REPO_ROOT / "data" / "lesson_planner.db"))
    ap.add_argument(
        "--registry",
        default=str(_REPO_ROOT / "reference_docs" / "scraped_registry.json"),
    )
    ap.add_argument(
        "--planned-out",
        default=str(_REPO_ROOT / "reference_docs" / "planned_registry.json"),
    )
    ap.add_argument(
        "--gap-out",
        default=str(_REPO_ROOT / "reference_docs" / "db_curriculum_gaps.json"),
    )
    ap.add_argument(
        "--scrapped-doc-ids",
        default=str(_REPO_ROOT / "reference_docs" / "scrapped_curriculum_doc_ids.json"),
        help="Doc ids excluded from gap counts (same directory default as scraped_registry).",
    )
    ns = ap.parse_args()
    detect_gaps(ns.db, ns.registry, ns.planned_out, ns.gap_out, ns.scrapped_doc_ids)
