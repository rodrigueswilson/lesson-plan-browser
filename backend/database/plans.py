"""Weekly plan and original lesson plan operations for SQLite database."""

import json
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import Session, delete, desc, select

from backend.schema import (
    LessonModeSession,
    LessonStep,
    OriginalLessonPlan,
    PerformanceMetric,
    WeeklyPlan,
)
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.utils.metadata_utils import parse_week_of_date

logger = logging.getLogger(__name__)


def create_weekly_plan(
    db,
    user_id: str,
    week_of: str,
    output_file: str,
    week_folder_path: str,
    consolidated: bool = False,
    total_slots: int = 1,
) -> str:
    """Create a new weekly plan record - works in both modes."""
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    if db.use_ipc:
        try:
            db._adapter.execute(
                """INSERT INTO weekly_plans 
                   (id, user_id, week_of, output_file, week_folder_path, consolidated, total_slots, status, generated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    plan_id,
                    user_id,
                    week_of,
                    output_file,
                    week_folder_path,
                    1 if consolidated else 0,
                    total_slots,
                    "pending",
                    datetime.utcnow().isoformat(),
                ],
            )
            return plan_id
        except Exception as e:
            logger.error(f"Error creating weekly plan via IPC: {e}")
            raise
    else:
        try:
            plan = WeeklyPlan(
                id=plan_id,
                user_id=user_id,
                week_of=week_of,
                output_file=output_file,
                week_folder_path=week_folder_path,
                consolidated=1 if consolidated else 0,
                total_slots=total_slots,
                status="pending",
            )

            with Session(db.engine) as session:
                session.add(plan)
                session.commit()
                session.refresh(plan)
                return plan.id
        except Exception as e:
            logger.error(f"Error creating weekly plan: {e}")
            raise


def get_weekly_plan(db, plan_id: str) -> Optional[WeeklyPlan]:
    """Get a weekly plan by ID - works in both modes."""
    if db.use_ipc:
        row = db._adapter.query_one(
            "SELECT * FROM weekly_plans WHERE id = ?", [plan_id]
        )
        if not row:
            return None

        lesson_json = row.get("lesson_json")
        if isinstance(lesson_json, str):
            try:
                lesson_json = json.loads(lesson_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse lesson_json for plan {plan_id}")
                lesson_json = None

        def parse_datetime(dt_value):
            if isinstance(dt_value, datetime):
                return dt_value
            if isinstance(dt_value, str):
                try:
                    return datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return datetime.utcnow()
            return datetime.utcnow()

        return WeeklyPlan(
            id=row["id"],
            user_id=row["user_id"],
            week_of=row["week_of"],
            status=row.get("status", "pending"),
            output_file=row.get("output_file"),
            week_folder_path=row.get("week_folder_path"),
            consolidated=row.get("consolidated", 0),
            total_slots=row.get("total_slots", 1),
            generated_at=parse_datetime(row.get("generated_at")),
            processing_time_ms=row.get("processing_time_ms"),
            total_tokens=row.get("total_tokens"),
            total_cost_usd=row.get("total_cost_usd"),
            llm_model=row.get("llm_model"),
            error_message=row.get("error_message"),
            lesson_json=lesson_json,
        )
    else:
        with Session(db.engine) as session:
            plan = session.get(WeeklyPlan, plan_id)
            if plan and plan.lesson_json and isinstance(plan.lesson_json, str):
                try:
                    plan.lesson_json = json.loads(plan.lesson_json)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        f"Failed to parse lesson_json for plan {plan_id}"
                    )
                    plan.lesson_json = None
            return plan


def get_user_plans(
    db, user_id: str, limit: Optional[int] = None
) -> List[WeeklyPlan]:
    """Get weekly plans for a user."""
    with Session(db.engine) as session:
        statement = (
            select(WeeklyPlan)
            .where(WeeklyPlan.user_id == user_id)
            .order_by(desc(WeeklyPlan.generated_at))
        )
        if limit:
            statement = statement.limit(limit)
        plans = list(session.exec(statement).all())
        for plan in plans:
            if plan.lesson_json and isinstance(plan.lesson_json, str):
                try:
                    plan.lesson_json = json.loads(plan.lesson_json)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        f"Failed to parse lesson_json for plan {plan.id}"
                    )
                    plan.lesson_json = None
        return plans


def update_weekly_plan(
    db,
    plan_id: str,
    status: Optional[str] = None,
    output_file: Optional[str] = None,
    error_message: Optional[str] = None,
    lesson_json: Optional[Dict[str, Any]] = None,
    total_slots: Optional[int] = None,
) -> bool:
    """Update weekly plan status or lesson_json."""
    try:
        with Session(db.engine) as session:
            plan = session.get(WeeklyPlan, plan_id)
            if not plan:
                return False

            if status:
                plan.status = status
            if output_file:
                plan.output_file = output_file
            if error_message:
                plan.error_message = error_message
            if lesson_json is not None:
                normalize_objectives_in_lesson(lesson_json)
                plan.lesson_json = lesson_json
            if total_slots is not None:
                plan.total_slots = total_slots

            session.add(plan)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating weekly plan: {e}")
        return False


def create_original_lesson_plan(db, plan_data: Dict[str, Any]) -> str:
    """Create a new original lesson plan record (extraction cache)."""
    try:
        for field in [
            "content_json",
            "monday_content",
            "tuesday_content",
            "wednesday_content",
            "thursday_content",
            "friday_content",
            "available_days",
        ]:
            if field in plan_data:
                plan_data[field] = db._coerce_json_field(plan_data[field])

        plan = OriginalLessonPlan(**plan_data)
        with Session(db.engine) as session:
            session.merge(plan)
            session.commit()
            return plan.id
    except Exception as e:
        logger.error(f"Error creating original lesson plan: {e}")
        raise


def get_original_lesson_plan(
    db, user_id: str, week_of: str, slot_number: int
) -> Optional[OriginalLessonPlan]:
    """Get original lesson plan content for a specific slot."""
    with Session(db.engine) as session:
        statement = select(OriginalLessonPlan).where(
            OriginalLessonPlan.user_id == user_id,
            OriginalLessonPlan.week_of == week_of,
            OriginalLessonPlan.slot_number == slot_number,
        )
        plan = session.exec(statement).first()

        if plan:
            for field in [
                "content_json",
                "monday_content",
                "tuesday_content",
                "wednesday_content",
                "thursday_content",
                "friday_content",
                "available_days",
            ]:
                setattr(plan, field, db._coerce_json_field(getattr(plan, field)))

        return plan


def get_original_lesson_plans_for_week(
    db, user_id: str, week_of: str
) -> List[OriginalLessonPlan]:
    """Get all original lesson plans for a week."""
    with Session(db.engine) as session:
        statement = select(OriginalLessonPlan).where(
            OriginalLessonPlan.user_id == user_id,
            OriginalLessonPlan.week_of == week_of,
        )
        plans = list(session.exec(statement).all())

        for plan in plans:
            for field in [
                "content_json",
                "monday_content",
                "tuesday_content",
                "wednesday_content",
                "thursday_content",
                "friday_content",
                "available_days",
            ]:
                setattr(plan, field, db._coerce_json_field(getattr(plan, field)))

        return plans


def get_original_lesson_plans_for_file(
    db, user_id: str, week_of: str, file_path: str
) -> List[OriginalLessonPlan]:
    """Get all original lesson plans associated with a specific file."""
    with Session(db.engine) as session:
        statement = select(OriginalLessonPlan).where(
            OriginalLessonPlan.user_id == user_id,
            OriginalLessonPlan.week_of == week_of,
            OriginalLessonPlan.source_file_path == file_path,
        )
        return list(session.exec(statement).all())


def update_original_lesson_plan_status(
    db, plan_id: str, status: str, error_message: Optional[str] = None
) -> bool:
    """Update original lesson plan status."""
    try:
        with Session(db.engine) as session:
            plan = session.get(OriginalLessonPlan, plan_id)
            if not plan:
                return False

            plan.status = status
            if error_message is not None:
                plan.error_message = error_message

            plan.updated_at = datetime.utcnow()
            session.add(plan)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating original lesson plan status: {e}")
        return False


def delete_original_lesson_plans(db, user_id: str, week_of: str) -> int:
    """Delete all original lesson plans for a user and week."""
    try:
        with Session(db.engine) as session:
            statement = delete(OriginalLessonPlan).where(
                OriginalLessonPlan.user_id == user_id,
                OriginalLessonPlan.week_of == week_of,
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount
    except Exception as e:
        logger.error(f"Error deleting original lesson plans: {e}")
        return 0


def _today_date_for_school_sort() -> date:
    """Anchor for inferring year when week_of omits it; patchable in tests."""
    return datetime.now(timezone.utc).date()


# How far ahead a week label may still mean "this upcoming week" (no year in string).
_AMBIGUOUS_NEAR_FUTURE_DAYS = 21


def _ambiguous_week_start_date(month: int, day: int, ref: date) -> date:
    """
    Pick a calendar year for (month, day) when week_of has no year.

    Candidates are (ref.year - 1) .. (ref.year + 1) for that month/day.

    Pure "closest in absolute days" is wrong in spring: e.g. ref Mar 2026 would map
    Sep to Sep 2026 (closer than Sep 2025), pushing last fall above current spring.

    Instead: if some candidate falls just after ref (within a few weeks), use the
    earliest such date (upcoming week). Otherwise use the most recent candidate on or
    before ref (last time that calendar week occurred). If everything is far in the
    future, use the earliest candidate.
    """
    candidates: List[date] = []
    for y in range(ref.year - 1, ref.year + 2):
        try:
            candidates.append(date(y, month, day))
        except ValueError:
            continue
    if not candidates:
        return ref
    horizon = ref + timedelta(days=_AMBIGUOUS_NEAR_FUTURE_DAYS)
    near_future = [c for c in candidates if ref < c <= horizon]
    if near_future:
        return min(near_future)
    past_or_today = [c for c in candidates if c <= ref]
    if past_or_today:
        return max(past_or_today)
    return min(candidates)


def _school_week_group_sort_key(week_of: str, _plans: List[Dict[str, Any]]) -> tuple:
    """Sort by inferred Monday/start calendar date, descending (most recent real week first)."""
    parsed = parse_week_of_date(week_of)
    if parsed is None:
        return (-1,)
    m, d, y = parsed[0], parsed[1], parsed[2]
    if y is not None:
        try:
            start = date(y, m, d)
        except ValueError:
            return (-1,)
    else:
        start = _ambiguous_week_start_date(m, d, _today_date_for_school_sort())
    return (start.toordinal(),)


def _recent_week_group_sort_key(plans: List[Dict[str, Any]]) -> tuple:
    """Sort key uses naive datetimes only (mixed aware/naive ISO strings from ORM/export)."""
    max_dt: Optional[datetime] = None
    for p in plans:
        ga = p.get("generated_at")
        if not ga or not isinstance(ga, str):
            continue
        dt = parse_export_generated_at(ga)
        if dt is None:
            continue
        if max_dt is None or dt > max_dt:
            max_dt = dt
    if max_dt is None:
        return (datetime.min,)
    return (max_dt,)


def _group_plans_by_week(
    db, user_id: str, sort_mode: str = "school"
) -> List[Dict[str, Any]]:
    """All weeks for user with plan summaries; sort weeks per sort_mode; newest plan first per week."""
    with Session(db.engine) as session:
        all_plans = list(
            session.exec(
                select(WeeklyPlan)
                .where(WeeklyPlan.user_id == user_id)
                .order_by(WeeklyPlan.generated_at)
            ).all()
        )
    by_week: Dict[str, List[Dict[str, Any]]] = {}
    for p in all_plans:
        w = p.week_of or ""
        if w not in by_week:
            by_week[w] = []
        by_week[w].append(
            {
                "id": p.id,
                "generated_at": p.generated_at.isoformat() if p.generated_at else None,
                "status": p.status or "pending",
            }
        )
    groups = [{"week_of": week_of, "plans": plans} for week_of, plans in by_week.items()]
    mode = (sort_mode or "school").strip().lower()
    if mode == "recent":
        groups.sort(key=lambda g: _recent_week_group_sort_key(g["plans"]), reverse=True)
    else:
        groups.sort(
            key=lambda g: _school_week_group_sort_key(g["week_of"], g["plans"]),
            reverse=True,
        )
    for g in groups:
        g["plans"] = list(reversed(g["plans"]))
    return groups


def get_plans_grouped_by_week(
    db, user_id: str, sort_mode: str = "school"
) -> List[Dict[str, Any]]:
    """Return every week that has at least one plan for this user."""
    return _group_plans_by_week(db, user_id, sort_mode=sort_mode)


def get_duplicate_weeks(db, user_id: str) -> List[Dict[str, Any]]:
    """Return weeks that have more than one plan for this user (subset of grouped-by-week)."""
    return [w for w in _group_plans_by_week(db, user_id, sort_mode="school") if len(w["plans"]) > 1]


def parse_export_generated_at(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime from export JSON; returns naive UTC-ish datetime."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def insert_weekly_plan_from_export(
    db,
    plan_id: str,
    user_id: str,
    week_of: str,
    status: str,
    output_file: Optional[str],
    week_folder_path: Optional[str],
    consolidated: int,
    total_slots: int,
    generated_at: Optional[datetime],
    processing_time_ms: Optional[float],
    total_tokens: Optional[int],
    total_cost_usd: Optional[float],
    llm_model: Optional[str],
    error_message: Optional[str],
    lesson_json: Optional[Dict[str, Any]],
) -> None:
    """Insert a weekly_plans row from export JSON (Settings > Database restore). Non-IPC only."""
    if db.use_ipc:
        raise NotImplementedError("insert_weekly_plan_from_export requires SQLModel engine")
    plan = WeeklyPlan(
        id=plan_id,
        user_id=user_id,
        week_of=week_of,
        status=status or "pending",
        output_file=output_file,
        week_folder_path=week_folder_path,
        consolidated=consolidated,
        total_slots=total_slots or 1,
        generated_at=generated_at or datetime.utcnow(),
        processing_time_ms=processing_time_ms,
        total_tokens=total_tokens,
        total_cost_usd=total_cost_usd,
        llm_model=llm_model,
        error_message=error_message,
        lesson_json=lesson_json,
    )
    with Session(db.engine) as session:
        session.add(plan)
        session.commit()


def delete_plan_and_dependents(db, plan_id: str) -> None:
    """Delete a weekly plan and its lesson_steps, performance_metrics, lesson_mode_sessions."""
    with Session(db.engine) as session:
        session.exec(delete(LessonStep).where(LessonStep.lesson_plan_id == plan_id))
        session.exec(delete(PerformanceMetric).where(PerformanceMetric.plan_id == plan_id))
        session.exec(
            delete(LessonModeSession).where(LessonModeSession.lesson_plan_id == plan_id)
        )
        session.exec(delete(WeeklyPlan).where(WeeklyPlan.id == plan_id))
        session.commit()
