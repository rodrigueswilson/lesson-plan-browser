"""
Migration script to add parallel processing metrics to performance_metrics table.
Adds fields for tracking parallel processing performance, rate limits, and concurrency.
Supports both SQLite and Supabase.
"""

import sqlite3
from pathlib import Path
from backend.config import settings
from backend.telemetry import logger


def add_parallel_processing_fields_sqlite(db_path: str = "data/lesson_planner.db"):
    """Add parallel processing fields to performance_metrics table in SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(performance_metrics)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ("is_parallel", "INTEGER DEFAULT 0", "Whether operation was processed in parallel"),
            ("parallel_slot_count", "INTEGER", "Number of slots processed in parallel"),
            ("sequential_time_ms", "REAL", "Estimated time if processed sequentially"),
            ("rate_limit_errors", "INTEGER DEFAULT 0", "Number of rate limit errors encountered"),
            ("concurrency_level", "INTEGER", "Actual concurrency level used"),
            ("tpm_usage", "INTEGER", "Tokens per minute usage at time of request"),
            ("rpm_usage", "INTEGER", "Requests per minute usage at time of request"),
        ]
        
        for column_name, column_type, description in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE performance_metrics 
                        ADD COLUMN {column_name} {column_type}
                    """)
                    logger.info(
                        "parallel_processing_column_added",
                        extra={"column": column_name, "database": "sqlite"}
                    )
                    print(f"✓ Added column {column_name} to performance_metrics table")
                except sqlite3.Error as e:
                    logger.warning(
                        "parallel_processing_column_add_failed",
                        extra={"column": column_name, "error": str(e)}
                    )
                    print(f"⚠ Warning: Could not add column {column_name}: {e}")
            else:
                logger.info(
                    "parallel_processing_column_exists",
                    extra={"column": column_name}
                )
                print(f"✓ Column {column_name} already exists")
        
        conn.commit()
        logger.info("parallel_processing_migration_completed", extra={"database": "sqlite"})
        print("✓ Parallel processing metrics migration completed for SQLite")
        
    except sqlite3.Error as e:
        logger.error("parallel_processing_migration_failed", extra={"error": str(e)})
        raise
    finally:
        conn.close()


def add_parallel_processing_fields_supabase():
    """Add parallel processing fields to performance_metrics table in Supabase."""
    # Note: Supabase Python client doesn't support raw SQL execution directly
    # This would need to be run manually in Supabase SQL editor or via migration tool
    logger.info("parallel_processing_migration_supabase_note", extra={
        "message": "Run SQL manually in Supabase"
    })
    print("NOTE: Supabase migration: Run the SQL manually in Supabase SQL editor")
    print("SQL file location: sql/add_parallel_processing_metrics_supabase.sql")
    print("")
    print("For SQLite, the migration has been completed successfully.")


if __name__ == "__main__":
    if settings.USE_SUPABASE:
        add_parallel_processing_fields_supabase()
    else:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not db_path or db_path == settings.DATABASE_URL:
            # Fallback to default path
            db_path = str(settings.SQLITE_DB_PATH)
        add_parallel_processing_fields_sqlite(db_path)
