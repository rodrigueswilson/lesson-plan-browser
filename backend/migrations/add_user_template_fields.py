"""
Migration: Add template_path and signature_image_path fields to users table.

This allows each user to have their own lesson plan template and signature image.
"""

import sqlite3
from pathlib import Path


def migrate(db_path: str):
    """Add template_path and signature_image_path columns to users table.
    
    Args:
        db_path: Path to the database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add template_path column if it doesn't exist
        if 'template_path' not in columns:
            print("Adding template_path column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN template_path TEXT
            """)
            print("✓ Added template_path column")
        else:
            print("template_path column already exists")
        
        # Add signature_image_path column if it doesn't exist
        if 'signature_image_path' not in columns:
            print("Adding signature_image_path column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN signature_image_path TEXT
            """)
            print("✓ Added signature_image_path column")
        else:
            print("signature_image_path column already exists")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Default database path
    db_path = Path(__file__).parent.parent.parent / "data" / "lesson_planner.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Please provide the database path as an argument")
        exit(1)
    
    print(f"Running migration on database: {db_path}")
    migrate(str(db_path))

