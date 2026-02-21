"""
Migration script to create original_lesson_plans table.
Stores extracted content from primary teacher files before LLM transformation.
Supports both SQLite and Supabase.
"""

import sqlite3
import hashlib
from pathlib import Path
from backend.config import settings
from backend.telemetry import logger


def create_original_lesson_plans_table_sqlite(db_path: str = "data/lesson_plans.db"):
    """Create original_lesson_plans table in SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS original_lesson_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                week_of TEXT NOT NULL,
                slot_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                grade TEXT NOT NULL,
                homeroom TEXT,
                
                -- Source file information
                source_file_path TEXT NOT NULL,
                source_file_name TEXT NOT NULL,
                primary_teacher_name TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Extracted content (structured)
                content_json TEXT NOT NULL,  -- JSON string
                full_text TEXT,  -- Plain text version for LLM
                
                -- Per-day content breakdown (optional)
                monday_content TEXT,
                tuesday_content TEXT,
                wednesday_content TEXT,
                thursday_content TEXT,
                friday_content TEXT,
                
                -- Metadata
                available_days TEXT,  -- JSON array: ['monday', 'tuesday', ...]
                has_no_school INTEGER DEFAULT 0,
                content_hash TEXT,  -- Hash for change detection
                
                -- Status
                status TEXT DEFAULT 'extracted',  -- 'extracted', 'processed', 'error'
                error_message TEXT,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, week_of, slot_number)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_original_plans_user_week 
            ON original_lesson_plans(user_id, week_of)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_original_plans_status 
            ON original_lesson_plans(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_original_plans_slot 
            ON original_lesson_plans(user_id, week_of, slot_number)
        """)
        
        conn.commit()
        logger.info("original_lesson_plans_table_created", extra={"database": "sqlite"})
        print("✓ Created original_lesson_plans table in SQLite")
        
    except sqlite3.Error as e:
        logger.error("original_lesson_plans_table_creation_failed", extra={"error": str(e)})
        raise
    finally:
        conn.close()


def create_original_lesson_plans_table_supabase():
    """Create original_lesson_plans table in Supabase."""
    # Note: Supabase Python client doesn't support raw SQL execution directly
    # This would need to be run manually in Supabase SQL editor or via migration tool
    logger.info("original_lesson_plans_table_supabase_note", extra={"message": "Run SQL manually in Supabase"})
    print("NOTE: Supabase migration: Run the SQL manually in Supabase SQL editor")
    print("SQL file location: sql/create_original_lesson_plans_table_supabase.sql")
    print("")
    print("For SQLite, the table has been created successfully.")


if __name__ == "__main__":
    if settings.USE_SUPABASE:
        create_original_lesson_plans_table_supabase()
    else:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        create_original_lesson_plans_table_sqlite(db_path)
