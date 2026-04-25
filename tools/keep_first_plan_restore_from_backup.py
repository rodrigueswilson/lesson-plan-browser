#!/usr/bin/env python3
"""
Keep the first (older) lesson plan for a user/week and remove the second (newer) one.
Optionally restore the first version from an automatic backup, then re-export to tablet.

Two versions can exist when:
- The same week was generated twice (two rows in weekly_plans); or
- A partial/missing-only run created a new plan instead of merging.

Usage:
  # List plans for a user/week (oldest first = first version)
  python tools/keep_first_plan_restore_from_backup.py --user-id USER_ID --week "03-02-03-06" --list

  # Keep the first plan and delete the second (in main DB)
  python tools/keep_first_plan_restore_from_backup.py --user-id USER_ID --week "03-02-03-06" --keep-first [--force]

  # List automatic backups (main DB archives + tablet export prev)
  python tools/keep_first_plan_restore_from_backup.py --user-id USER_ID --list-backups

  # List weeks that have plans for this user (to find the right week_of)
  python tools/keep_first_plan_restore_from_backup.py --user-id USER_ID --list-weeks

  # Restore the first version from a backup DB into main, then remove the second
  python tools/keep_first_plan_restore_from_backup.py --user-id USER_ID --week "03-02-03-06" --restore-from-backup PATH_TO_BACKUP.db [--force]

After restoring or keeping-first, re-export to tablet from the app (Tablet export) so the tablet gets the single desired plan.
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from backend.config import settings


def _main_db_path() -> Path:
    path = getattr(settings, "SQLITE_DB_PATH", None)
    if path is None:
        path = Path("data/lesson_planner.db")
    return Path(path).resolve()


def _archive_dir() -> Path:
    return _main_db_path().parent / "archives"


def _tablet_export_dir(user_id: str) -> Path:
    return _main_db_path().parent / "tablet_db_exports" / user_id


def list_main_backups() -> list[Path]:
    """Main DB timestamped backups: archives/lesson_planner_backup_*.db"""
    archives = _archive_dir()
    if not archives.exists():
        return []
    backups = sorted(archives.glob("lesson_planner_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def list_tablet_prev_backups(user_id: str) -> list[Path]:
    """Tablet export 'previous' backups: lesson_planner_prev_*.db (created before each new export)."""
    base = _tablet_export_dir(user_id)
    if not base.exists():
        return []
    backups = sorted(base.glob("lesson_planner_prev_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def list_weeks_for_user(conn: sqlite3.Connection, user_id: str) -> list[tuple]:
    """Return (week_of, plan_count, latest_generated_at) for this user."""
    cursor = conn.execute(
        "SELECT week_of, COUNT(*), MAX(generated_at) FROM weekly_plans WHERE user_id = ? GROUP BY week_of ORDER BY MAX(generated_at) DESC",
        (user_id,),
    )
    return cursor.fetchall()


def list_plans_for_week(conn: sqlite3.Connection, user_id: str, week_of: str) -> list[tuple]:
    """Return (id, generated_at, status) for this user+week, ordered by generated_at ASC (oldest first)."""
    cursor = conn.execute(
        "SELECT id, generated_at, status FROM weekly_plans WHERE user_id = ? AND week_of = ? ORDER BY generated_at ASC",
        (user_id, week_of),
    )
    return cursor.fetchall()


def copy_plan_from_to(
    *,
    source_conn: sqlite3.Connection,
    dest_conn: sqlite3.Connection,
    plan_id: str,
) -> None:
    """Copy one weekly_plan and its lesson_steps (and metrics/sessions if present) from source to dest."""
    # weekly_plans
    src_cols = [d[1] for d in source_conn.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    dest_cols = [d[1] for d in dest_conn.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    cols = [c for c in src_cols if c in dest_cols]
    row = source_conn.execute(
        f"SELECT {','.join(cols)} FROM weekly_plans WHERE id = ?", (plan_id,)
    ).fetchone()
    if not row:
        raise SystemExit(f"Plan {plan_id} not found in source database.")
    ph = ",".join("?" for _ in cols)
    dest_conn.execute(
        f"INSERT OR REPLACE INTO weekly_plans ({','.join(cols)}) VALUES ({ph})",
        row,
    )

    # lesson_steps
    try:
        src_s = [d[1] for d in source_conn.execute("PRAGMA table_info(lesson_steps)").fetchall()]
        dest_s = [d[1] for d in dest_conn.execute("PRAGMA table_info(lesson_steps)").fetchall()]
        sc = [c for c in src_s if c in dest_s]
        steps = source_conn.execute(
            f"SELECT {','.join(sc)} FROM lesson_steps WHERE lesson_plan_id = ?", (plan_id,)
        ).fetchall()
        for s in steps:
            dest_conn.execute(
                f"INSERT OR REPLACE INTO lesson_steps ({','.join(sc)}) VALUES ({','.join('?' for _ in sc)})",
                s,
            )
    except sqlite3.OperationalError:
        pass

    # performance_metrics
    try:
        for t in ("performance_metrics",):
            src_m = [d[1] for d in source_conn.execute(f"PRAGMA table_info({t})").fetchall()]
            dest_m = [d[1] for d in dest_conn.execute(f"PRAGMA table_info({t})").fetchall()]
            m_cols = [c for c in src_m if c in dest_m]
            if not m_cols:
                continue
            key_col = "plan_id" if t == "performance_metrics" else "lesson_plan_id"
            rows = source_conn.execute(
                f"SELECT {','.join(m_cols)} FROM {t} WHERE {key_col} = ?", (plan_id,)
            ).fetchall()
            for r in rows:
                dest_conn.execute(
                    f"INSERT OR REPLACE INTO {t} ({','.join(m_cols)}) VALUES ({','.join('?' for _ in m_cols)})",
                    r,
                )
    except sqlite3.OperationalError:
        pass

    # lesson_mode_sessions
    try:
        src_l = [d[1] for d in source_conn.execute("PRAGMA table_info(lesson_mode_sessions)").fetchall()]
        dest_l = [d[1] for d in dest_conn.execute("PRAGMA table_info(lesson_mode_sessions)").fetchall()]
        l_cols = [c for c in src_l if c in dest_l]
        if l_cols:
            rows = source_conn.execute(
                f"SELECT {','.join(l_cols)} FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (plan_id,)
            ).fetchall()
            for r in rows:
                dest_conn.execute(
                    f"INSERT OR REPLACE INTO lesson_mode_sessions ({','.join(l_cols)}) VALUES ({','.join('?' for _ in l_cols)})",
                    r,
                )
    except sqlite3.OperationalError:
        pass


def delete_plan_and_dependents(conn: sqlite3.Connection, plan_id: str) -> tuple[int, int, int, int]:
    """Delete lesson_steps, performance_metrics, lesson_mode_sessions, weekly_plans. Returns counts."""
    n_steps = conn.execute("DELETE FROM lesson_steps WHERE lesson_plan_id = ?", (plan_id,)).rowcount
    try:
        n_metrics = conn.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan_id,)).rowcount
    except sqlite3.OperationalError:
        n_metrics = 0
    try:
        n_sessions = conn.execute("DELETE FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (plan_id,)).rowcount
    except sqlite3.OperationalError:
        n_sessions = 0
    n_plans = conn.execute("DELETE FROM weekly_plans WHERE id = ?", (plan_id,)).rowcount
    return n_steps, n_metrics, n_sessions, n_plans


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keep the first (older) lesson plan for a user/week; optionally restore from backup."
    )
    parser.add_argument("--user-id", required=True, help="User ID (e.g. UUID)")
    parser.add_argument(
        "--week",
        help="week_of value (e.g. 03-02-03-06 or 03/02-03/06). Required for --list, --keep-first, --restore-from-backup.",
    )
    parser.add_argument("--list", action="store_true", help="List plans for this user/week (oldest first).")
    parser.add_argument("--list-weeks", action="store_true", help="List weeks that have plans for this user.")
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List automatic backups (main DB archives + tablet export prev for this user).",
    )
    parser.add_argument(
        "--keep-first",
        action="store_true",
        help="Keep the oldest plan for this user/week and delete the newer one(s).",
    )
    parser.add_argument(
        "--restore-from-backup",
        metavar="PATH",
        help="Path to a backup DB. Copy the oldest plan for this user/week from backup into main, then delete newer plan(s) in main.",
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be done.")
    args = parser.parse_args()

    main_path = _main_db_path()
    if not main_path.exists():
        print(f"Main database not found: {main_path}")
        return 1

    if args.list_backups:
        print("Main DB backups (newest first):")
        for p in list_main_backups():
            mtime = p.stat().st_mtime
            ts = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {p}")
            print(f"    modified: {ts}")
        print("\nTablet export previous backups for this user (newest first):")
        for p in list_tablet_prev_backups(args.user_id):
            mtime = p.stat().st_mtime
            ts = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {p}")
            print(f"    modified: {ts}")
        if not list_main_backups() and not list_tablet_prev_backups(args.user_id):
            print("  (none found)")
        return 0

    if args.list_weeks:
        conn = sqlite3.connect(str(main_path))
        try:
            weeks = list_weeks_for_user(conn, args.user_id)
        finally:
            conn.close()
        if not weeks:
            print(f"No plans found for user_id={args.user_id!r}.")
            return 0
        print(f"Weeks with plans for user_id={args.user_id!r}:")
        for week_of, count, latest in weeks:
            print(f"  week_of={week_of!r}  plans={count}  latest_generated_at={latest}")
        return 0

    if not args.week:
        if args.list or args.keep_first or args.restore_from_backup:
            print("Error: --week is required for --list, --keep-first, and --restore-from-backup.")
            return 1
        print("Use --list-backups, --list-weeks, or provide --week with --list / --keep-first / --restore-from-backup.")
        return 0

    conn = sqlite3.connect(str(main_path))
    try:
        plans = list_plans_for_week(conn, args.user_id, args.week)
    finally:
        conn.close()

    if args.list:
        if not plans:
            print(f"No plans found for user_id={args.user_id!r} week_of={args.week!r}.")
            return 0
        print(f"Plans for user_id={args.user_id!r} week_of={args.week!r} (oldest = first version, newest = second):")
        for plan_id, generated_at, status in plans:
            print(f"  id={plan_id}  generated_at={generated_at}  status={status}")
        return 0

    if args.keep_first:
        if len(plans) < 2:
            print("There are not two versions for this user/week. Nothing to do.")
            return 0
        keep_id = plans[0][0]
        delete_ids = [p[0] for p in plans[1:]]
        print("Keeping first version (oldest) and deleting the rest:")
        print(f"  Keep:  {keep_id} (generated_at={plans[0][1]})")
        for plan_id, gen_at, _ in plans[1:]:
            print(f"  Delete: {plan_id} (generated_at={gen_at})")
        if args.dry_run:
            print("\n[DRY RUN] No changes made.")
            return 0
        if not args.force:
            confirm = input("\nType 'yes' to keep the first and delete the rest: ")
            if confirm.strip().lower() != "yes":
                print("Cancelled.")
                return 0
        conn = sqlite3.connect(str(main_path))
        try:
            for plan_id in delete_ids:
                delete_plan_and_dependents(conn, plan_id)
            conn.commit()
        finally:
            conn.close()
        print("Done. Re-export to tablet from the app to send the first version to the tablet.")
        return 0

    if args.restore_from_backup:
        backup_path = Path(args.restore_from_backup).resolve()
        if not backup_path.exists():
            print(f"Backup file not found: {backup_path}")
            return 1
        backup_conn = sqlite3.connect(str(backup_path))
        try:
            backup_plans = list_plans_for_week(backup_conn, args.user_id, args.week)
        finally:
            backup_conn.close()
        if not backup_plans:
            print(f"No plan found in backup for user_id={args.user_id!r} week_of={args.week!r}.")
            return 1
        restore_id = backup_plans[0][0]
        print(f"Plan in backup (oldest for this user/week): id={restore_id} generated_at={backup_plans[0][1]}")
        main_plans = list_plans_for_week(sqlite3.connect(str(main_path)), args.user_id, args.week)
        if main_plans:
            print("Plans currently in main DB (will be replaced/removed):")
            for plan_id, gen_at, status in main_plans:
                print(f"  {plan_id}  generated_at={gen_at}  status={status}")
        if args.dry_run:
            print("\n[DRY RUN] Would copy plan from backup into main and delete other plans for this user/week.")
            return 0
        if not args.force:
            confirm = input("\nType 'yes' to restore this plan from backup and remove others in main: ")
            if confirm.strip().lower() != "yes":
                print("Cancelled.")
                return 0
        backup_conn = sqlite3.connect(str(backup_path))
        main_conn = sqlite3.connect(str(main_path))
        try:
            copy_plan_from_to(source_conn=backup_conn, dest_conn=main_conn, plan_id=restore_id)
            main_conn.commit()
            # Remove any other plan for this user/week in main so only the restored one remains
            current = list_plans_for_week(main_conn, args.user_id, args.week)
            for plan_id, _, _ in current:
                if plan_id != restore_id:
                    delete_plan_and_dependents(main_conn, plan_id)
            main_conn.commit()
        finally:
            backup_conn.close()
            main_conn.close()
        print("Done. The first version from the backup is now in the main DB.")
        print("Re-export to tablet from the app to send it to the tablet.")
        return 0

    print("Use --list, --list-backups, --keep-first, or --restore-from-backup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
