"""Check which database is being used."""

from backend.config import settings
from pathlib import Path

print("=" * 80)
print("DATABASE CONFIGURATION")
print("=" * 80)

print(f"\nDATABASE_URL from config: {settings.DATABASE_URL}")

# Parse the path
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    db_path = Path(db_path)
    
    print(f"Parsed path: {db_path}")
    print(f"Absolute path: {db_path.absolute()}")
    print(f"Exists: {db_path.exists()}")
    
    if db_path.exists():
        print(f"Size: {db_path.stat().st_size:,} bytes")
        
        # Check schema
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(weekly_plans)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\nColumns in weekly_plans table:")
        for col in columns:
            print(f"  - {col}")
        
        if "week_folder_path" in columns:
            print("\n✅ week_folder_path column EXISTS")
        else:
            print("\n❌ week_folder_path column MISSING - THIS IS THE PROBLEM!")
        
        conn.close()
