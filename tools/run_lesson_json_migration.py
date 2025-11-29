"""
Script to run the lesson_json column migration for Supabase.
Adds the lesson_json JSONB column to the weekly_plans table.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings


def run_migration():
    """Run the lesson_json column migration."""
    # Read the migration SQL
    migration_file = Path(__file__).parent.parent / "sql" / "add_lesson_json_column.sql"
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    migration_sql = migration_file.read_text()
    
    print("=" * 70)
    print("SUPABASE MIGRATION: Add lesson_json column to weekly_plans")
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
            # Execute each statement separately
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
            for stmt in statements:
                if stmt:
                    cursor.execute(stmt)
            
            # Verify column was added
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'weekly_plans' 
                AND column_name = 'lesson_json'
            """)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                print(f"\n[SUCCESS] Migration successful! Column '{result[0]}' ({result[1]}) added.")
                
                # Check indexes
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'weekly_plans' 
                    AND indexname LIKE '%lesson_json%'
                """)
                indexes = [row[0] for row in cursor2.fetchall()]
                cursor2.close()
                conn.close()
                
                print(f"Indexes created: {', '.join(indexes) if indexes else 'None'}")
                return True
            else:
                print("[WARNING] Migration executed but column not found")
        else:
            print("[INFO] Database password not set (SUPABASE_DB_PASSWORD env var)")
            
    except ImportError:
        print("[INFO] psycopg2 not installed - install with: pip install psycopg2-binary")
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
    print("\n6. Verify in 'Table Editor' -> 'weekly_plans' table that 'lesson_json' column exists")
    print("\n" + "=" * 70)
    
    return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

