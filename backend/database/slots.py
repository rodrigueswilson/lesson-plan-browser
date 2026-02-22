"""Class slot operations for SQLite database."""

import logging
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, delete, select

from backend.schema import ClassSlot

logger = logging.getLogger(__name__)


def create_class_slot(
    db,
    user_id: str,
    slot_number: int,
    subject: str,
    grade: str,
    homeroom: Optional[str] = None,
    plan_group_label: Optional[str] = None,
    proficiency_levels: Optional[str] = None,
    primary_teacher_file: Optional[str] = None,
    primary_teacher_first_name: Optional[str] = None,
    primary_teacher_last_name: Optional[str] = None,
) -> str:
    """Create a class slot configuration."""
    try:
        primary_teacher_name = None
        if primary_teacher_first_name or primary_teacher_last_name:
            primary_teacher_name = f"{primary_teacher_first_name or ''} {primary_teacher_last_name or ''}".strip()

        slot = ClassSlot(
            id=f"slot_{datetime.now().strftime('%Y%m%d%H%M%S')}_{slot_number}",
            user_id=user_id,
            slot_number=slot_number,
            subject=subject,
            grade=grade,
            homeroom=homeroom,
            plan_group_label=plan_group_label,
            proficiency_levels=proficiency_levels,
            primary_teacher_file=primary_teacher_file,
            primary_teacher_name=primary_teacher_name,
            primary_teacher_first_name=primary_teacher_first_name,
            primary_teacher_last_name=primary_teacher_last_name,
        )

        with Session(db.engine) as session:
            session.add(slot)
            session.commit()
            session.refresh(slot)
            return slot.id
    except Exception as e:
        logger.error(f"Error creating class slot: {e}")
        raise


def get_user_slots(db, user_id: str) -> List[ClassSlot]:
    """Get all class slots for a user - works in both modes."""
    if db.use_ipc:
        rows = db._adapter.query(
            "SELECT * FROM class_slots WHERE user_id = ? ORDER BY slot_number",
            [user_id],
        )
        slots = []

        def parse_datetime(dt_value):
            if isinstance(dt_value, datetime):
                return dt_value
            if isinstance(dt_value, str):
                try:
                    return datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return datetime.utcnow()
            return datetime.utcnow()

        for row in rows:
            slots.append(
                ClassSlot(
                    id=row["id"],
                    user_id=row["user_id"],
                    slot_number=row["slot_number"],
                    subject=row["subject"],
                    grade=row["grade"],
                    homeroom=row.get("homeroom"),
                    plan_group_label=row.get("plan_group_label"),
                    proficiency_levels=row.get("proficiency_levels"),
                    primary_teacher_file=row.get("primary_teacher_file"),
                    primary_teacher_name=row.get("primary_teacher_name"),
                    primary_teacher_first_name=row.get(
                        "primary_teacher_first_name"
                    ),
                    primary_teacher_last_name=row.get("primary_teacher_last_name"),
                    primary_teacher_file_pattern=row.get(
                        "primary_teacher_file_pattern"
                    ),
                    display_order=row.get("display_order", 0),
                    created_at=parse_datetime(row.get("created_at")),
                    updated_at=parse_datetime(row.get("updated_at")),
                )
            )
        return slots
    else:
        with Session(db.engine) as session:
            statement = (
                select(ClassSlot)
                .where(ClassSlot.user_id == user_id)
                .order_by(ClassSlot.slot_number)
            )
            return list(session.exec(statement).all())


def get_slot(db, slot_id: str) -> Optional[ClassSlot]:
    """Get a specific class slot."""
    with Session(db.engine) as session:
        return session.get(ClassSlot, slot_id)


def update_class_slot(db, slot_id: str, **kwargs) -> bool:
    """Update class slot configuration."""
    try:
        with Session(db.engine) as session:
            slot = session.get(ClassSlot, slot_id)
            if not slot:
                return False

            for key, value in kwargs.items():
                if hasattr(slot, key):
                    setattr(slot, key, value)

            if (
                "primary_teacher_first_name" in kwargs
                or "primary_teacher_last_name" in kwargs
            ):
                f = kwargs.get(
                    "primary_teacher_first_name", slot.primary_teacher_first_name
                )
                l = kwargs.get(
                    "primary_teacher_last_name", slot.primary_teacher_last_name
                )
                slot.primary_teacher_name = f"{f or ''} {l or ''}".strip()

            slot.updated_at = datetime.utcnow()
            session.add(slot)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating class slot: {e}")
        return False


def delete_class_slot(db, slot_id: str) -> bool:
    """Delete a class slot."""
    try:
        with Session(db.engine) as session:
            slot = session.get(ClassSlot, slot_id)
            if not slot:
                return False
            session.delete(slot)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting class slot: {e}")
        return False


def delete_user_slots(db, user_id: str) -> int:
    """Delete all class slots for a user."""
    try:
        with Session(db.engine) as session:
            statement = delete(ClassSlot).where(ClassSlot.user_id == user_id)
            result = session.exec(statement)
            session.commit()
            return result.rowcount
    except Exception as e:
        logger.error(f"Error deleting user slots: {e}")
        return 0
