"""User CRUD operations for SQLite database."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, delete, select

from backend.schema import ClassSlot, ScheduleEntry, User, WeeklyPlan

logger = logging.getLogger(__name__)


def create_user(
    db,
    first_name: str = None,
    last_name: str = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> str:
    """Create a new user."""
    try:
        if name and not first_name and not last_name:
            parts = name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        if not name:
            name = f"{first_name} {last_name}".strip()

        user = User(
            id=f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        with Session(db.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise


def get_user(db, user_id: str) -> Optional[User]:
    """Get user by ID - works in both modes."""
    if db.use_ipc:
        row = db._adapter.query_one("SELECT * FROM users WHERE id = ?", [user_id])
        if not row:
            return None

        def parse_datetime(dt_value):
            if isinstance(dt_value, datetime):
                return dt_value
            if isinstance(dt_value, str):
                try:
                    return datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return datetime.utcnow()
            return datetime.utcnow()

        return User(
            id=row["id"],
            email=row.get("email"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            name=row.get("name", ""),
            base_path_override=row.get("base_path_override"),
            template_path=row.get("template_path"),
            signature_image_path=row.get("signature_image_path"),
            created_at=parse_datetime(row.get("created_at")),
            updated_at=parse_datetime(row.get("updated_at")),
        )
    else:
        with Session(db.engine) as session:
            return session.get(User, user_id)


def get_user_by_name(db, name: str) -> Optional[User]:
    """Get user by name."""
    with Session(db.engine) as session:
        statement = select(User).where(User.name == name)
        return session.exec(statement).first()


def list_users(db) -> List[User]:
    """Get all users."""
    with Session(db.engine) as session:
        statement = select(User)
        return list(session.exec(statement).all())


def update_user(
    db,
    user_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> bool:
    """Update user information."""
    try:
        with Session(db.engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False

            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if email is not None:
                user.email = email

            if name:
                user.name = name
            elif first_name is not None or last_name is not None:
                f = first_name if first_name is not None else user.first_name
                l = last_name if last_name is not None else user.last_name
                user.name = f"{f} {l}".strip()

            user.updated_at = datetime.utcnow()
            session.add(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return False


def update_user_base_path(db, user_id: str, base_path: str) -> bool:
    """Update user's base path override."""
    try:
        with Session(db.engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False
            user.base_path_override = base_path
            user.updated_at = datetime.utcnow()
            session.add(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating user base path: {e}")
        return False


def update_user_template_paths(
    db,
    user_id: str,
    template_path: Optional[str] = None,
    signature_image_path: Optional[str] = None,
) -> bool:
    """Update user's template path and/or signature image path."""
    try:
        with Session(db.engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False

            if template_path is not None:
                user.template_path = template_path
            if signature_image_path is not None:
                user.signature_image_path = signature_image_path

            user.updated_at = datetime.utcnow()
            session.add(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating user template paths: {e}")
        return False


def delete_user(db, user_id: str) -> bool:
    """Delete user and all associated data."""
    try:
        with Session(db.engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False

            session.exec(delete(ClassSlot).where(ClassSlot.user_id == user_id))
            session.exec(delete(WeeklyPlan).where(WeeklyPlan.user_id == user_id))
            session.exec(
                delete(ScheduleEntry).where(ScheduleEntry.user_id == user_id)
            )

            session.delete(user)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False
