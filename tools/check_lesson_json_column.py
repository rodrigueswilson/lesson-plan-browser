"""
Script to check if lesson_json column exists in Supabase weekly_plans table.
Also tests if the update_weekly_plan method works correctly.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.supabase_database import SupabaseDatabase


def check_column_exists():
    """Check if lesson_json column exists in weekly_plans table."""
    print("=" * 70)
    print("CHECKING lesson_json COLUMN IN SUPABASE")
    print("=" * 70)
    print(f"\nProject: {settings.SUPABASE_PROJECT}")
    print(f"Supabase URL: {settings.supabase_url}")
    
    try:
        # Initialize database
        db = SupabaseDatabase()
        
        # Method 1: Try to query the column directly
        print("\n[Method 1] Attempting to query lesson_json column directly...")
        try:
            # Try to select from weekly_plans with lesson_json
            result = db.client.table("weekly_plans").select("id, lesson_json").limit(1).execute()
            print("[OK] Column exists and is accessible!")
            print(f"  Found {len(result.data)} plan(s) (sample query successful)")
            column_exists = True
        except Exception as e:
            error_msg = str(e)
            if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                print(f"[ERROR] Column does NOT exist: {error_msg}")
                column_exists = False
            elif "permission" in error_msg.lower() or "authorization" in error_msg.lower():
                print(f"[WARNING] Permission error (but column might exist): {error_msg}")
                column_exists = None  # Unknown
            else:
                print(f"[WARNING] Unexpected error: {error_msg}")
                column_exists = None
        
        # Method 2: Try to get a plan and check if lesson_json is in the response
        print("\n[Method 2] Checking if lesson_json appears in plan data...")
        try:
            # Get plans by querying the table directly
            plans_result = db.client.table("weekly_plans").select("*").limit(1).execute()
            plans = plans_result.data if plans_result.data else []
            if plans:
                plan = plans[0]
                if 'lesson_json' in plan:
                    print("[OK] Column exists! Found 'lesson_json' key in plan data")
                    print(f"  Type: {type(plan.get('lesson_json'))}")
                    if plan.get('lesson_json'):
                        lesson_json_val = plan['lesson_json']
                        if isinstance(lesson_json_val, str):
                            print(f"  Value is stored as string (length: {len(lesson_json_val)})")
                            try:
                                parsed = json.loads(lesson_json_val)
                                print(f"  Can be parsed as JSON: YES")
                            except:
                                print(f"  Cannot be parsed as JSON: NO")
                        elif isinstance(lesson_json_val, dict):
                            print(f"  Value is stored as dict/JSONB: YES")
                    else:
                        print(f"  Value is NULL/empty")
                    column_exists = True
                else:
                    print("[ERROR] Column does NOT exist - 'lesson_json' key missing from plan")
                    print(f"  Available keys: {list(plan.keys())[:10]}")
                    column_exists = False
            else:
                print("[WARNING] No plans found in database (cannot verify column)")
                column_exists = None
        except Exception as e:
            print(f"[WARNING] Error checking plans: {e}")
            column_exists = None
        
        # Method 3: Try direct PostgreSQL query if psycopg2 is available
        print("\n[Method 3] Attempting direct PostgreSQL query...")
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            supabase_url = settings.supabase_url
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            
            if db_password and supabase_url:
                parsed = urlparse(supabase_url)
                host = parsed.hostname
                conn_string = f"postgresql://postgres:{db_password}@{host}:5432/postgres"
                
                conn = psycopg2.connect(conn_string, connect_timeout=10)
                cursor = conn.cursor()
                
                # Check column
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'weekly_plans' 
                    AND column_name = 'lesson_json'
                """)
                result = cursor.fetchone()
                
                if result:
                    print(f"[OK] Column exists in database:")
                    print(f"  Column: {result[0]}")
                    print(f"  Type: {result[1]}")
                    print(f"  Nullable: {result[2]}")
                    
                    # Check indexes
                    cursor.execute("""
                        SELECT indexname, indexdef
                        FROM pg_indexes 
                        WHERE tablename = 'weekly_plans' 
                        AND indexname LIKE '%lesson_json%'
                    """)
                    indexes = cursor.fetchall()
                    if indexes:
                        print(f"\n  Indexes found: {len(indexes)}")
                        for idx_name, idx_def in indexes:
                            print(f"    - {idx_name}")
                    else:
                        print(f"\n  [WARNING] No indexes found (recommended but not critical)")
                    
                    column_exists = True
                else:
                    print("[ERROR] Column does NOT exist in database schema")
                    column_exists = False
                
                cursor.close()
                conn.close()
            else:
                print("[WARNING] Database password not set (SUPABASE_DB_PASSWORD env var)")
                print("  Skipping direct PostgreSQL check")
                
        except ImportError:
            print("[WARNING] psycopg2 not installed - install with: pip install psycopg2-binary")
            print("  Skipping direct PostgreSQL check")
        except Exception as e:
            print(f"[WARNING] Direct connection failed: {e}")
        
        # Method 4: Test update_weekly_plan with lesson_json
        print("\n[Method 4] Testing update_weekly_plan with lesson_json parameter...")
        try:
            plans_result = db.client.table("weekly_plans").select("id").limit(1).execute()
            plans = plans_result.data if plans_result.data else []
            if plans:
                test_plan_id = plans[0]['id']
                test_json = {"test": "data", "metadata": {"test": True}}
                
                print(f"  Testing with plan ID: {test_plan_id}")
                result = db.update_weekly_plan(
                    test_plan_id,
                    lesson_json=test_json
                )
                
                if result:
                    print("[OK] update_weekly_plan() accepts lesson_json parameter successfully!")
                    print("  Method signature is correct")
                else:
                    print("[WARNING] update_weekly_plan() returned False (plan might not exist)")
            else:
                print("[WARNING] No plans found - cannot test update method")
        except TypeError as e:
            if "unexpected keyword argument 'lesson_json'" in str(e):
                print(f"[ERROR] update_weekly_plan() does NOT accept lesson_json parameter!")
                print(f"  Error: {e}")
                print("  This means the method signature is wrong in the code")
            else:
                print(f"[WARNING] TypeError: {e}")
        except Exception as e:
            error_msg = str(e)
            if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                print(f"[ERROR] Column does NOT exist: {e}")
                column_exists = False
            else:
                print(f"[WARNING] Unexpected error during update test: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        if column_exists is True:
            print("[OK] lesson_json column EXISTS in database")
            print("\nIf the error persists, the issue might be:")
            print("  1. The column exists but plans don't have lesson_json data")
            print("  2. There's a caching issue - try generating a new plan")
            print("  3. The frontend is not receiving the data correctly")
        elif column_exists is False:
            print("[ERROR] lesson_json column DOES NOT EXIST in database")
            print("\nACTION REQUIRED:")
            print("  Run the migration SQL in Supabase Dashboard:")
            print("  See: sql/add_lesson_json_column.sql")
            print("  Or run: python tools/run_lesson_json_migration.py")
        else:
            print("[UNKNOWN] Could not definitively determine if column exists")
            print("  Please check manually in Supabase Dashboard:")
            print("  1. Go to Table Editor")
            print("  2. Select 'weekly_plans' table")
            print("  3. Check if 'lesson_json' column is listed")
        
        print("\n" + "=" * 70)
        return column_exists
        
    except Exception as e:
        print(f"\n[ERROR] Failed to check column: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = check_column_exists()
    sys.exit(0 if result is True else 1)

