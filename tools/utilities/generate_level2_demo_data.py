"""
Generate demo data with Level 2 detailed operation names.
Creates realistic data showing all 19 operations from detailed tracking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
import random
from backend.database import get_db
from backend.performance_tracker import get_tracker


def generate_level2_demo_data(num_plans=30):
    """Generate demo plans with Level 2 detailed operations."""
    db = get_db()
    
    print(f"\n{'='*70}")
    print(f"GENERATING LEVEL 2 DEMO DATA")
    print('='*70)
    print(f"Creating {num_plans} demo plans with detailed operations...")
    print('='*70)
    
    # Create demo user
    user_id = db.create_user("Demo User (Level 2 Tracking)", "level2@demo.test")
    print(f"\n✓ Created demo user: {user_id}")
    
    # Create class slots
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
    
    # Level 2 operations with realistic timings
    operations = [
        # PARSE operations
        ("parse_locate_file", 50, 100, None, None, 0),
        ("parse_open_docx", 300, 600, None, None, 0),
        ("parse_extract_text", 100, 200, None, None, 0),
        ("parse_extract_metadata", 30, 80, None, None, 0),
        ("parse_list_subjects", 20, 60, None, None, 0),
        
        # PROCESS operations (LLM)
        ("llm_build_prompt", 80, 150, None, None, 0),
        ("llm_api_call", 2000, 4000, "gpt-4o-mini", "openai", 0.0015),  # THE BOTTLENECK
        ("llm_parse_response", 100, 200, None, None, 0),
        ("llm_validate_structure", 40, 80, None, None, 0),
        
        # RENDER operations
        ("render_load_template", 150, 300, None, None, 0),
        ("render_fill_metadata", 30, 80, None, None, 0),
        ("render_fill_days", 400, 800, None, None, 0),
        ("render_normalize_tables", 150, 300, None, None, 0),
        ("render_save_docx", 100, 200, None, None, 0),
    ]
    
    plan_ids = []
    
    # Create plans spread over the last 30 days
    for i in range(num_plans):
        days_ago = i % 30
        plan_date = datetime.now() - timedelta(days=days_ago)
        week_of = plan_date.strftime("%m-%d")
        
        # Create plan
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=week_of,
            output_file=f"level2_demo_week_{week_of}.docx",
            week_folder_path=f"/demo/level2/week_{week_of}",
            consolidated=True,
            total_slots=3,
        )
        plan_ids.append(plan_id)
        db.update_weekly_plan(plan_id, status="completed")
        
        # Add all Level 2 operations for this plan
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for op_name, min_ms, max_ms, model, provider, base_cost in operations:
                duration = random.randint(min_ms, max_ms)
                
                # For LLM operations, add token info
                if op_name == "llm_api_call":
                    tokens_in = random.randint(1000, 2000)
                    tokens_out = random.randint(500, 1200)
                    tokens_total = tokens_in + tokens_out
                    # Calculate realistic cost
                    cost = (tokens_in * 0.00000015 + tokens_out * 0.0000006)
                else:
                    tokens_in = 0
                    tokens_out = 0
                    tokens_total = 0
                    cost = 0.0
                
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
                        op_name,
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
    
    print(f"✓ Created all {num_plans} plans with Level 2 operations")
    
    # Get summary stats
    tracker = get_tracker()
    stats = tracker.get_aggregate_stats(days=30, user_id=user_id)
    
    print(f"\n{'='*70}")
    print("LEVEL 2 DEMO DATA SUMMARY")
    print('='*70)
    print(f"User ID: {user_id}")
    print(f"User Name: Demo User (Level 2 Tracking)")
    print(f"Total Plans: {stats['total_plans']}")
    print(f"Total Operations: {stats['total_operations']}")
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"Total Cost: ${stats['total_cost_usd']:.4f}")
    print(f"Data Span: Last 30 days")
    print(f"\nOperations per plan: {len(operations)}")
    print('='*70)
    
    # Save user ID
    with open("demo_data_user_id.txt", "w") as f:
        f.write(user_id)
    
    print(f"\n{'='*70}")
    print("HOW TO VIEW IN THE APP")
    print('='*70)
    print("1. Refresh the Analytics Dashboard in the app")
    print("2. You should now see:")
    print("   - Color-coded bars (blue/orange/green)")
    print("   - Detailed operations table with 14 operations")
    print("   - Phase summary cards")
    print("   - llm_api_call as the biggest bottleneck")
    print()
    print("3. When done, run cleanup:")
    print("   python cleanup_demo_data.py")
    print('='*70)
    
    return user_id


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LEVEL 2 DEMO DATA GENERATOR")
    print("="*70)
    print()
    print("This will create demo data with detailed Level 2 operations:")
    print("  - 5 PARSE operations")
    print("  - 4 PROCESS operations (including llm_api_call)")
    print("  - 5 RENDER operations")
    print("  - 30 plans spanning 30 days")
    print("="*70)
    
    try:
        user_id = generate_level2_demo_data(num_plans=30)
        
        print(f"\n{'='*70}")
        print("✓ LEVEL 2 DEMO DATA GENERATION COMPLETE!")
        print('='*70)
        print("Refresh the Analytics Dashboard to see:")
        print("  - 14 detailed operations")
        print("  - Color-coded by phase")
        print("  - llm_api_call as the bottleneck")
        print('='*70)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
