"""
Simple demo of performance tracking system.
Shows tracking in action without complex mocking.

Usage:
    python test_tracking_simple_demo.py
"""

import time
from pathlib import Path

from backend.database import Database
from backend.performance_tracker import PerformanceTracker


def demo_tracking():
    """Demonstrate performance tracking with mock data."""
    print()
    print("=" * 70)
    print("Performance Tracking System - Interactive Demo")
    print("=" * 70)
    print()
    
    # Create database
    db_path = Path("data/demo_tracking.db")
    db_path.parent.mkdir(exist_ok=True)
    
    db = Database(str(db_path))
    print(f"✓ Database: {db_path}")
    
    # Create test user
    user_id = db.create_user("Demo Teacher", "demo@example.com")
    print(f"✓ User created: Demo Teacher")
    
    # Create weekly plan
    plan_id = db.create_weekly_plan(
        user_id=user_id,
        week_of="10/6-10/10",
        output_file="demo_plan.docx",
        week_folder_path="demo/week",
    )
    print(f"✓ Plan created: {plan_id[:8]}...")
    print()
    
    # Create tracker (need to patch get_db to use our instance)
    import backend.performance_tracker
    original_get_db = backend.performance_tracker.get_db
    backend.performance_tracker.get_db = lambda: db
    
    tracker = PerformanceTracker(enabled=True)
    print("=" * 70)
    print("Simulating LLM Processing with Tracking")
    print("=" * 70)
    print()
    
    # Simulate processing 3 slots
    subjects = ["Math", "Science", "English"]
    
    for i, subject in enumerate(subjects, 1):
        print(f"Processing Slot {i}: {subject}")
        print("-" * 70)
        
        # Start tracking
        op_id = tracker.start_operation(
            plan_id=plan_id,
            operation_type="process_slot",
            metadata={
                "slot_number": i,
                "subject": subject,
                "grade": str(5 + i)
            }
        )
        
        # Simulate LLM processing time
        processing_time = 0.5 + (i * 0.2)  # Vary by slot
        print(f"  Calling LLM API... ", end="", flush=True)
        time.sleep(processing_time)
        print("✓")
        
        # Simulate token usage (realistic numbers)
        base_tokens = 1200
        tokens_input = base_tokens + (i * 150)
        tokens_output = 700 + (i * 100)
        
        print(f"  Tokens: {tokens_input:,} input + {tokens_output:,} output = {tokens_input + tokens_output:,} total")
        
        # End tracking with results
        tracker.end_operation(op_id, result={
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai"
        })
        
        # Get the metric we just created
        metrics = tracker.get_plan_metrics(plan_id)
        latest_metric = metrics[-1]
        
        print(f"  Duration: {latest_metric['duration_ms']:.2f}ms")
        print(f"  Cost: ${latest_metric['cost_usd']:.4f}")
        print()
    
    # Get summary
    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    
    summary = tracker.get_plan_summary(plan_id)
    
    print(f"Total Operations: {summary['operation_count']}")
    print(f"Total Duration: {summary['total_duration_ms']:.2f}ms ({summary['total_duration_ms']/1000:.2f}s)")
    print(f"Average Duration: {summary['avg_duration_ms']:.2f}ms per operation")
    print()
    print(f"Total Tokens: {summary['total_tokens']:,}")
    print(f"  - Input: {summary['total_tokens_input']:,}")
    print(f"  - Output: {summary['total_tokens_output']:,}")
    print()
    print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
    print()
    
    # Update plan summary
    print("=" * 70)
    print("Updating Database")
    print("=" * 70)
    
    tracker.update_plan_summary(plan_id)
    print("✓ Plan summary updated in weekly_plans table")
    
    # Show database record
    plans = db.get_user_plans(user_id)
    plan = plans[0]
    
    print()
    print("Database Record (weekly_plans):")
    print(f"  Status: {plan['status']}")
    print(f"  Total Tokens: {plan['total_tokens']:,}")
    print(f"  Total Cost: ${plan['total_cost_usd']:.4f}")
    print(f"  Processing Time: {plan['processing_time_ms']:.2f}ms")
    print(f"  Model: {plan['llm_model']}")
    print()
    
    # Export to CSV
    print("=" * 70)
    print("Exporting Metrics")
    print("=" * 70)
    
    # Use timestamped filename to avoid conflicts
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = Path(f"metrics/demo_export_{timestamp}.csv")
    csv_path.parent.mkdir(exist_ok=True)
    
    try:
        exported = tracker.export_to_csv(plan_id, str(csv_path))
    except PermissionError:
        print("⚠️  Previous CSV file is open in Excel!")
        print("   Using timestamped filename instead...")
        csv_path = Path(f"metrics/demo_export_{timestamp}_alt.csv")
        exported = tracker.export_to_csv(plan_id, str(csv_path))
    
    if exported:
        print(f"✓ Exported to: {csv_path}")
        print(f"✓ File size: {csv_path.stat().st_size} bytes")
        print()
        
        # Show preview
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print("CSV Preview (first 4 lines):")
        print("-" * 70)
        for line in lines[:4]:
            # Show first 70 chars
            display = line.rstrip()
            if len(display) > 70:
                display = display[:67] + "..."
            print(display)
        
        if len(lines) > 4:
            print(f"... ({len(lines) - 4} more rows)")
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("What was demonstrated:")
    print("  ✓ Performance tracking for 3 slots")
    print("  ✓ Token usage capture (mock LLM)")
    print("  ✓ Cost calculations (accurate pricing)")
    print("  ✓ Duration measurements")
    print("  ✓ Database storage")
    print("  ✓ Summary aggregation")
    print("  ✓ CSV export for analysis")
    print()
    print(f"Database: {db_path}")
    print(f"CSV Export: {csv_path}")
    print()
    print("You can:")
    print("  - Open the CSV in Excel for analysis")
    print("  - Query the database for custom reports")
    print("  - Use this data for research")
    print()


if __name__ == "__main__":
    try:
        demo_tracking()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
