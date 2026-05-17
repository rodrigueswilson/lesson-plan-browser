"""
Research helper: write plain text for one curriculum.db lesson (for LangExtract file input).

Usage (repo root):
  python docs/research/spikes/langextract_curriculum_smoke/export_lesson_text_from_db.py \\
    --unit-id Math_2_U1_15E1iQ_x --lesson-number 1 \\
    --out docs/research/spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _strip_html_to_text(s: str) -> str:
    if not s or not s.strip():
        return ""
    t = re.sub(r"(?is)<script.*?>.*?</script>", " ", s)
    t = re.sub(r"(?is)<style.*?>.*?</style>", " ", t)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</p\s*>", "\n\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    lines = [ln.strip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit-id", required=True)
    ap.add_argument("--lesson-number", type=int, required=True)
    ap.add_argument("--out", required=True, help="Output UTF-8 text path (repo-relative or absolute)")
    args = ap.parse_args()

    db_path = os.environ.get("CURRICULUM_DB_PATH", str(_REPO_ROOT / "data" / "curriculum.db"))
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _REPO_ROOT / out_path

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT id, lesson_number, title, narrative_html, procedure_html
        FROM lessons
        WHERE unit_id = ? AND lesson_number = ?
        """,
        (args.unit_id, args.lesson_number),
    ).fetchone()
    conn.close()
    if not row:
        print(f"No lesson for unit_id={args.unit_id!r} lesson_number={args.lesson_number}", file=sys.stderr)
        return 1

    title = row["title"] or ""
    nar = _strip_html_to_text(row["narrative_html"] or "")
    proc = _strip_html_to_text(row["procedure_html"] or "")
    parts = [f"Lesson {row['lesson_number']}: {title}".strip(), "", "Narrative:", nar, "", "Procedure:", proc]
    text = "\n".join(parts).strip() + "\n"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {len(text)} chars to {out_path}", flush=True)
    print(f"lesson_id={row['id']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
