"""Check database schema."""

import sqlite3
from pathlib import Path

db_path = Path("data/lesson_planner.db")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=" * 80)
print("DATABASE SCHEMA")
print("=" * 80)

for (table_name,) in tables:
    print(f"\n📋 Table: {table_name}")
    
    # Get table info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"   - {name}: {col_type}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   Rows: {count}")

conn.close()
