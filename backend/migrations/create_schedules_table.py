"""
Migration to create schedules table for schedule management.

This migration creates the schedules table to store teacher schedules
with time slots, subjects, grades, and homerooms for each day of the week.
"""

import sqlite3
from pathlib import Path
from backend.config import settings
from backend.telemetry import logger


def migrate():
    """Create schedules table if it doesn't exist."""
    # Extract path from sqlite:///./data/lesson_plans.db format
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    db_file = Path(db_path)
    
    if not db_file.exists():
        logger.warning(f"Database file not found at {db_path}, skipping migration")
        return
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schedules'
        """)
        
        if cursor.fetchone():
            logger.info("schedules table already exists, skipping migration")
            return
        
        # Create schedules table
        cursor.execute("""
            CREATE TABLE schedules (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                subject TEXT NOT NULL,
                homeroom TEXT,
                grade TEXT,
                plan_slot_group_id TEXT,
                slot_number INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX idx_schedules_user_day 
            ON schedules(user_id, day_of_week)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_schedules_user_time 
            ON schedules(user_id, day_of_week, start_time)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_schedules_current 
            ON schedules(user_id, is_active, day_of_week, start_time, end_time)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_schedules_homeroom 
            ON schedules(user_id, homeroom, day_of_week)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_schedules_grade 
            ON schedules(user_id, grade, day_of_week)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_schedules_plan_group
            ON schedules(plan_slot_group_id)
        """)
        
        conn.commit()
        logger.info("Successfully created schedules table and indexes")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating schedules table: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

