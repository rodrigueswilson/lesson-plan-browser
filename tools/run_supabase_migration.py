"""
Simple script to run Supabase migration.
Tries multiple approaches to execute the migration automatically.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings

# Read the migration SQL
migration_file = Path(__file__).parent.parent / "sql" / "add_user_template_fields.sql"
migration_sql = migration_file.read_text() if migration_file.exists() else ""

print("=" * 70)
print("SUPABASE MIGRATION: Add template_path and signature_image_path columns")
print("=" * 70)
print(f"\nProject: {settings.SUPABASE_PROJECT}")
print(f"Supabase URL: {settings.supabase_url}")

# Try approach 1: Direct PostgreSQL connection with psycopg2
print("\n[Approach 1] Trying direct PostgreSQL connection...")
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from urllib.parse import urlparse
    
    supabase_url = settings.supabase_url
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    if db_password and supabase_url:
        parsed = urlparse(supabase_url)
        host = parsed.hostname
        conn_string = f"postgresql://postgres:{db_password}@{host}:5432/postgres"
        
        print(f"Connecting to {host}...")
        conn = psycopg2.connect(conn_string, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Executing migration SQL...")
        cursor.execute(migration_sql)
        
        # Verify
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('template_path', 'signature_image_path')
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        if len(columns) == 2:
            print("[SUCCESS] Migration successful! Both columns added.")
            sys.exit(0)
        else:
            print(f"[WARNING] Migration executed but only found {len(columns)} columns")
    else:
        print("[INFO] Database password not set (SUPABASE_DB_PASSWORD)")
        
except ImportError:
    print("[INFO] psycopg2 not installed")
except Exception as e:
    print(f"[INFO] Direct connection failed: {e}")

# If direct connection didn't work, provide manual instructions
print("\n" + "=" * 70)
print("MANUAL MIGRATION REQUIRED")
print("=" * 70)
print("\nPlease run the following SQL in your Supabase Dashboard:")
print("\n1. Go to: https://supabase.com/dashboard")
print(f"2. Select your project")
print("3. Click 'SQL Editor' in the left sidebar")
print("4. Click 'New query'")
print("5. Paste and run this SQL:\n")
print("-" * 70)
print(migration_sql)
print("-" * 70)
print("\n6. Verify in 'Table Editor' -> 'users' table that both columns exist")
print("\n" + "=" * 70)

sys.exit(1)

