"""Lesson step operations for SQLite database."""

import logging
from typing import Any, Dict, List, Optional

from sqlmodel import Session, delete, select

from backend.schema import LessonStep
from backend.database.engine import hydrate_lesson_step

logger = logging.getLogger(__name__)


def create_lesson_step(db, step_data: Dict[str, Any]) -> str:
    """Create a lesson step."""
    try:
        payload = step_data.copy()
        payload["day_of_week"] = db._normalize_day(payload.get("day_of_week"))

        step = LessonStep(**payload)

        with Session(db.engine) as session:
            session.add(step)
            session.commit()
            session.refresh(step)
            return step.id
    except Exception as e:
        logger.error(f"Error creating lesson step: {e}")
        raise


def delete_lesson_steps(
    db,
    plan_id: str,
    day_of_week: Optional[str] = None,
    slot_number: Optional[int] = None,
) -> int:
    """Delete lesson steps for a plan/day/slot."""
    try:
        with Session(db.engine) as session:
            stmt = delete(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
            normalized_day = db._normalize_day(day_of_week)
            if normalized_day:
                stmt = stmt.where(LessonStep.day_of_week == normalized_day)
            if slot_number is not None:
                stmt = stmt.where(LessonStep.slot_number == slot_number)
            result = session.exec(stmt)
            session.commit()
            return result.rowcount or 0
    except Exception as e:
        logger.error(f"Error deleting lesson steps: {e}")
        return 0


def get_lesson_steps(
    db,
    plan_id: str,
    day_of_week: Optional[str] = None,
    slot_number: Optional[int] = None,
) -> List[LessonStep]:
    """Get lesson steps."""
    with Session(db.engine) as session:
        query = select(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
        normalized_day = db._normalize_day(day_of_week)
        if normalized_day:
            query = query.where(LessonStep.day_of_week == normalized_day)
        if slot_number is not None:
            query = query.where(LessonStep.slot_number == slot_number)

        query = query.order_by(LessonStep.step_number)
        steps = list(session.exec(query).all())
        return [hydrate_lesson_step(step, db._coerce_json_field) for step in steps]
