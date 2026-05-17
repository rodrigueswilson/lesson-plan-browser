#!/usr/bin/env python3
"""
Delete the most recent lesson plan for a given week from the database.

Finds the plan by week_of (e.g. "26 W09"), picks the one with latest generated_at,
then deletes dependent rows (lesson_steps, performance_metrics, lesson_mode_sessions)
and finally the weekly_plans row.

Usage:
  python tools/delete_plan_by_week.py [--week "26 W09"] [--dry-run] [--force]

Run from project root so backend is importable.
"""

import argparse
import sys
from pathlib import Path

# Run from project root
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from sqlmodel import Session, delete, desc, select

from backend.config import settings
from backend.schema import (
    LessonModeSession,
    LessonStep,
    PerformanceMetric,
    WeeklyPlan,
)


def get_engine():
    """Use app DB: Session(engine) when available, else connect to SQLite path."""
    from backend.database import get_db

    db = get_db()
    if getattr(db, "use_ipc", False) or not getattr(db, "engine", None):
        from sqlalchemy import create_engine

        path = getattr(settings, "SQLITE_DB_PATH", Path("data/lesson_planner.db"))
        path = Path(path).resolve()
        url = f"sqlite:///{path}"
        return create_engine(url, connect_args={"check_same_thread": False})
    return db.engine


def find_most_recent_plan(engine, week_of: str):
    """Return the single WeeklyPlan for week_of with latest generated_at, or None."""
    with Session(engine) as session:
        stmt = (
            select(WeeklyPlan)
            .where(WeeklyPlan.week_of == week_of)
            .order_by(desc(WeeklyPlan.generated_at))
            .limit(1)
        )
        return session.exec(stmt).first()


def list_candidate_weeks(engine):
    """Print plans with week_of containing '26' and '09' to help identify stored value."""
    with Session(engine) as session:
        stmt = (
            select(WeeklyPlan)
            .where(
                WeeklyPlan.week_of.contains("26"),
                WeeklyPlan.week_of.contains("09"),
            )
            .order_by(desc(WeeklyPlan.generated_at))
            .limit(20)
        )
        plans = list(session.exec(stmt).all())
    return plans


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


def main():
    parser = argparse.ArgumentParser(
        description="Delete the most recent lesson plan for a given week."
    )
    parser.add_argument(
        "--week",
        default="26 W09",
        help="week_of value (default: 26 W09)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show which plan would be deleted; do not delete.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List candidate plans (week_of containing 26 and 09) and exit.",
    )
    parser.add_argument(
        "--plan-id",
        metavar="ID",
        help="Delete this plan by id (skips week_of lookup).",
    )
    args = parser.parse_args()

    db_path = getattr(settings, "SQLITE_DB_PATH", Path("data/lesson_planner.db"))
    resolved_path = Path(db_path).resolve() if not Path(db_path).is_absolute() else Path(db_path)
    if not resolved_path.exists():
        print(f"Error: database not found at {resolved_path}")
        return 1

    engine = get_engine()

    if args.list:
        plans = list_candidate_weeks(engine)
        if not plans:
            print("No plans found with week_of containing '26' and '09'.")
            return 0
        print("Candidate plans (week_of containing 26 and 09):")
        for p in plans:
            print(f"  id={p.id} user_id={p.user_id} week_of={p.week_of!r} generated_at={p.generated_at}")
        return 0

    if args.plan_id:
        with Session(engine) as session:
            plan = session.get(WeeklyPlan, args.plan_id)
        if not plan:
            print(f"No plan found with id={args.plan_id!r}.")
            return 1
    else:
        plan = find_most_recent_plan(engine, args.week)
        if not plan:
            print(f"No plan found for week_of={args.week!r}.")
            print("Run with --list to see candidate week_of values.")
            return 1

    print("Plan to delete (most recent for this week):")
    print(f"  id={plan.id}")
    print(f"  user_id={plan.user_id}")
    print(f"  week_of={plan.week_of!r}")
    print(f"  generated_at={plan.generated_at}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return 0

    if not args.force:
        confirm = input("\nType 'yes' to delete this plan and all related records: ")
        if confirm.strip().lower() != "yes":
            print("Cancelled.")
            return 0

    n_steps, n_metrics, n_sessions, n_plans = delete_plan_and_dependents(
        engine, plan.id, dry_run=False
    )
    print(f"\nDeleted: lesson_steps={n_steps}, performance_metrics={n_metrics}, lesson_mode_sessions={n_sessions}, weekly_plans={n_plans}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
