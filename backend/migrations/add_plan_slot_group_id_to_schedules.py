"""
Migration to add plan_slot_group_id column to schedules table.
Allows linking multiple periods to the same lesson plan slot.
"""

import sqlite3
from pathlib import Path

from backend.config import settings
from backend.telemetry import logger


def migrate():
    """Add plan_slot_group_id column and index if missing."""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    db_file = Path(db_path)

    if not db_file.exists():
        logger.warning(f"Database file not found at {db_path}, skipping migration")
        return

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schedules'
            """
        )
        if not cursor.fetchone():
            logger.warning("schedules table does not exist, skipping migration")
            return

        cursor.execute("PRAGMA table_info('schedules')")
        columns = [row[1] for row in cursor.fetchall()]

        if "plan_slot_group_id" not in columns:
            logger.info("Adding plan_slot_group_id column to schedules table")
            cursor.execute(
                "ALTER TABLE schedules ADD COLUMN plan_slot_group_id TEXT"
            )
        else:
            logger.info("plan_slot_group_id column already exists, skipping add")

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_schedules_plan_group
            ON schedules(plan_slot_group_id)
            """
        )

        conn.commit()
        logger.info("Successfully ensured plan_slot_group_id column and index exist")
    except Exception as exc:
        conn.rollback()
        logger.error("schedules_plan_group_migration_failed", extra={"error": str(exc)})
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

