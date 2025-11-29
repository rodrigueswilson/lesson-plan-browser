"""
Migration script to create lesson_mode_sessions table for Lesson Mode state persistence.
Supports both SQLite and Supabase.
"""

import sqlite3
from pathlib import Path
from backend.config import settings
from backend.telemetry import logger

def create_lesson_mode_sessions_table_sqlite(db_path: str = "data/lesson_plans.db"):
    """Create lesson_mode_sessions table in SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_mode_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                lesson_plan_id TEXT NOT NULL,
                schedule_entry_id TEXT,
                day_of_week TEXT NOT NULL,
                slot_number INTEGER NOT NULL,
                current_step_index INTEGER NOT NULL DEFAULT 0,
                remaining_time INTEGER NOT NULL DEFAULT 0,
                is_running INTEGER NOT NULL DEFAULT 0,
                is_paused INTEGER NOT NULL DEFAULT 0,
                is_synced INTEGER NOT NULL DEFAULT 0,
                timer_start_time TEXT,
                paused_at INTEGER,
                adjusted_durations TEXT,
                session_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (lesson_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (schedule_entry_id) REFERENCES schedules(id) ON DELETE SET NULL
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_user_id 
            ON lesson_mode_sessions(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_plan_id 
            ON lesson_mode_sessions(lesson_plan_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_active 
            ON lesson_mode_sessions(user_id, ended_at)
            WHERE ended_at IS NULL
        """)
        
        conn.commit()
        logger.info("✅ Created lesson_mode_sessions table in SQLite database")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create lesson_mode_sessions table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def run_migration():
    """Run the migration."""
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Running migration: create_lesson_mode_sessions_table")
    success = create_lesson_mode_sessions_table_sqlite(str(db_path))
    
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        exit(1)

if __name__ == "__main__":
    run_migration()

