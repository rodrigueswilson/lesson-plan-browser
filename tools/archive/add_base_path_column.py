"""
Add base_path_override column to users table.
Run this once to update the database schema.
"""

import sqlite3
from pathlib import Path

db_path = Path("data/lesson_planner.db")

if not db_path.exists():
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'base_path_override' in columns:
        print("✓ Column 'base_path_override' already exists")
    else:
        # Add the column
        cursor.execute("ALTER TABLE users ADD COLUMN base_path_override TEXT")
        conn.commit()
        print("✓ Added 'base_path_override' column to users table")
    
    # Verify
    cursor.execute("PRAGMA table_info(users)")
    print("\nCurrent users table schema:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")
    
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✓ Database migration complete!")
