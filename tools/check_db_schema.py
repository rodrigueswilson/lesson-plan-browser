"""Check database schema and recent entries."""

import sqlite3

DB_PATH = r'd:\LP\data\lesson_plans.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("="*80)
print("DATABASE TABLES")
print("="*80)
print()

for (table_name,) in tables:
    print(f"Table: {table_name}")
    
    # Get schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"  Columns:")
    for col in columns:
        print(f"    - {col[1]} ({col[2]})")
    
    # Get count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")
    print()

conn.close()
