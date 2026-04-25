"""Emit golden-lesson row metrics for all Grade 2 Science canonical lessons (SQLite)."""

from __future__ import annotations

import os
import sqlite3
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    db = os.environ.get("CURRICULUM_DB_PATH", os.path.join(_REPO, "data", "curriculum.db"))
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id
        FROM lessons l
        JOIN units u ON u.id = l.unit_id
        WHERE u.grade = 2 AND u.subject = 'Science' AND u.id LIKE 'Science_2_Mod%'
        ORDER BY u.unit_number, l.lesson_number
        """
    )
    lesson_ids = [r[0] for r in cur.fetchall()]
    print(
        "lesson_id",
        "title",
        "proc_len",
        "struct_len",
        "segments",
        "body_has_paired",
        sep="\t",
    )
    for lid in lesson_ids:
        cur.execute(
            """
            SELECT title,
                   LENGTH(COALESCE(procedure_html, '')),
                   LENGTH(COALESCE(science_li_sc_day_structured, '')),
                   (SELECT COUNT(*) FROM science_lesson_day_segments s WHERE s.lesson_id = lessons.id),
                   CASE WHEN COALESCE(procedure_html, '') LIKE '%Paired%'
                             OR COALESCE(procedure_html, '') LIKE '%paired%'
                             OR COALESCE(science_li_sc_day_structured, '') LIKE '%Paired%'
                             OR COALESCE(science_li_sc_day_structured, '') LIKE '%paired%'
                             OR COALESCE(narrative_html, '') LIKE '%Paired%'
                             OR COALESCE(narrative_html, '') LIKE '%paired%'
                        THEN 1 ELSE 0 END
            FROM lessons WHERE id = ?
            """,
            (lid,),
        )
        row = cur.fetchone()
        if not row:
            print(lid, "MISSING", sep="\t")
            continue
        t, lp, ls, se, mp = row
        print(lid, t, lp, ls, se, mp, sep="\t")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
