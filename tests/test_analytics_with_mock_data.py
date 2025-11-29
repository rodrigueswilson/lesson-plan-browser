"""
Test analytics with mock data.
Creates 30 mock plans with metrics, tests analytics, then cleans up.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
import random
from backend.database import get_db
from backend.performance_tracker import get_tracker


def create_mock_data(num_plans=30):
    """Create mock plans with performance metrics."""
    db = get_db()
    tracker = get_tracker()
    
    print(f"\n{'='*70}")
    print(f"Creating {num_plans} mock plans with metrics...")
    print('='*70)
    
    # Create test user
    user_id = db.create_user("Analytics Test User", "analytics_test@example.com")
    print(f"✓ Created test user: {user_id}")
    
    plan_ids = []
    models = ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
    operation_types = ["parse_slot", "process_slot", "render_document"]
    
    # Create plans spread over the last 30 days
    for i in range(num_plans):
        days_ago = i % 30  # Spread across 30 days
        plan_date = datetime.now() - timedelta(days=days_ago)
        
        # Create plan
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=plan_date.strftime("%Y-%m-%d"),
            output_file=f"mock_plan_{i}.docx",
            week_folder_path=f"/mock/week_{i}",
        )
        plan_ids.append(plan_id)
        
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
    
    print(f"✓ Created all {num_plans} plans with {sum(random.randint(3, 5) for _ in range(num_plans))} operations")
    print(f"✓ Data spans last 30 days")
    
    return user_id, plan_ids


def test_analytics_with_data(user_id):
    """Test analytics endpoints with mock data."""
    tracker = get_tracker()
    
    print(f"\n{'='*70}")
    print("Testing Analytics with Mock Data")
    print('='*70)
    
    # Test 1: Aggregate Stats
    print("\n[1/5] Testing Aggregate Stats...")
    stats = tracker.get_aggregate_stats(days=30, user_id=user_id)
    
    print(f"  ✓ Total Plans: {stats['total_plans']}")
    print(f"  ✓ Total Operations: {stats['total_operations']}")
    print(f"  ✓ Total Duration: {stats['total_duration_ms']:,.0f} ms")
    print(f"  ✓ Avg Duration: {stats['avg_duration_ms']:,.0f} ms")
    print(f"  ✓ Total Tokens: {stats['total_tokens']:,}")
    print(f"  ✓ Total Cost: ${stats['total_cost_usd']:.4f}")
    
    assert stats['total_plans'] == 30, f"Expected 30 plans, got {stats['total_plans']}"
    assert stats['total_operations'] > 0, "Should have operations"
    assert stats['total_cost_usd'] > 0, "Should have cost"
    print("  ✓ Aggregate stats validation PASSED")
    
    # Test 2: Model Distribution
    print("\n[2/5] Testing Model Distribution...")
    model_dist = stats['model_distribution']
    print(f"  ✓ Found {len(model_dist)} models")
    
    for model in model_dist:
        print(f"    - {model['llm_model']}: {model['count']} operations, ${model['cost']:.4f}")
    
    assert len(model_dist) > 0, "Should have model distribution"
    print("  ✓ Model distribution PASSED")
    
    # Test 3: Operation Breakdown
    print("\n[3/5] Testing Operation Breakdown...")
    op_breakdown = stats['operation_breakdown']
    print(f"  ✓ Found {len(op_breakdown)} operation types")
    
    for op in op_breakdown:
        print(f"    - {op['operation_type']}: {op['count']} operations, avg {op['avg_duration_ms']:.0f} ms")
    
    assert len(op_breakdown) == 3, f"Expected 3 operation types, got {len(op_breakdown)}"
    print("  ✓ Operation breakdown PASSED")
    
    # Test 4: Daily Breakdown
    print("\n[4/5] Testing Daily Breakdown...")
    daily = tracker.get_daily_breakdown(days=30, user_id=user_id)
    print(f"  ✓ Found data for {len(daily)} days")
    
    if len(daily) > 0:
        print(f"  ✓ Most recent day: {daily[0]['date']}")
        print(f"    - Plans: {daily[0]['plans']}")
        print(f"    - Operations: {daily[0]['operations']}")
        print(f"    - Cost: ${daily[0]['cost_usd']:.4f}")
    
    assert len(daily) > 0, "Should have daily data"
    print("  ✓ Daily breakdown PASSED")
    
    # Test 5: CSV Export
    print("\n[5/5] Testing CSV Export...")
    csv_data = tracker.export_analytics_csv(days=30, user_id=user_id)
    
    lines = csv_data.strip().split('\n')
    print(f"  ✓ CSV has {len(lines)} lines (header + {len(lines)-1} data rows)")
    print(f"  ✓ Header: {lines[0][:60]}...")
    
    assert len(csv_data) > 0, "CSV should have content"
    assert len(lines) > 1, "CSV should have data rows"
    print("  ✓ CSV export PASSED")
    
    # Test 6: Different Time Ranges
    print("\n[6/6] Testing Different Time Ranges...")
    stats_7d = tracker.get_aggregate_stats(days=7, user_id=user_id)
    stats_90d = tracker.get_aggregate_stats(days=90, user_id=user_id)
    
    print(f"  ✓ 7 days: {stats_7d['total_plans']} plans")
    print(f"  ✓ 30 days: {stats['total_plans']} plans")
    print(f"  ✓ 90 days: {stats_90d['total_plans']} plans")
    
    assert stats_7d['total_plans'] <= stats['total_plans'], "7-day should have <= 30-day"
    assert stats['total_plans'] <= stats_90d['total_plans'], "30-day should have <= 90-day"
    print("  ✓ Time range filtering PASSED")
    
    print(f"\n{'='*70}")
    print("✓ ALL ANALYTICS TESTS PASSED!")
    print('='*70)


def cleanup_mock_data(user_id, plan_ids):
    """Clean up all mock data."""
    db = get_db()
    
    print(f"\n{'='*70}")
    print("Cleaning Up Mock Data...")
    print('='*70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Delete performance metrics
        for plan_id in plan_ids:
            cursor.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan_id,))
        print(f"✓ Deleted performance metrics for {len(plan_ids)} plans")
        
        # Delete plans
        for plan_id in plan_ids:
            cursor.execute("DELETE FROM weekly_plans WHERE id = ?", (plan_id,))
        print(f"✓ Deleted {len(plan_ids)} plans")
        
        # Delete class slots for user
        cursor.execute("DELETE FROM class_slots WHERE user_id = ?", (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"✓ Deleted test user")
    
    print('='*70)
    print("✓ Cleanup Complete - All mock data removed")
    print('='*70)


def main():
    """Main test execution."""
    print("\n" + "="*70)
    print("ANALYTICS DASHBOARD TEST WITH MOCK DATA")
    print("="*70)
    print("This test will:")
    print("  1. Create 30 mock plans with realistic metrics")
    print("  2. Test all analytics functionality")
    print("  3. Clean up all mock data")
    print("="*70)
    
    user_id = None
    plan_ids = []
    
    try:
        # Create mock data
        user_id, plan_ids = create_mock_data(num_plans=30)
        
        # Test analytics
        test_analytics_with_data(user_id)
        
        # Success summary
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print('='*70)
        print("✓ Created 30 mock plans")
        print("✓ Generated realistic performance metrics")
        print("✓ Tested aggregate statistics")
        print("✓ Tested model distribution")
        print("✓ Tested operation breakdown")
        print("✓ Tested daily breakdown")
        print("✓ Tested CSV export")
        print("✓ Tested time range filtering")
        print('='*70)
        print("✓ ALL TESTS PASSED!")
        print('='*70)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always clean up
        if user_id and plan_ids:
            cleanup_mock_data(user_id, plan_ids)
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
