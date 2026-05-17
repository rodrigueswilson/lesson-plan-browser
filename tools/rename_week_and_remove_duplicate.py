#!/usr/bin/env python3
"""
Delete all plans for one week and rename all plans for another week (canonical match).

Use case: Remove duplicate W43 10/20-10/25 and rename W43 10/21-10/25 to 10/20-10/24.
Uses normalize_week_of_for_match so stored variants (10-20-10-25, etc.) are matched.

Usage:
  python tools/rename_week_and_remove_duplicate.py [options]

  Defaults: --delete-week 10/20-10/25, --rename-from 10/21-10/25, --rename-to 10/20-10/24
  Use --dry-run first to list affected plans, then run without it and confirm.

Run from project root so backend is importable.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Run from project root
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from sqlmodel import Session, delete, select

from backend.config import settings
from backend.schema import (
    LessonModeSession,
    LessonStep,
    PerformanceMetric,
    WeeklyPlan,
)
from backend.utils.date_formatter import normalize_week_of_for_match


def get_engine():
    """Use app DB; if unavailable, connect to SQLite path."""
    from backend.database import get_db

    db = get_db()
    if getattr(db, "use_ipc", False) or not getattr(db, "engine", None):
        from sqlalchemy import create_engine

        path = getattr(settings, "SQLITE_DB_PATH", Path("data/lesson_planner.db"))
        path = Path(path).resolve()
        url = f"sqlite:///{path}"
        return create_engine(url, connect_args={"check_same_thread": False})
    return db.engine


def delete_plan_and_dependents(engine, plan_id: str, dry_run: bool = False):
    """Delete lesson_steps, performance_metrics, lesson_mode_sessions, then weekly_plans."""
    with Session(engine) as session:
        n_steps = session.exec(
            delete(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
        ).rowcount
        n_metrics = session.exec(
            delete(PerformanceMetric).where(PerformanceMetric.plan_id == plan_id)
        ).rowcount
        n_sessions = session.exec(
            delete(LessonModeSession).where(LessonModeSession.lesson_plan_id == plan_id)
        ).rowcount
        n_plans = session.exec(delete(WeeklyPlan).where(WeeklyPlan.id == plan_id)).rowcount

        if not dry_run:
            session.commit()

    return n_steps, n_metrics, n_sessions, n_plans


def load_plans_for_scope(engine, user_id: Optional[str]):
    """Load all WeeklyPlan rows, optionally filtered by user_id."""
    with Session(engine) as session:
        stmt = select(WeeklyPlan)
        if user_id:
            stmt = stmt.where(WeeklyPlan.user_id == user_id)
        plans = list(session.exec(stmt).all())
    return plans


def run_rename(engine, plan: WeeklyPlan, new_week_of: str, dry_run: bool) -> bool:
    """Set plan.week_of and lesson_json.metadata.week_of to new_week_of; persist unless dry_run."""
    if dry_run:
        return True
    with Session(engine) as session:
        row = session.get(WeeklyPlan, plan.id)
        if not row:
            return False
        row.week_of = new_week_of
        if row.lesson_json is not None and isinstance(row.lesson_json, dict):
            if "metadata" not in row.lesson_json:
                row.lesson_json["metadata"] = {}
            if isinstance(row.lesson_json["metadata"], dict):
                row.lesson_json["metadata"]["week_of"] = new_week_of
        session.add(row)
        session.commit()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Delete all plans for one week and rename another week (canonical match)."
    )
    parser.add_argument(
        "--delete-week",
        default="10/20-10/25",
        help="week_of to delete (all matching plans, canonical match)",
    )
    parser.add_argument(
        "--rename-from",
        default="10/21-10/25",
        help="week_of to rename (canonical match)",
    )
    parser.add_argument(
        "--rename-to",
        default="10/20-10/24",
        help="new week_of value for renamed plans",
    )
    parser.add_argument(
        "--user-id",
        metavar="ID",
        help="Limit to this user_id (optional).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list affected plans; do not change the database.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    args = parser.parse_args()

    db_path = getattr(settings, "SQLITE_DB_PATH", Path("data/lesson_planner.db"))
    resolved_path = Path(db_path).resolve() if not Path(db_path).is_absolute() else Path(db_path)
    if not resolved_path.exists():
        print(f"Error: database not found at {resolved_path}")
        return 1

    engine = get_engine()
    delete_canonical = normalize_week_of_for_match(args.delete_week)
    rename_from_canonical = normalize_week_of_for_match(args.rename_from)

    if not delete_canonical:
        print(f"Error: invalid --delete-week {args.delete_week!r}")
        return 1
    if not rename_from_canonical:
        print(f"Error: invalid --rename-from {args.rename_from!r}")
        return 1

    plans = load_plans_for_scope(engine, args.user_id)
    to_delete = [
        p for p in plans
        if p.week_of and normalize_week_of_for_match(p.week_of) == delete_canonical
    ]
    to_rename = [
        p for p in plans
        if p.week_of and normalize_week_of_for_match(p.week_of) == rename_from_canonical
    ]

    print("Plans to DELETE (week canonical match {!r}):".format(delete_canonical))
    if not to_delete:
        print("  (none)")
    for p in to_delete:
        print("  id={} user_id={} week_of={!r} generated_at={}".format(
            p.id, p.user_id, p.week_of, p.generated_at
        ))

    print("\nPlans to RENAME to {!r}:".format(args.rename_to))
    if not to_rename:
        print("  (none)")
    for p in to_rename:
        print("  id={} user_id={} week_of={!r} generated_at={}".format(
            p.id, p.user_id, p.week_of, p.generated_at
        ))

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return 0

    if not to_delete and not to_rename:
        print("\nNothing to do.")
        return 0

    if not args.force:
        confirm = input("\nType 'yes' to apply delete and rename: ")
        if confirm.strip().lower() != "yes":
            print("Cancelled.")
            return 0

    total_steps = total_metrics = total_sessions = total_plans = 0
    for p in to_delete:
        n_steps, n_metrics, n_sessions, n_plans = delete_plan_and_dependents(
            engine, p.id, dry_run=False
        )
        total_steps += n_steps
        total_metrics += n_metrics
        total_sessions += n_sessions
        total_plans += n_plans
    if to_delete:
        print(
            "Deleted: lesson_steps={}, performance_metrics={}, lesson_mode_sessions={}, weekly_plans={}".format(
                total_steps, total_metrics, total_sessions, total_plans
            )
        )

    for p in to_rename:
        run_rename(engine, p, args.rename_to, dry_run=False)
    if to_rename:
        print("Renamed {} plan(s) to week_of={!r}.".format(len(to_rename), args.rename_to))

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
