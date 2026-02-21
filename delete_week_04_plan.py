#!/usr/bin/env python3
"""Delete week 04 lesson plan (01-19-01-23) from the database."""

import sqlite3
import sys
from pathlib import Path

def main():
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        print(f"Error: {db_path} not found")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    args = sys.argv[1:]
    force = "--force" in args
    
    plan_id = "plan_20260118112824"
    week_of = "01-19-01-23"
    
    print(f"Searching for week 04 lesson plan in {db_path}...")
    print("=" * 80)
    
    try:
        # Verify plan exists
        cursor.execute(
            "SELECT id, user_id, week_of, status, generated_at, total_slots FROM weekly_plans WHERE id = ? OR week_of = ?",
            (plan_id, week_of)
        )
        plan = cursor.fetchone()
        
        if not plan:
            print(f"Plan not found (ID: {plan_id}, Week: {week_of})")
            return
        
        print(f"\n[FOUND] Plan Details:")
        print(f"  Plan ID: {plan['id']}")
        print(f"  Week Of: {plan['week_of']}")
        print(f"  Status: {plan['status']}")
        print(f"  User ID: {plan['user_id']}")
        print(f"  Total Slots: {plan['total_slots']}")
        print(f"  Generated At: {plan['generated_at']}")
        
        # Count related records
        cursor.execute("SELECT COUNT(*) as count FROM lesson_steps WHERE lesson_plan_id = ?", (plan['id'],))
        steps_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM performance_metrics WHERE plan_id = ?", (plan['id'],))
        metrics_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (plan['id'],))
        sessions_count = cursor.fetchone()['count']
        
        print(f"\n[RELATED RECORDS]")
        print(f"  lesson_steps: {steps_count} record(s)")
        print(f"  performance_metrics: {metrics_count} record(s)")
        print(f"  lesson_mode_sessions: {sessions_count} record(s)")
        
        total_records = 1 + steps_count + metrics_count + sessions_count
        print(f"\n[TOTAL] {total_records} record(s) will be deleted")
        
        if force:
            confirm = 'yes'
        else:
            confirm = input(f"\nType 'yes' to delete this plan and all related records: ")
        
        if confirm.lower() == 'yes':
            print("\n[DELETING] Starting deletion...")
            
            # Delete in order (following foreign key dependencies)
            # 1. lesson_mode_sessions (no FK constraint, but references plan_id)
            if sessions_count > 0:
                cursor.execute("DELETE FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (plan['id'],))
                print(f"  - Deleted {cursor.rowcount} lesson_mode_sessions record(s)")
            
            # 2. lesson_steps (has FK with CASCADE, but explicit deletion for safety)
            if steps_count > 0:
                cursor.execute("DELETE FROM lesson_steps WHERE lesson_plan_id = ?", (plan['id'],))
                print(f"  - Deleted {cursor.rowcount} lesson_steps record(s)")
            
            # 3. performance_metrics (has FK with CASCADE, but explicit deletion for safety)
            if metrics_count > 0:
                cursor.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan['id'],))
                print(f"  - Deleted {cursor.rowcount} performance_metrics record(s)")
            
            # 4. weekly_plans (main record)
            cursor.execute("DELETE FROM weekly_plans WHERE id = ?", (plan['id'],))
            print(f"  - Deleted {cursor.rowcount} weekly_plans record(s)")
            
            conn.commit()
            print("\n[SUCCESS] Deletion complete!")
            
            # Verify deletion
            cursor.execute("SELECT COUNT(*) as count FROM weekly_plans WHERE id = ?", (plan['id'],))
            remaining = cursor.fetchone()['count']
            
            if remaining == 0:
                print("[VERIFIED] Plan successfully removed from database")
            else:
                print(f"[WARNING] Plan still exists in database ({remaining} record(s))")
        else:
            print("\n[CANCELLED] Deletion cancelled.")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
