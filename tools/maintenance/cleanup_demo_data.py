"""
Cleanup demo data created by generate_demo_data.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db


def cleanup_demo_data():
    """Remove all demo data."""
    db = get_db()
    
    # Read user ID from file
    try:
        with open("demo_data_user_id.txt", "r") as f:
            user_id = f.read().strip()
    except FileNotFoundError:
        print("✗ Error: demo_data_user_id.txt not found")
        print("  Demo data may have already been cleaned up.")
        return False
    
    print(f"\n{'='*70}")
    print("CLEANING UP DEMO DATA")
    print('='*70)
    print(f"User ID: {user_id}")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get plan IDs for this user
        cursor.execute("SELECT id FROM weekly_plans WHERE user_id = ?", (user_id,))
        plan_ids = [row[0] for row in cursor.fetchall()]
        
        if not plan_ids:
            print("✗ No plans found for this user")
        else:
            # Delete performance metrics
            for plan_id in plan_ids:
                cursor.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan_id,))
            print(f"✓ Deleted performance metrics for {len(plan_ids)} plans")
            
            # Delete plans
            cursor.execute("DELETE FROM weekly_plans WHERE user_id = ?", (user_id,))
            print(f"✓ Deleted {len(plan_ids)} plans")
        
        # Delete class slots
        cursor.execute("DELETE FROM class_slots WHERE user_id = ?", (user_id,))
        print(f"✓ Deleted class slots")
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"✓ Deleted demo user")
    
    # Remove the user ID file
    Path("demo_data_user_id.txt").unlink()
    print(f"✓ Removed demo_data_user_id.txt")
    
    print('='*70)
    print("✓ CLEANUP COMPLETE - All demo data removed")
    print('='*70)
    
    return True


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("DEMO DATA CLEANUP")
    print("="*70)
    print()
    print("This will remove all demo data created by generate_demo_data.py")
    print("="*70)
    
    try:
        success = cleanup_demo_data()
        
        if success:
            print("\n✓ Demo data has been removed from the database")
            print("  You can now generate new demo data if needed")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
