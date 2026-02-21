"""
One-time cleanup: normalize common schedule subject typos.

Currently fixes:
- "Mat" / "MAT" / "Maths" / "MATHS"  -> "Math"

This updates the SQLite database in-place, with an automatic timestamped backup.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fix schedule subject typos in lesson_planner.db")
    p.add_argument(
        "--db",
        default=str(Path("data") / "lesson_planner.db"),
        help="Path to SQLite database (default: data/lesson_planner.db)",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this flag, runs in dry-run mode.",
    )
    p.add_argument(
        "--user-id",
        default=None,
        help="Optional: only update rows for this user_id",
    )
    p.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup copy of the DB (not recommended).",
    )
    return p.parse_args()


def backup_db(db_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(db_path.suffix + f".bak_{ts}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    if args.apply and not args.no_backup:
        backup_path = backup_db(db_path)
        print(f"[OK] Backup created: {backup_path}")
    elif args.apply:
        print("[WARN] --no-backup set; no DB backup created")

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        where_user = ""
        params: list[object] = []
        if args.user_id:
            where_user = " AND user_id = ?"
            params.append(args.user_id)

        # Identify candidates (case/whitespace-insensitive)
        select_sql = (
            "SELECT id, user_id, day_of_week, slot_number, start_time, end_time, subject "
            "FROM schedules "
            "WHERE subject IS NOT NULL "
            "  AND upper(trim(subject)) IN ('MAT', 'MATHS')"
            f"{where_user} "
            "ORDER BY user_id, day_of_week, start_time, slot_number"
        )
        rows = con.execute(select_sql, params).fetchall()

        print(f"[INFO] Found {len(rows)} schedule row(s) with subject typo (Mat/Maths).")
        for r in rows[:50]:
            print(
                f"  - user={r['user_id']} day={r['day_of_week']} "
                f"{r['start_time']}-{r['end_time']} slot={r['slot_number']} "
                f"id={r['id']} subject={r['subject']!r} -> 'Math'"
            )
        if len(rows) > 50:
            print(f"  ... and {len(rows) - 50} more")

        if not args.apply:
            print("[DRY-RUN] No changes applied. Re-run with --apply to update the DB.")
            return 0

        update_sql = (
            "UPDATE schedules "
            "SET subject = 'Math', updated_at = ? "
            "WHERE subject IS NOT NULL "
            "  AND upper(trim(subject)) IN ('MAT', 'MATHS')"
            f"{where_user}"
        )
        now_iso = datetime.utcnow().isoformat()
        update_params = [now_iso] + params
        cur = con.execute(update_sql, update_params)
        con.commit()
        print(f"[OK] Updated {cur.rowcount} row(s).")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())

