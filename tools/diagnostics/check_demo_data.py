"""
Check if demo data exists in the database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db
from backend.performance_tracker import get_tracker


def check_demo_data():
    """Check demo data in database."""
    db = get_db()
    
    print(f"\n{'='*70}")
    print("CHECKING DEMO DATA IN DATABASE")
    print('='*70)
    
    # Check for demo user
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        
        print(f"\nTotal Users: {len(users)}")
        for user in users:
            print(f"  - {user[1]} ({user[2]})")
            print(f"    ID: {user[0]}")
        
        # Check for demo user specifically
        cursor.execute("SELECT id FROM users WHERE name LIKE '%Demo%'")
        demo_user = cursor.fetchone()
        
        if not demo_user:
            print("\n✗ No demo user found!")
            print("  Run: python generate_demo_data.py")
            return
        
        demo_user_id = demo_user[0]
        print(f"\n✓ Found demo user: {demo_user_id}")
        
        # Check plans
        cursor.execute("SELECT COUNT(*) FROM weekly_plans WHERE user_id = ?", (demo_user_id,))
        plan_count = cursor.fetchone()[0]
        print(f"✓ Plans for demo user: {plan_count}")
        
        # Check metrics
        cursor.execute("""
            SELECT COUNT(*) FROM performance_metrics pm
            JOIN weekly_plans wp ON pm.plan_id = wp.id
            WHERE wp.user_id = ?
        """, (demo_user_id,))
        metric_count = cursor.fetchone()[0]
        print(f"✓ Metrics for demo user: {metric_count}")
    
    # Test analytics
    print(f"\n{'='*70}")
    print("TESTING ANALYTICS QUERIES")
    print('='*70)
    
    tracker = get_tracker()
    
    # Test without user filter
    print("\n[1] Analytics WITHOUT user filter (all users):")
    stats_all = tracker.get_aggregate_stats(days=30)
    print(f"  Total Plans: {stats_all['total_plans']}")
    print(f"  Total Operations: {stats_all['total_operations']}")
    print(f"  Total Cost: ${stats_all['total_cost_usd']:.4f}" if stats_all['total_cost_usd'] else "  Total Cost: $0.0000")
    
    # Test with demo user filter
    print(f"\n[2] Analytics WITH demo user filter:")
    stats_demo = tracker.get_aggregate_stats(days=30, user_id=demo_user_id)
    print(f"  Total Plans: {stats_demo['total_plans']}")
    print(f"  Total Operations: {stats_demo['total_operations']}")
    print(f"  Total Cost: ${stats_demo['total_cost_usd']:.4f}" if stats_demo['total_cost_usd'] else "  Total Cost: $0.0000")
    
    print(f"\n{'='*70}")
    print("DIAGNOSIS")
    print('='*70)
    
    if stats_all['total_plans'] == 0:
        print("✗ No data in database at all")
        print("  Solution: Run 'python generate_demo_data.py'")
    elif stats_demo['total_plans'] == 0:
        print("✗ Data exists but not for demo user")
        print("  Solution: Check user ID in frontend")
    else:
        print("✓ Data exists and queries work!")
        print(f"\n  Demo User ID: {demo_user_id}")
        print(f"  Plans: {stats_demo['total_plans']}")
        print(f"  Operations: {stats_demo['total_operations']}")
        print("\n  In the app:")
        print("  1. Make sure 'Demo User (Analytics Test)' is selected")
        print("  2. The Analytics component should use currentUser.id")
        print("  3. Check browser console for errors")


if __name__ == "__main__":
    check_demo_data()
