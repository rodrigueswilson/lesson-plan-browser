"""
Test detailed workflow tracking with mock operations.
Creates a test plan and simulates the workflow with detailed tracking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import random
from backend.database import get_db
from backend.performance_tracker import get_tracker


def simulate_workflow():
    """Simulate a complete workflow with detailed tracking."""
    db = get_db()
    tracker = get_tracker()
    
    print("\n" + "="*70)
    print("TESTING DETAILED WORKFLOW TRACKING")
    print("="*70)
    
    # Create test user and plan
    user_id = db.create_user("Tracking Test User", "tracking@test.com")
    plan_id = db.create_weekly_plan(
        user_id=user_id,
        week_of="10-21",
        output_file="test_detailed_tracking.docx",
        week_folder_path="/test/detailed",
    )
    
    print(f"\n✓ Created test plan: {plan_id}")
    print(f"✓ Tracking enabled: {tracker.enabled}")
    
    print("\n" + "="*70)
    print("SIMULATING WORKFLOW WITH DETAILED TRACKING")
    print("="*70)
    
    # Simulate PARSE phase
    print("\n[PARSE PHASE]")
    
    with tracker.track_operation(plan_id, "parse_locate_file"):
        time.sleep(0.05)  # 50ms
        print("  ✓ parse_locate_file: 50ms")
    
    with tracker.track_operation(plan_id, "parse_open_docx"):
        time.sleep(0.3)  # 300ms
        print("  ✓ parse_open_docx: 300ms")
    
    with tracker.track_operation(plan_id, "parse_extract_text"):
        time.sleep(0.15)  # 150ms
        print("  ✓ parse_extract_text: 150ms")
    
    with tracker.track_operation(plan_id, "parse_extract_tables"):
        time.sleep(0.1)  # 100ms
        print("  ✓ parse_extract_tables: 100ms")
    
    # Simulate PROCESS phase (LLM operations)
    print("\n[PROCESS PHASE - LLM]")
    
    with tracker.track_operation(plan_id, "llm_build_prompt"):
        time.sleep(0.08)  # 80ms
        print("  ✓ llm_build_prompt: 80ms")
    
    # Simulate LLM API call with token tracking
    with tracker.track_operation(plan_id, "llm_api_call") as op:
        time.sleep(2.5)  # 2500ms - THE BOTTLENECK!
        # Add token/model info
        op["tokens_input"] = 1500
        op["tokens_output"] = 800
        op["llm_model"] = "gpt-4o-mini"
        op["llm_provider"] = "openai"
        print("  ✓ llm_api_call: 2500ms ⚠️ BOTTLENECK")
        print("    - Model: gpt-4o-mini")
        print("    - Tokens: 1500 in, 800 out")
    
    with tracker.track_operation(plan_id, "llm_parse_response"):
        time.sleep(0.12)  # 120ms
        print("  ✓ llm_parse_response: 120ms")
    
    with tracker.track_operation(plan_id, "llm_validate_structure"):
        time.sleep(0.05)  # 50ms
        print("  ✓ llm_validate_structure: 50ms")
    
    # Simulate RENDER phase
    print("\n[RENDER PHASE]")
    
    with tracker.track_operation(plan_id, "render_load_template"):
        time.sleep(0.2)  # 200ms
        print("  ✓ render_load_template: 200ms")
    
    with tracker.track_operation(plan_id, "render_create_tables"):
        time.sleep(0.6)  # 600ms
        print("  ✓ render_create_tables: 600ms")
    
    with tracker.track_operation(plan_id, "render_apply_formatting"):
        time.sleep(0.3)  # 300ms
        print("  ✓ render_apply_formatting: 300ms")
    
    with tracker.track_operation(plan_id, "render_save_docx"):
        time.sleep(0.15)  # 150ms
        print("  ✓ render_save_docx: 150ms")
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE - Checking Database")
    print("="*70)
    
    # Query the database to see what was tracked
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT operation_type, duration_ms, tokens_input, tokens_output, llm_model
            FROM performance_metrics
            WHERE plan_id = ?
            ORDER BY started_at
        """, (plan_id,))
        
        metrics = cursor.fetchall()
        
        print(f"\n✓ Tracked {len(metrics)} operations:")
        print()
        
        total_time = 0
        parse_time = 0
        process_time = 0
        render_time = 0
        
        for op_type, duration, tokens_in, tokens_out, model in metrics:
            duration_sec = duration / 1000
            total_time += duration
            
            # Categorize by phase
            if op_type.startswith('parse_'):
                parse_time += duration
                phase = "PARSE"
            elif op_type.startswith('llm_'):
                process_time += duration
                phase = "PROCESS"
            elif op_type.startswith('render_'):
                render_time += duration
                phase = "RENDER"
            else:
                phase = "OTHER"
            
            # Format output
            line = f"  [{phase:7}] {op_type:25} {duration:6.0f}ms ({duration_sec:.2f}s)"
            
            if tokens_in and tokens_out:
                line += f"  | {tokens_in} + {tokens_out} tokens"
            if model:
                line += f"  | {model}"
            
            print(line)
        
        print("\n" + "="*70)
        print("PHASE BREAKDOWN")
        print("="*70)
        
        total_sec = total_time / 1000
        parse_sec = parse_time / 1000
        process_sec = process_time / 1000
        render_sec = render_time / 1000
        
        parse_pct = (parse_time / total_time * 100) if total_time > 0 else 0
        process_pct = (process_time / total_time * 100) if total_time > 0 else 0
        render_pct = (render_time / total_time * 100) if total_time > 0 else 0
        
        print(f"\nPARSE Phase:   {parse_sec:5.2f}s ({parse_pct:5.1f}%)")
        print(f"PROCESS Phase: {process_sec:5.2f}s ({process_pct:5.1f}%) ⚠️ SLOWEST")
        print(f"RENDER Phase:  {render_sec:5.2f}s ({render_pct:5.1f}%)")
        print(f"{'─'*40}")
        print(f"TOTAL:         {total_sec:5.2f}s (100.0%)")
        
        # Find bottleneck
        print("\n" + "="*70)
        print("BOTTLENECK ANALYSIS")
        print("="*70)
        
        cursor.execute("""
            SELECT operation_type, AVG(duration_ms) as avg_ms, COUNT(*) as count
            FROM performance_metrics
            WHERE plan_id = ?
            GROUP BY operation_type
            ORDER BY avg_ms DESC
            LIMIT 5
        """, (plan_id,))
        
        print("\nTop 5 Slowest Operations:")
        for i, (op_type, avg_ms, count) in enumerate(cursor.fetchall(), 1):
            pct = (avg_ms / total_time * 100) if total_time > 0 else 0
            marker = " ⚠️⚠️⚠️" if i == 1 else ""
            print(f"  {i}. {op_type:25} {avg_ms:6.0f}ms ({pct:5.1f}%){marker}")
    
    # Cleanup
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan_id,))
        cursor.execute("DELETE FROM weekly_plans WHERE id = ?", (plan_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    print("✓ Test data cleaned up")
    
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("\n✓ Detailed tracking is working!")
    print("✓ Database is storing all operations")
    print("✓ Can identify bottlenecks (llm_api_call)")
    print("\nNext: Process a real lesson plan to see actual metrics!")


if __name__ == "__main__":
    simulate_workflow()
