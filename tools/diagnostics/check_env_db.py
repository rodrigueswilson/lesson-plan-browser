"""Check which database file is being used."""

import os
from pathlib import Path
from backend.config import settings

print("=" * 80)
print("DATABASE CONFIGURATION CHECK")
print("=" * 80)

# Check environment variable
env_db = os.getenv("DATABASE_URL")
print(f"\nEnvironment variable DATABASE_URL: {env_db}")

# Check settings
print(f"Settings DATABASE_URL: {settings.DATABASE_URL}")

# Extract actual path
db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
db_path = Path(db_path)

print(f"\nResolved path: {db_path}")
print(f"Absolute path: {db_path.absolute()}")
print(f"File exists: {db_path.exists()}")

if db_path.exists():
    print(f"File size: {db_path.stat().st_size:,} bytes")
    
    # Check for users
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users in database: {user_count}")
    conn.close()
else:
    print("❌ Database file does not exist!")

# Check what files exist
print("\n" + "=" * 80)
print("DATABASE FILES IN data/")
print("=" * 80)

data_dir = Path("data")
if data_dir.exists():
    for db_file in data_dir.glob("*.db"):
        print(f"\n📁 {db_file.name}")
        print(f"   Size: {db_file.stat().st_size:,} bytes")
        
        # Check users
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"   Users: {count}")
            conn.close()
        except:
            print(f"   Users: (error reading)")
