"""
Database migration: Add week_folder_path column to weekly_plans table
"""

import sqlite3
from pathlib import Path

def migrate():
    """Add week_folder_path column to weekly_plans table."""
    db_path = Path("data/lesson_planner.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("No migration needed - fresh database will have the column")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(weekly_plans)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'week_folder_path' in columns:
            print("Column 'week_folder_path' already exists in weekly_plans table")
            print("No migration needed")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE weekly_plans 
                ADD COLUMN week_folder_path TEXT
            """)
            conn.commit()
            print("Successfully added 'week_folder_path' column to weekly_plans table")
        
        # Show current schema
        cursor.execute("PRAGMA table_info(weekly_plans)")
        print("\nCurrent weekly_plans schema:")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")
    
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Add week_folder_path column")
    print("=" * 60)
    print()
    migrate()
    print()
    print("=" * 60)
    print("Migration complete")
    print("=" * 60)
