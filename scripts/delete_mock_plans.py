import sqlite3
import sys
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    if not db_path.exists():
        print(f"Error: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    args = sys.argv[1:]
    force = "--force" in args
        
    print(f"Scanning {db_path} for Mock plans...")
    
    # query to find IDs
    try:
        cursor.execute("SELECT id, week_of, generated_at FROM weekly_plans WHERE lesson_json LIKE '%Mock Student Goal%'")
        rows = cursor.fetchall()
        
        if not rows:
            print("No Mock plans found.")
            return

        print(f"Found {len(rows)} Mock plans:")
        msg = ""
        ids_to_delete = []
        for r in rows:
            print(f" - ID: {r[0]} | Week: {r[1]} | Generated: {r[2]}")
            ids_to_delete.append(r[0])
            
        if force:
            confirm = 'yes'
        else:
            confirm = input(f"\nType 'yes' to delete these {len(ids_to_delete)} plans: ")

        if confirm.lower() == 'yes':
            for pid in ids_to_delete:
                cursor.execute("DELETE FROM weekly_plans WHERE id=?", (pid,))
                # Also delete associated lesson steps if any
                cursor.execute("DELETE FROM lesson_steps WHERE lesson_plan_id=?", (pid,))
                print(f"Deleted plan {pid}")
            
            conn.commit()
            print("Cleanup complete.")
        else:
            print("Deletion cancelled.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
