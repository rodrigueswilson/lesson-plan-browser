"""
Add vocabulary_cognates column to lesson_steps table if it doesn't exist.
"""
import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from backend.config import settings

db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
if not db_path.exists():
    print(f"[FAIL] Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(lesson_steps)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "vocabulary_cognates" in columns:
        print("[OK] vocabulary_cognates column already exists")
    else:
        print("[INFO] Adding vocabulary_cognates column...")
        cursor.execute("""
            ALTER TABLE lesson_steps 
            ADD COLUMN vocabulary_cognates TEXT
        """)
        conn.commit()
        print("[OK] vocabulary_cognates column added successfully")
    
    # Verify
    cursor.execute("PRAGMA table_info(lesson_steps)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"\nColumns in lesson_steps table:")
    for col in columns:
        print(f"  - {col}")
    
except sqlite3.Error as e:
    print(f"[FAIL] Error: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()

print("\n[SUCCESS] Migration complete!")

