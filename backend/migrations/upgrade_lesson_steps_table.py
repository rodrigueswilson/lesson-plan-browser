"""
Migration helper to upgrade legacy lesson_steps tables to the new schema.

The legacy table used columns such as plan_id/content, while the current schema
stores lesson_plan_id, step metadata, and JSON/text fields that align with the
API contract. This script copies data into the new structure while providing
reasonable defaults for newly introduced columns.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings
from backend.telemetry import logger

NEW_COLUMNS = [
    "id",
    "lesson_plan_id",
    "day_of_week",
    "slot_number",
    "step_number",
    "step_name",
    "duration_minutes",
    "start_time_offset",
    "content_type",
    "display_content",
    "hidden_content",
    "sentence_frames",
    "materials_needed",
    "created_at",
    "updated_at",
]


def _load_rows(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    cursor.execute("SELECT * FROM lesson_steps")
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _serialize_materials(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(",") if item.strip()]
        if not parts:
            return None
        return json.dumps(parts)
    if isinstance(value, list):
        return json.dumps(value)
    return json.dumps([value])


def _build_new_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    upgraded = []
    for row in rows:
        duration = row.get("duration_minutes") or 0
        step_number = row.get("step_number") or 1
        start_offset = max(step_number - 1, 0) * duration
        upgraded.append(
            {
                "id": row["id"],
                "lesson_plan_id": row.get("plan_id") or row.get("lesson_plan_id"),
                "day_of_week": (row.get("day_of_week") or "").lower(),
                "slot_number": row.get("slot_number"),
                "step_number": step_number,
                "step_name": row.get("step_name") or f"Step {step_number}",
                "duration_minutes": duration,
                "start_time_offset": start_offset,
                "content_type": row.get("content_type") or "instruction",
                "display_content": row.get("display_content")
                or row.get("content")
                or "",
                "hidden_content": row.get("hidden_content"),
                "sentence_frames": row.get("sentence_frames"),
                "materials_needed": _serialize_materials(row.get("materials_needed")),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at") or row.get("created_at"),
            }
        )
    return upgraded


def _create_new_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lesson_steps_new (
            id TEXT PRIMARY KEY,
            lesson_plan_id TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            slot_number INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            start_time_offset INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            display_content TEXT NOT NULL,
            hidden_content TEXT,
            sentence_frames TEXT,
            materials_needed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
            UNIQUE(lesson_plan_id, day_of_week, slot_number, step_number)
        )
        """
    )


def _create_indexes(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_day_slot
        ON lesson_steps(lesson_plan_id, day_of_week, slot_number)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_id
        ON lesson_steps(lesson_plan_id)
        """
    )


def upgrade_lesson_steps_table(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(lesson_steps)")
    columns = {row[1] for row in cursor.fetchall()}

    if not columns:
        logger.info("lesson_steps table not found; nothing to upgrade")
        conn.close()
        return

    if "lesson_plan_id" in columns and "display_content" in columns:
        logger.info("lesson_steps table already matches current schema")
        conn.close()
        return

    logger.info("lesson_steps_table_upgrade_start")
    rows = _load_rows(cursor)
    upgraded_rows = _build_new_rows(rows)

    try:
        cursor.execute("BEGIN")
        _create_new_table(cursor)
        cursor.executemany(
            f"""
            INSERT OR REPLACE INTO lesson_steps_new ({", ".join(NEW_COLUMNS)})
            VALUES ({", ".join(["?"] * len(NEW_COLUMNS))})
            """,
            [[row.get(column) for column in NEW_COLUMNS] for row in upgraded_rows],
        )
        cursor.execute("DROP TABLE lesson_steps")
        cursor.execute("ALTER TABLE lesson_steps_new RENAME TO lesson_steps")
        _create_indexes(cursor)
        conn.commit()
        logger.info(
            "lesson_steps_table_upgrade_complete",
            extra={"rows_migrated": len(upgraded_rows)},
        )
        print(f"Upgraded lesson_steps table ({len(upgraded_rows)} rows migrated)")
    except Exception as exc:  # pragma: no cover
        conn.rollback()
        logger.error("lesson_steps_table_upgrade_failed", extra={"error": str(exc)})
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    sqlite_path = settings.SQLITE_DB_PATH
    upgrade_lesson_steps_table(sqlite_path)
