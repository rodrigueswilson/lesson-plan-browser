"""Check what operations are tracked in the system."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db

db = get_db()

print("\n=== OPERATIONS IN WORKFLOW ===\n")

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Get distinct operation types
    cursor.execute("SELECT DISTINCT operation_type FROM performance_metrics ORDER BY operation_type")
    operations = [row[0] for row in cursor.fetchall()]
    
    print("Operations tracked:")
    for op in operations:
        print(f"  - {op}")
    
    print("\n=== AVERAGE TIME PER OPERATION ===\n")
    
    # Get average time for each operation
    cursor.execute("""
        SELECT 
            operation_type,
            COUNT(*) as count,
            AVG(duration_ms) as avg_ms,
            MIN(duration_ms) as min_ms,
            MAX(duration_ms) as max_ms
        FROM performance_metrics
        GROUP BY operation_type
        ORDER BY avg_ms DESC
    """)
    
    for row in cursor.fetchall():
        op_type, count, avg_ms, min_ms, max_ms = row
        print(f"{op_type}:")
        print(f"  Count: {count}")
        print(f"  Average: {avg_ms:.0f} ms ({avg_ms/1000:.1f}s)")
        print(f"  Min: {min_ms:.0f} ms")
        print(f"  Max: {max_ms:.0f} ms")
        print()
    
    print("=== TOTAL WORKFLOW TIME ===\n")
    
    # Get total time per plan
    cursor.execute("""
        SELECT 
            plan_id,
            SUM(duration_ms) as total_ms,
            COUNT(*) as num_operations
        FROM performance_metrics
        GROUP BY plan_id
        ORDER BY total_ms DESC
        LIMIT 5
    """)
    
    print("Top 5 slowest plans:")
    for row in cursor.fetchall():
        plan_id, total_ms, num_ops = row
        print(f"  Plan {plan_id[:8]}...: {total_ms:.0f} ms ({total_ms/1000:.1f}s) - {num_ops} operations")
