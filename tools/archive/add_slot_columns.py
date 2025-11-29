"""
Add missing columns to class_slots table.
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
    # Check current columns
    cursor.execute("PRAGMA table_info(class_slots)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Add missing columns
    columns_to_add = [
        ('primary_teacher_name', 'TEXT'),
        ('primary_teacher_file_pattern', 'TEXT'),
        ('display_order', 'INTEGER'),
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name in columns:
            print(f"✓ Column '{col_name}' already exists")
        else:
            cursor.execute(f"ALTER TABLE class_slots ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"✓ Added '{col_name}' column to class_slots table")
    
    # Verify
    cursor.execute("PRAGMA table_info(class_slots)")
    print("\nCurrent class_slots table schema:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")
    
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✓ Database migration complete!")
