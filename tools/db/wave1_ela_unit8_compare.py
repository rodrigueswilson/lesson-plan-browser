"""
Wave comparison report for ELA units.

Checks:
- Lesson coverage and structured-plan presence.
- SSOT guard (`ela_key_learning_summary` should be empty when structured exists).
- Structured-cell coverage across key lesson-plan fields.
- Link persistence: Google Doc IDs in structured HTML should exist in `resources`.

Usage:
  python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_2_U8_sample
  python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_3_U8_sample
  python tools/db/wave1_ela_unit8_compare.py --list-ela
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict

DEFAULT_UNIT_ID = "ELA_2_U8_sample"
GOOGLE_DOC_ID_RE = re.compile(r"https://docs\.google\.com/document/d/([A-Za-z0-9_-]+)")

KEY_FIELDS = [
    "learning_intention_html",
    "success_criteria_html",
    "njsls_standards_html",
    "key_questions_html",
    "instructional_routines_assessments_html",
    "vocabulary_cell_html",
    "instructional_resources_cell_html",
    "anticipatory_set_html",
    "learning_procedures_html",
    "engagement_with_content_html",
    "daily_instructional_task_html",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--unit-id",
        default=DEFAULT_UNIT_ID,
        help="Unit id to compare (default: ELA_2_U8_sample)",
    )
    ap.add_argument(
        "--list-ela",
        action="store_true",
        help="List Grade 2/3 ELA units with lesson and structured counts, then exit.",
    )
    ap.add_argument(
        "--db",
        default=r"d:\LP\data\curriculum.db",
        help="Path to curriculum.db",
    )
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if args.list_ela:
        rows = cur.execute(
            """
            SELECT u.id, u.grade, u.unit_number, u.title,
                   COUNT(l.id) AS lesson_count,
                   SUM(CASE WHEN l.ela_lesson_plan_structured IS NOT NULL
                             AND TRIM(l.ela_lesson_plan_structured) != ''
                            THEN 1 ELSE 0 END) AS structured_count
            FROM units u
            LEFT JOIN lessons l ON l.unit_id = u.id
            WHERE u.subject = 'ELA' AND u.grade IN (2, 3)
            GROUP BY u.id, u.grade, u.unit_number, u.title
            ORDER BY u.grade, u.unit_number
            """
        ).fetchall()
        print("ELA Grade 2/3 units:")
        for r in rows:
            print(
                f"- {r['id']} | G{r['grade']} U{r['unit_number']} | "
                f"lessons={r['lesson_count']} structured={r['structured_count']} | {r['title']}"
            )
        conn.close()
        return 0

    unit_id = args.unit_id
    lessons = cur.execute(
        """
        SELECT id, lesson_number, title, ela_lesson_plan_structured, ela_key_learning_summary
        FROM lessons
        WHERE unit_id = ?
        ORDER BY lesson_number
        """,
        (unit_id,),
    ).fetchall()

    print(f"Wave report for {unit_id}")
    print(f"- total lessons in DB: {len(lessons)}")

    missing_structured: list[int] = []
    summary_present: list[int] = []
    field_counts: dict[str, int] = defaultdict(int)
    links_per_lesson: list[tuple[int, int]] = []
    all_google_ids: set[str] = set()

    for row in lessons:
        lesson_num = int(row["lesson_number"])
        raw = (row["ela_lesson_plan_structured"] or "").strip()
        if not raw:
            missing_structured.append(lesson_num)
            continue
        plan = json.loads(raw)

        if (row["ela_key_learning_summary"] or "").strip():
            summary_present.append(lesson_num)

        for f in KEY_FIELDS:
            v = plan.get(f)
            if isinstance(v, str) and v.strip():
                field_counts[f] += 1

        html_blob = " ".join(v for v in plan.values() if isinstance(v, str))
        lesson_ids = set(GOOGLE_DOC_ID_RE.findall(html_blob))
        all_google_ids.update(lesson_ids)
        links_per_lesson.append((lesson_num, len(lesson_ids)))

    print(f"- lessons missing structured plan: {missing_structured or 'none'}")
    print(f"- lessons with unexpected ela_key_learning_summary: {summary_present or 'none'}")

    print("- key field coverage (count of lessons with non-empty field):")
    for f in KEY_FIELDS:
        print(f"  - {f}: {field_counts[f]}/{len(lessons)}")

    print("- unique Google Doc links per lesson (from structured HTML):")
    for lesson_num, n_links in links_per_lesson:
        print(f"  - Lesson {lesson_num}: {n_links}")

    missing_resource_rows: list[str] = []
    for google_id in sorted(all_google_ids):
        r = cur.execute("SELECT id FROM resources WHERE id = ?", (google_id,)).fetchone()
        if r is None:
            missing_resource_rows.append(google_id)

    print(f"- total unique Google Doc IDs in structured HTML: {len(all_google_ids)}")
    print(f"- missing resources rows for those IDs: {len(missing_resource_rows)}")
    if missing_resource_rows:
        for gid in missing_resource_rows:
            print(f"  - {gid}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
