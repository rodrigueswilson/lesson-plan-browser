
import sqlite3
import os
from pathlib import Path

def migrate_db():
    # Path to the database
    db_path = Path("data/lesson_planner.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Migrating database at {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(lesson_steps)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Add vocabulary_cognates if missing
        if "vocabulary_cognates" not in columns:
            print("Adding vocabulary_cognates column...")
            cursor.execute("ALTER TABLE lesson_steps ADD COLUMN vocabulary_cognates JSON")
        else:
            print("vocabulary_cognates column already exists.")
            
        # Add sentence_frames if missing
        if "sentence_frames" not in columns:
            print("Adding sentence_frames column...")
            cursor.execute("ALTER TABLE lesson_steps ADD COLUMN sentence_frames JSON")
        else:
            print("sentence_frames column already exists.")
            
        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    # Ensure we are in the root directory or adjust path
    if not Path("data").exists():
        # Try to find the data directory relative to the script if run from scripts/
        if Path("../data").exists():
            os.chdir("..")
            
    migrate_db()
