"""
Script-aided UI spot-check for Wave 2 ELA units.

Checks first/middle/last lessons per unit for:
- structured payload presence
- heading/bullet readability signals in procedures
- Daily Instructional Task / Read Aloud heading-vs-bullet behavior
- vocabulary/resources cell presence
- Google Doc links have matching rows in resources
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from typing import Dict, List, Tuple

GOOGLE_DOC_RE = re.compile(r"https://docs\.google\.com/document/d/([A-Za-z0-9_-]+)")


def _pick_lesson_numbers(all_numbers: List[int]) -> List[int]:
    if not all_numbers:
        return []
    ordered = sorted(all_numbers)
    mid = ordered[len(ordered) // 2]
    picks = [ordered[0], mid, ordered[-1]]
    out: List[int] = []
    for n in picks:
        if n not in out:
            out.append(n)
    return out


def _check_lesson(
    cur: sqlite3.Cursor,
    unit_id: str,
    lesson_number: int,
) -> Dict[str, object]:
    row = cur.execute(
        """
        SELECT title, ela_lesson_plan_structured
        FROM lessons
        WHERE unit_id = ? AND lesson_number = ?
        """,
        (unit_id, lesson_number),
    ).fetchone()
    if not row:
        return {"lesson_number": lesson_number, "error": "lesson_not_found"}

    raw = (row[1] or "").strip()
    if not raw:
        return {"lesson_number": lesson_number, "title": row[0], "error": "structured_missing"}
    plan = json.loads(raw)

    anticipatory = str(plan.get("anticipatory_set_html") or "")
    routines = str(plan.get("instructional_routines_assessments_html") or "")
    vocab = str(plan.get("vocabulary_cell_html") or "")
    resources = str(plan.get("instructional_resources_cell_html") or "")

    has_bold = "<b>" in anticipatory or "<strong>" in anticipatory
    has_bullets = "<ul>" in anticipatory and "<li>" in anticipatory
    has_daily_heading = "<b>Daily Instructional Task:</b>" in routines
    has_read_aloud_heading = "<b>Read Aloud" in routines
    has_bolded_list_item = "<li><b>" in routines

    gids = sorted(
        set(
            GOOGLE_DOC_RE.findall(
                " ".join(v for v in plan.values() if isinstance(v, str))
            )
        )
    )
    missing_resource_rows: List[str] = []
    for gid in gids:
        r = cur.execute("SELECT id FROM resources WHERE id = ?", (gid,)).fetchone()
        if not r:
            missing_resource_rows.append(gid)

    return {
        "lesson_number": lesson_number,
        "title": row[0],
        "has_structured": True,
        "anticipatory_has_bold": has_bold,
        "anticipatory_has_bullets": has_bullets,
        "daily_heading_bold": has_daily_heading,
        "read_aloud_heading_bold": has_read_aloud_heading,
        "routines_has_bolded_li": has_bolded_list_item,
        "vocabulary_cell_non_empty": bool(vocab.strip()),
        "resources_cell_non_empty": bool(resources.strip()),
        "google_doc_links": len(gids),
        "missing_resource_rows": missing_resource_rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=r"d:\LP\data\curriculum.db")
    ap.add_argument(
        "--units",
        nargs="+",
        required=True,
        help="Unit ids to spot-check",
    )
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    print("Wave 2 UI spot-check report")
    for unit_id in args.units:
        nums = [
            int(r[0])
            for r in cur.execute(
                "SELECT lesson_number FROM lessons WHERE unit_id = ? ORDER BY lesson_number",
                (unit_id,),
            ).fetchall()
        ]
        picks = _pick_lesson_numbers(nums)
        print(f"\nUnit {unit_id}: lessons sampled={picks}")
        for ln in picks:
            result = _check_lesson(cur, unit_id, ln)
            print(json.dumps(result, ensure_ascii=False))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
