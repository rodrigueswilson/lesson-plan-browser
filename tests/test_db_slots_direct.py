"""
Direct test of get_user_slots() outside of FastAPI context.
This will help determine if the issue is in the database method itself
or in the async/threading context.
"""

import sqlite3
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_direct_connection():
    """Test SQLite connection directly without Database class."""
    print("=" * 60)
    print("TEST 1: Direct SQLite Connection")
    print("=" * 60)
    
    db_path = Path("data/lesson_plans.db")
    print(f"Database path: {db_path.absolute()}")
    print(f"Database exists: {db_path.exists()}")
    print(f"Database size: {db_path.stat().st_size if db_path.exists() else 0} bytes")
    
    try:
        print("\n1. Opening connection with 5-second timeout...")
        conn = sqlite3.connect(db_path, timeout=5.0)
        print("   ✓ Connection opened")
        
        print("\n2. Setting row_factory...")
        conn.row_factory = sqlite3.Row
        print("   ✓ Row factory set")
        
        print("\n3. Executing PRAGMA foreign_keys...")
        conn.execute("PRAGMA foreign_keys = ON")
        print("   ✓ PRAGMA executed")
        
        print("\n4. Creating cursor...")
        cursor = conn.cursor()
        print("   ✓ Cursor created")
        
        print("\n5. Querying class_slots table...")
        cursor.execute("""
            SELECT * FROM class_slots 
            WHERE user_id = ? 
            ORDER BY slot_number
        """, ("29fa9ed7-3174-4999-86fd-40a542c28cff",))
        print("   ✓ Query executed")
        
        print("\n6. Fetching results...")
        rows = cursor.fetchall()
        print(f"   ✓ Got {len(rows)} rows")
        
        print("\n7. Converting to dicts...")
        slots = [dict(row) for row in rows]
        print(f"   ✓ Converted {len(slots)} slots")
        
        print("\n8. Closing connection...")
        conn.close()
        print("   ✓ Connection closed")
        
        print("\n" + "=" * 60)
        print(f"SUCCESS: Retrieved {len(slots)} slots")
        print("=" * 60)
        
        if slots:
            print("\nFirst slot:")
            for key, value in slots[0].items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            conn.close()
        except:
            pass


def test_database_class():
    """Test using the Database class."""
    print("\n\n" + "=" * 60)
    print("TEST 2: Database Class")
    print("=" * 60)
    
    try:
        from backend.database import Database
        
        print("\n1. Creating Database instance...")
        db = Database()
        print("   ✓ Database instance created")
        
        print("\n2. Calling get_user_slots()...")
        print("   (This is where it hangs in the backend)")
        
        # Add a timeout using threading
        import threading
        result = [None]
        error = [None]
        
        def call_get_user_slots():
            try:
                result[0] = db.get_user_slots("29fa9ed7-3174-4999-86fd-40a542c28cff")
            except Exception as e:
                error[0] = e
        
        thread = threading.Thread(target=call_get_user_slots)
        thread.daemon = True
        thread.start()
        thread.join(timeout=10.0)
        
        if thread.is_alive():
            print("   ❌ TIMEOUT: get_user_slots() hung for 10 seconds!")
            print("   This confirms the hang is in the Database class itself.")
            return False
        
        if error[0]:
            raise error[0]
        
        slots = result[0]
        print(f"   ✓ Got {len(slots)} slots")
        
        print("\n" + "=" * 60)
        print(f"SUCCESS: Database class works correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_locks():
    """Check for database lock files."""
    print("\n\n" + "=" * 60)
    print("TEST 3: Database Lock Files")
    print("=" * 60)
    
    data_dir = Path("data")
    lock_files = list(data_dir.glob("*.db-wal")) + list(data_dir.glob("*.db-shm"))
    
    if lock_files:
        print("\n⚠️  WARNING: Found lock files:")
        for f in lock_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
        print("\nThese may indicate a previous crash left the database locked.")
        print("Consider deleting them if no other processes are using the database.")
    else:
        print("\n✓ No lock files found (.db-wal, .db-shm)")
    
    return len(lock_files) == 0


if __name__ == "__main__":
    print("SQLite Database Diagnostic Tool")
    print("Testing get_user_slots() hang issue\n")
    
    # Run tests
    test1_passed = test_direct_connection()
    test2_passed = test_database_class()
    test3_passed = check_database_locks()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Direct SQLite): {'✓ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Database Class): {'✓ PASS' if test2_passed else '❌ FAIL'}")
    print(f"Test 3 (No Lock Files): {'✓ PASS' if test3_passed else '❌ FAIL'}")
    
    if test1_passed and not test2_passed:
        print("\n🔍 DIAGNOSIS: The Database class has an issue.")
        print("   The SQL query works, but something in the class is hanging.")
    elif not test1_passed:
        print("\n🔍 DIAGNOSIS: The database file itself is locked or corrupted.")
        print("   Consider killing Python processes and deleting lock files.")
    else:
        print("\n✓ All tests passed! The issue may be specific to FastAPI context.")
