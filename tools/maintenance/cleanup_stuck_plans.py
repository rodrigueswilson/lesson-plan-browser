"""
Cleanup script to remove stuck processing plans from the database.

Removes plans with 'processing' status that are older than 1 hour.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_stuck_plans():
    """Remove stuck processing plans from the database."""
    
    # Database path
    db_path = Path(__file__).parent / "data" / "lesson_planner.db"
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Calculate cutoff time (1 hour ago)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cutoff_time = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    # Find stuck processing plans
    cursor.execute("""
        SELECT id, week_of, generated_at, user_id
        FROM weekly_plans
        WHERE status = 'processing'
        AND generated_at < ?
    """, (cutoff_time,))
    
    stuck_plans = cursor.fetchall()
    
    if not stuck_plans:
        print("No stuck processing plans found.")
        conn.close()
        return
    
    print(f"\nFound {len(stuck_plans)} stuck processing plans:")
    for plan_id, week_of, generated_at, user_id in stuck_plans:
        print(f"  - ID: {plan_id}, Week: {week_of}, Generated: {generated_at}")
    
    # Ask for confirmation
    response = input(f"\nDelete these {len(stuck_plans)} plans? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        # Delete the stuck plans
        cursor.execute("""
            DELETE FROM weekly_plans
            WHERE status = 'processing'
            AND generated_at < ?
        """, (cutoff_time,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"\n✓ Successfully deleted {deleted_count} stuck processing plans.")
    else:
        print("\nCancelled. No plans were deleted.")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Cleanup Stuck Processing Plans")
    print("=" * 60)
    cleanup_stuck_plans()
    print("\nDone!")
