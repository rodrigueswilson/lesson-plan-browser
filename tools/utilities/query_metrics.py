"""
Query performance metrics from the database.
Shows accumulated data across all runs.

Usage:
    python query_metrics.py
"""

from pathlib import Path
from backend.database import Database


def query_all_metrics():
    """Query and display all performance metrics."""
    
    db_path = Path("data/demo_tracking.db")
    
    if not db_path.exists():
        print("❌ Database not found. Run test_tracking_simple_demo.py first.")
        return
    
    db = Database(str(db_path))
    
    print()
    print("=" * 80)
    print("Performance Metrics Database Query")
    print("=" * 80)
    print(f"Database: {db_path}")
    print()
    
    # Get all users
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM performance_metrics")
        total_metrics = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weekly_plans")
        total_plans = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print("📊 Database Overview")
        print("-" * 80)
        print(f"Total Users: {total_users}")
        print(f"Total Plans: {total_plans}")
        print(f"Total Metrics: {total_metrics}")
        print()
        
        # Get all plans with their metrics
        print("=" * 80)
        print("Weekly Plans Summary")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                id,
                week_of,
                status,
                generated_at,
                total_tokens,
                total_cost_usd,
                processing_time_ms,
                llm_model
            FROM weekly_plans
            ORDER BY generated_at DESC
        """)
        
        plans = cursor.fetchall()
        
        if not plans:
            print("No plans found.")
            return
        
        for i, plan in enumerate(plans, 1):
            plan_id, week_of, status, generated_at, tokens, cost, time_ms, model = plan
            
            print(f"\n📋 Plan {i}: {plan_id[:8]}...")
            print(f"   Week: {week_of}")
            print(f"   Status: {status}")
            print(f"   Generated: {generated_at}")
            print(f"   Model: {model}")
            print(f"   Tokens: {tokens:,}" if tokens else "   Tokens: N/A")
            print(f"   Cost: ${cost:.4f}" if cost else "   Cost: N/A")
            print(f"   Duration: {time_ms:.2f}ms" if time_ms else "   Duration: N/A")
            
            # Get metrics for this plan
            cursor.execute("""
                SELECT 
                    slot_number,
                    operation_type,
                    duration_ms,
                    tokens_input,
                    tokens_output,
                    tokens_total,
                    cost_usd,
                    error_message
                FROM performance_metrics
                WHERE plan_id = ?
                ORDER BY started_at
            """, (plan_id,))
            
            metrics = cursor.fetchall()
            
            if metrics:
                print(f"   Operations: {len(metrics)}")
                print()
                print("   " + "-" * 76)
                print(f"   {'Slot':<6} {'Type':<15} {'Duration':<12} {'Tokens':<12} {'Cost':<10} {'Status'}")
                print("   " + "-" * 76)
                
                for metric in metrics:
                    slot, op_type, duration, tok_in, tok_out, tok_total, cost, error = metric
                    
                    slot_str = str(slot) if slot else "N/A"
                    duration_str = f"{duration:.2f}ms" if duration else "N/A"
                    tokens_str = f"{tok_total:,}" if tok_total else "N/A"
                    cost_str = f"${cost:.4f}" if cost else "N/A"
                    status_str = "❌ Error" if error else "✓"
                    
                    print(f"   {slot_str:<6} {op_type:<15} {duration_str:<12} {tokens_str:<12} {cost_str:<10} {status_str}")
                    
                    if error:
                        print(f"      Error: {error[:60]}...")
        
        # Overall statistics
        print()
        print("=" * 80)
        print("Overall Statistics (All Runs)")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_operations,
                SUM(duration_ms) as total_duration,
                SUM(tokens_input) as total_input,
                SUM(tokens_output) as total_output,
                SUM(tokens_total) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration,
                MIN(started_at) as first_run,
                MAX(started_at) as last_run
            FROM performance_metrics
        """)
        
        stats = cursor.fetchone()
        
        if stats and stats[0] > 0:
            (total_ops, total_dur, total_in, total_out, total_tok, 
             total_cost, avg_dur, first_run, last_run) = stats
            
            print(f"Total Operations: {total_ops}")
            print(f"First Run: {first_run}")
            print(f"Last Run: {last_run}")
            print()
            print(f"Total Duration: {total_dur:.2f}ms ({total_dur/1000:.2f}s)")
            print(f"Average Duration: {avg_dur:.2f}ms per operation")
            print()
            print(f"Total Tokens: {int(total_tok):,}")
            print(f"  - Input: {int(total_in):,}")
            print(f"  - Output: {int(total_out):,}")
            print()
            print(f"Total Cost: ${total_cost:.4f}")
            print(f"Average Cost: ${total_cost/total_ops:.4f} per operation")
        
        # Statistics by model
        print()
        print("=" * 80)
        print("Statistics by Model")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                llm_model,
                COUNT(*) as operations,
                SUM(tokens_total) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration
            FROM performance_metrics
            WHERE llm_model IS NOT NULL
            GROUP BY llm_model
            ORDER BY operations DESC
        """)
        
        model_stats = cursor.fetchall()
        
        if model_stats:
            print(f"{'Model':<30} {'Ops':<8} {'Tokens':<15} {'Cost':<12} {'Avg Duration'}")
            print("-" * 80)
            
            for model, ops, tokens, cost, avg_dur in model_stats:
                print(f"{model:<30} {ops:<8} {int(tokens):>14,} ${cost:>10.4f} {avg_dur:>10.2f}ms")
        
        # Statistics by operation type
        print()
        print("=" * 80)
        print("Statistics by Operation Type")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                operation_type,
                COUNT(*) as operations,
                SUM(tokens_total) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration
            FROM performance_metrics
            GROUP BY operation_type
            ORDER BY operations DESC
        """)
        
        op_stats = cursor.fetchall()
        
        if op_stats:
            print(f"{'Operation':<20} {'Count':<8} {'Tokens':<15} {'Cost':<12} {'Avg Duration'}")
            print("-" * 80)
            
            for op_type, ops, tokens, cost, avg_dur in op_stats:
                print(f"{op_type:<20} {ops:<8} {int(tokens):>14,} ${cost:>10.4f} {avg_dur:>10.2f}ms")
        
        # Error summary
        print()
        print("=" * 80)
        print("Error Summary")
        print("=" * 80)
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM performance_metrics 
            WHERE error_message IS NOT NULL
        """)
        
        error_count = cursor.fetchone()[0]
        
        if error_count > 0:
            print(f"⚠️  {error_count} operations with errors")
            
            cursor.execute("""
                SELECT 
                    operation_type,
                    error_message,
                    started_at
                FROM performance_metrics
                WHERE error_message IS NOT NULL
                ORDER BY started_at DESC
                LIMIT 5
            """)
            
            errors = cursor.fetchall()
            
            print("\nRecent Errors:")
            for op_type, error, timestamp in errors:
                print(f"  - {timestamp}: {op_type}")
                print(f"    {error[:70]}...")
        else:
            print("✓ No errors recorded")
    
    print()
    print("=" * 80)
    print()


def query_latest_plan():
    """Show detailed metrics for the most recent plan."""
    
    db_path = Path("data/demo_tracking.db")
    
    if not db_path.exists():
        print("❌ Database not found.")
        return
    
    db = Database(str(db_path))
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get latest plan
        cursor.execute("""
            SELECT id, week_of, generated_at
            FROM weekly_plans
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        
        plan = cursor.fetchone()
        
        if not plan:
            print("No plans found.")
            return
        
        plan_id, week_of, generated_at = plan
        
        print()
        print("=" * 80)
        print(f"Latest Plan Details: {plan_id[:8]}...")
        print("=" * 80)
        print(f"Week: {week_of}")
        print(f"Generated: {generated_at}")
        print()
        
        # Get all metrics
        cursor.execute("""
            SELECT *
            FROM performance_metrics
            WHERE plan_id = ?
            ORDER BY started_at
        """, (plan_id,))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        
        print(f"Total Operations: {len(metrics)}")
        print()
        
        for i, metric in enumerate(metrics, 1):
            print(f"Operation {i}:")
            print(f"  ID: {metric['id'][:8]}...")
            print(f"  Type: {metric['operation_type']}")
            print(f"  Slot: {metric['slot_number']}")
            print(f"  Started: {metric['started_at']}")
            print(f"  Duration: {metric['duration_ms']:.2f}ms")
            print(f"  Tokens: {metric['tokens_total']:,} ({metric['tokens_input']:,} in + {metric['tokens_output']:,} out)")
            print(f"  Cost: ${metric['cost_usd']:.4f}")
            print(f"  Model: {metric['llm_model']}")
            print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--latest":
        query_latest_plan()
    else:
        query_all_metrics()
