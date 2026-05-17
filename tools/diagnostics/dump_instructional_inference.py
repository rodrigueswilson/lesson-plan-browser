#!/usr/bin/env python3
"""
Print per-day instructional inference for debugging (Phase 1 evidence collection).

Usage:
  python tools/diagnostics/dump_instructional_inference.py path/to/content.json

The JSON may be a full extract dict (with table_content) or a raw table_content object.

For DB exports, point at a file containing content_json or embed:
  {"table_content": {"Monday": {"Unit/Lesson": "..."}, ...}}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from tools.batch_processor_pkg.slot_flow_extract import get_available_days_from_content
from tools.docx_parser.instructional_day import (
    _day_text_for_instructional_inference,
    infer_instructional_weekdays_from_table_content,
    is_instructional_lesson_day,
)
from tools.docx_parser.no_school import is_day_no_school


def _load(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "table_content" in data:
        return data
    if isinstance(data, dict) and any(
        k.lower().strip() in ("monday", "tuesday", "all days") for k in data.keys()
    ):
        return {"table_content": data}
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to JSON with table_content or full content dict",
    )
    args = parser.parse_args()

    payload = _load(args.json_path)
    tc = payload.get("table_content") if isinstance(payload, dict) else None
    if not tc:
        print("No table_content found.", file=sys.stderr)
        sys.exit(1)

    summary = get_available_days_from_content({"table_content": tc})
    inferred = infer_instructional_weekdays_from_table_content(tc)

    print("get_available_days_from_content:", summary)
    print("infer_instructional_weekdays_from_table_content:", inferred)
    print()

    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday")
    for day, day_content in tc.items():
        dl = day.lower().strip()
        if dl not in weekdays:
            continue
        primary = _day_text_for_instructional_inference(day_content)
        full = (
            " ".join(day_content.values())
            if isinstance(day_content, dict)
            else str(day_content)
        )
        ok = is_instructional_lesson_day(primary)
        print(f"{dl}:")
        print(f"  primary_text_for_inference ({len(primary)} chars): {primary[:200]!r}")
        if full != primary:
            print(f"  legacy_full_join ({len(full)} chars): {full[:200]!r}")
        print(f"  counts_as_instructional: {ok}")
        print(f"  is_day_no_school(primary_only): {is_day_no_school(primary)}")
        print(f"  is_day_no_school(full_join): {is_day_no_school(full)}")
        print()


if __name__ == "__main__":
    main()
