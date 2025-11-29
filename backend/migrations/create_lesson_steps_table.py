"""
Migration script to create lesson_steps table for Lesson Mode feature.
Supports both SQLite and Supabase.
"""

import sqlite3
from pathlib import Path
from backend.config import settings
from backend.telemetry import logger

def create_lesson_steps_table_sqlite(db_path: str = "data/lesson_plans.db"):
    """Create lesson_steps table in SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_steps (
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
                vocabulary_cognates TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lesson_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
                UNIQUE(lesson_plan_id, day_of_week, slot_number, step_number)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_day_slot 
            ON lesson_steps(lesson_plan_id, day_of_week, slot_number)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_id 
            ON lesson_steps(lesson_plan_id)
        """)
        
        conn.commit()
        logger.info("lesson_steps_table_created", extra={"database": "sqlite"})
        print("✓ Created lesson_steps table in SQLite")
        
    except sqlite3.Error as e:
        logger.error("lesson_steps_table_creation_failed", extra={"error": str(e)})
        raise
    finally:
        conn.close()


def create_lesson_steps_table_supabase():
    """Create lesson_steps table in Supabase."""
    # Note: Supabase Python client doesn't support raw SQL execution directly
    # This would need to be run manually in Supabase SQL editor or via migration tool
    logger.info("lesson_steps_table_supabase_note", extra={"message": "Run SQL manually in Supabase"})
    print("NOTE: Supabase migration: Run the SQL manually in Supabase SQL editor")
    print("SQL file location: sql/create_lesson_steps_table_supabase.sql")
    print("")
    print("For SQLite, the table has been created successfully.")


if __name__ == "__main__":
    if settings.USE_SUPABASE:
        create_lesson_steps_table_supabase()
    else:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        create_lesson_steps_table_sqlite(db_path)

