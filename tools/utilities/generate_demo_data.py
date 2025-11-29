"""
Generate demo data for testing the analytics dashboard in the app.
This creates realistic data that persists so you can view it in the UI.
Run cleanup_demo_data.py when you're done to remove it.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
import random
from backend.database import get_db
from backend.performance_tracker import get_tracker


def generate_demo_data(num_plans=30):
    """Generate demo plans with performance metrics."""
    db = get_db()
    
    print(f"\n{'='*70}")
    print(f"GENERATING DEMO DATA FOR ANALYTICS DASHBOARD")
    print('='*70)
    print(f"Creating {num_plans} demo plans with realistic metrics...")
    print('='*70)
    
    # Create demo user
    user_id = db.create_user("Demo User (Analytics Test)", "demo@analytics.test")
    print(f"\n✓ Created demo user: {user_id}")
    print(f"  Name: Demo User (Analytics Test)")
    
    # Create some class slots for the demo user
    slot_configs = [
        {"subject": "Math", "grade": "5th", "homeroom": "Room 101"},
        {"subject": "Science", "grade": "5th", "homeroom": "Room 102"},
        {"subject": "ELA", "grade": "4th", "homeroom": "Room 103"},
    ]
    
    for i, config in enumerate(slot_configs, 1):
        db.create_class_slot(
            user_id=user_id,
            slot_number=i,
            subject=config["subject"],
            grade=config["grade"],
            homeroom=config["homeroom"],
        )
    
    print(f"✓ Created {len(slot_configs)} class slots")
    
    plan_ids = []
    models = [
        "gpt-4o-mini",
        "gpt-4o", 
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022"
    ]
    operation_types = ["parse_slot", "process_slot", "render_document"]
    
    # Create plans spread over the last 30 days
    for i in range(num_plans):
        days_ago = i % 30  # Spread across 30 days
        plan_date = datetime.now() - timedelta(days=days_ago)
        week_of = plan_date.strftime("%m-%d")
        
        # Create plan
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=week_of,
            output_file=f"demo_plan_week_{week_of}.docx",
            week_folder_path=f"/demo/week_{week_of}",
            consolidated=True,
            total_slots=3,
        )
        plan_ids.append(plan_id)
        
        # Update plan status to completed
        db.update_weekly_plan(plan_id, status="completed")
        
        # Add 3-5 operations per plan
        num_operations = random.randint(3, 5)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for j in range(num_operations):
                op_type = random.choice(operation_types)
                
                # Generate realistic metrics based on operation type
                if op_type == "parse_slot":
                    duration = random.randint(800, 2000)
                    tokens_in = 0
                    tokens_out = 0
                    model = None
                    provider = None
                    cost = 0.0
                elif op_type == "process_slot":
                    duration = random.randint(2000, 5000)
                    tokens_in = random.randint(500, 2000)
                    tokens_out = random.randint(200, 1000)
                    model = random.choice(models)
                    provider = "openai" if "gpt" in model else "anthropic"
                    # Realistic cost calculation
                    if "gpt-4o-mini" in model:
                        cost = (tokens_in * 0.00000015 + tokens_out * 0.0000006)
                    elif "gpt-4o" in model:
                        cost = (tokens_in * 0.0000025 + tokens_out * 0.00001)
                    elif "haiku" in model:
                        cost = (tokens_in * 0.00000025 + tokens_out * 0.00000125)
                    else:  # sonnet
                        cost = (tokens_in * 0.000003 + tokens_out * 0.000015)
                else:  # render_document
                    duration = random.randint(1500, 3500)
                    tokens_in = 0
                    tokens_out = 0
                    model = None
                    provider = None
                    cost = 0.0
                
                tokens_total = tokens_in + tokens_out
                
                # Insert metric
                cursor.execute(
                    """
                    INSERT INTO performance_metrics 
                    (plan_id, operation_type, duration_ms, tokens_input, tokens_output, 
                     tokens_total, llm_model, llm_provider, cost_usd, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_id,
                        op_type,
                        duration,
                        tokens_in,
                        tokens_out,
                        tokens_total,
                        model,
                        provider,
                        cost,
                        plan_date.isoformat(),
                        plan_date.isoformat(),
                    ),
                )
        
        if (i + 1) % 10 == 0:
            print(f"✓ Created {i + 1}/{num_plans} plans...")
    
    print(f"✓ Created all {num_plans} plans")
    
    # Get summary stats
    tracker = get_tracker()
    stats = tracker.get_aggregate_stats(days=30, user_id=user_id)
    
    print(f"\n{'='*70}")
    print("DEMO DATA SUMMARY")
    print('='*70)
    print(f"User ID: {user_id}")
    print(f"User Name: Demo User (Analytics Test)")
    print(f"Total Plans: {stats['total_plans']}")
    print(f"Total Operations: {stats['total_operations']}")
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"Total Cost: ${stats['total_cost_usd']:.4f}")
    print(f"Data Span: Last 30 days")
    print('='*70)
    
    # Save user ID to file for cleanup
    with open("demo_data_user_id.txt", "w") as f:
        f.write(user_id)
    
    print(f"\n{'='*70}")
    print("HOW TO VIEW IN THE APP")
    print('='*70)
    print("1. Start the app:")
    print("   cd frontend")
    print("   npm run tauri dev")
    print()
    print("2. In the app:")
    print("   - Select 'Demo User (Analytics Test)' from the dropdown")
    print("   - Scroll down and expand 'Plan History' to see the plans")
    print("   - Expand 'Analytics Dashboard' to see the charts and metrics")
    print()
    print("3. When done, run cleanup:")
    print("   python cleanup_demo_data.py")
    print('='*70)
    
    return user_id


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("DEMO DATA GENERATOR FOR ANALYTICS DASHBOARD")
    print("="*70)
    print()
    print("This will create:")
    print("  - 1 demo user")
    print("  - 3 class slots")
    print("  - 30 completed plans with metrics")
    print("  - Realistic performance data spanning 30 days")
    print()
    print("The data will persist so you can view it in the app.")
    print("Run 'python cleanup_demo_data.py' when done to remove it.")
    print("="*70)
    
    try:
        user_id = generate_demo_data(num_plans=30)
        
        print(f"\n{'='*70}")
        print("✓ DEMO DATA GENERATION COMPLETE!")
        print('='*70)
        print(f"User ID saved to: demo_data_user_id.txt")
        print()
        print("Next steps:")
        print("  1. Start the app and select 'Demo User (Analytics Test)'")
        print("  2. View the analytics dashboard")
        print("  3. Run 'python cleanup_demo_data.py' when done")
        print('='*70)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
