"""
Engine creation, WAL, connection context, init_db, and shared helpers for SQLite database.
"""

import json
import logging
from contextlib import contextmanager
from pathlib import Path as PathType
from typing import Any, Optional, Tuple, Union

from sqlmodel import Session, SQLModel, create_engine, text

from backend.config import settings
from backend.schema import LessonStep

logger = logging.getLogger(__name__)


def build_engine(
    db_path: Optional[Union[str, PathType]] = None,
    use_ipc: bool = False,
    **kwargs,
) -> Tuple[Any, Optional[PathType], bool, Any]:
    """
    Create SQLite engine and optional IPC adapter.

    Returns:
        Tuple of (engine, db_path, use_ipc, adapter).
        For non-IPC: adapter is None. For IPC: engine is None, adapter is IPCDatabaseAdapter.
    """
    path_arg = db_path if db_path is not None else kwargs.get("db_path")

    if use_ipc:
        from backend.ipc_database import IPCDatabaseAdapter

        adapter = IPCDatabaseAdapter()
        return None, None, True, adapter

    if path_arg is not None:
        path_str = str(path_arg)
        if path_str == ":memory:":
            db_path_resolved = PathType(":memory:")
            sqlite_url = "sqlite:///:memory:"
        else:
            db_path_resolved = (
                PathType(path_arg) if not isinstance(path_arg, PathType) else path_arg
            )
            db_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            sqlite_url = f"sqlite:///{db_path_resolved}"
    else:
        db_path_resolved = settings.SQLITE_DB_PATH
        db_path_resolved.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{db_path_resolved}"

    engine = create_engine(
        sqlite_url, connect_args={"check_same_thread": False}
    )
    if ":memory:" not in sqlite_url:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()
        logger.debug("SQLite WAL mode enabled (reduces locking risk)")

    return engine, db_path_resolved, False, None


@contextmanager
def get_connection(engine):
    """Yield a SQLModel Session for the given engine."""
    with Session(engine) as session:
        yield session


def init_db(engine) -> None:
    """Initialize database schema on the given engine."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def _normalize_day(day: Optional[str]) -> Optional[str]:
    if isinstance(day, str):
        return day.lower()
    return day


def _coerce_json_field(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def hydrate_lesson_step(step: LessonStep, coerce_fn) -> LessonStep:
    """Ensure JSON/text fields on a LessonStep are returned as Python objects."""
    step.hidden_content = coerce_fn(getattr(step, "hidden_content", None))
    step.sentence_frames = coerce_fn(getattr(step, "sentence_frames", None))
    step.materials_needed = coerce_fn(getattr(step, "materials_needed", None))
    step.vocabulary_cognates = coerce_fn(getattr(step, "vocabulary_cognates", None))
    if step.day_of_week:
        step.day_of_week = step.day_of_week.lower()
    return step
