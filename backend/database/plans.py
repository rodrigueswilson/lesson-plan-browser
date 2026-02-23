"""Weekly plan and original lesson plan operations for SQLite database."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, delete, desc, select

from backend.schema import OriginalLessonPlan, WeeklyPlan
from backend.services.objectives_utils import normalize_objectives_in_lesson

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
