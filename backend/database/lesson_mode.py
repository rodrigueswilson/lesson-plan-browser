"""Lesson mode session operations for SQLite database."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session, desc, select

from backend.schema import LessonModeSession

logger = logging.getLogger(__name__)


def create_lesson_mode_session(db, session_data: Dict[str, Any]) -> str:
    """Create a lesson mode session."""
    try:
        payload = session_data.copy()
        if "day_of_week" in payload:
            payload["day_of_week"] = db._normalize_day(payload["day_of_week"])
        if "adjusted_durations" in payload and isinstance(
            payload["adjusted_durations"], dict
        ):
            payload["adjusted_durations"] = json.dumps(
                payload["adjusted_durations"]
            )

        datetime_fields = ["timer_start_time", "session_start_time", "last_updated", "ended_at"]
        for field in datetime_fields:
            if field in payload and payload[field] is not None:
                if isinstance(payload[field], str):
                    try:
                        payload[field] = datetime.fromisoformat(
                            payload[field].replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Failed to parse {field} as datetime: {e}")
                        if field in ["session_start_time", "last_updated"]:
                            payload[field] = datetime.utcnow()
                        else:
                            payload[field] = None

        session_obj = LessonModeSession(**payload)
        with Session(db.engine) as session:
            session.add(session_obj)
            session.commit()
            session.refresh(session_obj)
            return session_obj.id
    except Exception as e:
        logger.error(f"Error creating lesson mode session: {e}")
        raise


def get_lesson_mode_session(db, session_id: str) -> Optional[LessonModeSession]:
    """Get a lesson mode session by ID."""
    try:
        with Session(db.engine) as session:
            session_obj = session.get(LessonModeSession, session_id)
            if session_obj:
                if session_obj.adjusted_durations and isinstance(
                    session_obj.adjusted_durations, str
                ):
                    try:
                        session_obj.adjusted_durations = json.loads(
                            session_obj.adjusted_durations
                        )
                    except (json.JSONDecodeError, TypeError):
                        session_obj.adjusted_durations = None
            return session_obj
    except Exception as e:
        logger.error(f"Error getting lesson mode session: {e}")
        return None


def get_active_lesson_mode_session(
    db,
    user_id: str,
    lesson_plan_id: Optional[str] = None,
    day_of_week: Optional[str] = None,
    slot_number: Optional[int] = None,
) -> Optional[LessonModeSession]:
    """Get the active (not ended) lesson mode session for a user/lesson."""
    try:
        with Session(db.engine) as session:
            query = select(LessonModeSession).where(
                LessonModeSession.user_id == user_id,
                LessonModeSession.ended_at.is_(None),
            )
            if lesson_plan_id:
                query = query.where(
                    LessonModeSession.lesson_plan_id == lesson_plan_id
                )
            if day_of_week:
                normalized_day = db._normalize_day(day_of_week)
                query = query.where(LessonModeSession.day_of_week == normalized_day)
            if slot_number is not None:
                query = query.where(LessonModeSession.slot_number == slot_number)

            query = query.order_by(desc(LessonModeSession.last_updated))
            result = session.exec(query).first()

            if result:
                if result.adjusted_durations and isinstance(
                    result.adjusted_durations, str
                ):
                    try:
                        result.adjusted_durations = json.loads(
                            result.adjusted_durations
                        )
                    except (json.JSONDecodeError, TypeError):
                        result.adjusted_durations = None

            return result
    except Exception as e:
        logger.error(f"Error getting active lesson mode session: {e}")
        return None


def update_lesson_mode_session(
    db,
    session_id: str,
    updates: Dict[str, Any],
) -> bool:
    """Update a lesson mode session."""
    try:
        with Session(db.engine) as session:
            session_obj = session.get(LessonModeSession, session_id)
            if not session_obj:
                return False

            if "day_of_week" in updates:
                updates["day_of_week"] = db._normalize_day(updates["day_of_week"])

            if "adjusted_durations" in updates and isinstance(
                updates["adjusted_durations"], dict
            ):
                updates["adjusted_durations"] = json.dumps(
                    updates["adjusted_durations"]
                )

            datetime_fields = ["timer_start_time", "session_start_time", "last_updated", "ended_at"]
            fields_to_remove = []
            for field in datetime_fields:
                if field in updates and updates[field] is not None:
                    if isinstance(updates[field], str):
                        try:
                            updates[field] = datetime.fromisoformat(
                                updates[field].replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Failed to parse {field} as datetime: {e}")
                            if field == "last_updated":
                                updates[field] = datetime.utcnow()
                            elif field == "session_start_time":
                                fields_to_remove.append(field)
                            else:
                                updates[field] = None

            for field in fields_to_remove:
                updates.pop(field, None)

            for key, value in updates.items():
                if hasattr(session_obj, key):
                    setattr(session_obj, key, value)

            session_obj.last_updated = datetime.utcnow()
            session.add(session_obj)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating lesson mode session: {e}")
        return False


def end_lesson_mode_session(db, session_id: str) -> bool:
    """Mark a lesson mode session as ended."""
    try:
        with Session(db.engine) as session:
            session_obj = session.get(LessonModeSession, session_id)
            if not session_obj:
                return False

            session_obj.ended_at = datetime.utcnow()
            session_obj.last_updated = datetime.utcnow()
            session.add(session_obj)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error ending lesson mode session: {e}")
        return False
