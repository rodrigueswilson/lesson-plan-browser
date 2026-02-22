"""Schedule entry operations for SQLite database."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import Session, delete, select

from backend.schema import ScheduleEntry

logger = logging.getLogger(__name__)


def create_schedule_entry(db, entry_data: Dict[str, Any]) -> str:
    """Create a new schedule entry."""
    try:
        entry = ScheduleEntry(
            id=f"sched_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entry_data.get('day_of_week')}_{entry_data.get('slot_number')}",
            **entry_data,
        )
        with Session(db.engine) as session:
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry.id
    except Exception as e:
        logger.error(f"Error creating schedule entry: {e}")
        raise


def get_user_schedule(
    db,
    user_id: str,
    day_of_week: Optional[str] = None,
    homeroom: Optional[str] = None,
    grade: Optional[str] = None,
) -> List[ScheduleEntry]:
    """Get schedule entries for a user."""
    with Session(db.engine) as session:
        query = select(ScheduleEntry).where(ScheduleEntry.user_id == user_id)

        if day_of_week:
            query = query.where(ScheduleEntry.day_of_week == day_of_week)
        if homeroom:
            query = query.where(ScheduleEntry.homeroom == homeroom)
        if grade:
            query = query.where(ScheduleEntry.grade == grade)

        query = query.order_by(ScheduleEntry.day_of_week, ScheduleEntry.start_time)
        return list(session.exec(query).all())


def get_current_lesson(db, user_id: str) -> Optional[ScheduleEntry]:
    """Get current lesson based on current time."""
    try:
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")

        with Session(db.engine) as session:
            query = select(ScheduleEntry).where(
                ScheduleEntry.user_id == user_id,
                ScheduleEntry.day_of_week == current_day,
                ScheduleEntry.start_time <= current_time,
                ScheduleEntry.end_time > current_time,
                ScheduleEntry.is_active == True,
            )
            return session.exec(query).first()
    except Exception as e:
        logger.error(f"Error getting current lesson: {e}")
        return None


def update_schedule_entry(db, schedule_id: str, updates: Dict[str, Any]) -> bool:
    """Update a schedule entry."""
    try:
        with Session(db.engine) as session:
            entry = session.get(ScheduleEntry, schedule_id)
            if not entry:
                return False

            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)

            entry.updated_at = datetime.utcnow()
            session.add(entry)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating schedule entry: {e}")
        return False


def delete_schedule_entry(db, schedule_id: str) -> bool:
    """Delete a schedule entry."""
    try:
        with Session(db.engine) as session:
            entry = session.get(ScheduleEntry, schedule_id)
            if not entry:
                return False
            session.delete(entry)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting schedule entry: {e}")
        return False


def bulk_create_schedule_entries(
    db, entries: List[Dict[str, Any]]
) -> Tuple[int, List[str]]:
    """Bulk create schedule entries."""
    created_count = 0
    errors = []

    with Session(db.engine) as session:
        for entry_data in entries:
            try:
                entry = ScheduleEntry(
                    id=f"sched_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entry_data.get('day_of_week')}_{entry_data.get('slot_number')}",
                    **entry_data,
                )
                session.add(entry)
                created_count += 1
            except Exception as e:
                errors.append(
                    f"Error creating entry for {entry_data.get('day_of_week')}: {str(e)}"
                )

        try:
            session.commit()
        except Exception as e:
            errors.append(f"Commit failed: {str(e)}")
            return 0, errors

    return created_count, errors


def clear_user_schedule(db, user_id: str) -> int:
    """Delete all schedule entries for a user."""
    try:
        with Session(db.engine) as session:
            result = session.exec(
                delete(ScheduleEntry).where(ScheduleEntry.user_id == user_id)
            )
            session.commit()
            return result.rowcount or 0
    except Exception as e:
        logger.error(f"Error clearing schedule for user {user_id}: {e}")
        raise
