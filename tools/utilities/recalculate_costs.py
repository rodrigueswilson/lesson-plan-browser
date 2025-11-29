"""
Recalculate costs for existing performance metrics with updated pricing.
"""

from backend.database import get_db
from backend.model_pricing import calculate_cost

def recalculate_all_costs():
    """Recalculate costs for all performance metrics."""
    db = get_db()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all metrics with token data
        cursor.execute("""
            SELECT id, llm_model, tokens_input, tokens_output, cost_usd
            FROM performance_metrics
            WHERE llm_model IS NOT NULL
            AND tokens_total > 0
        """)
        
        metrics = cursor.fetchall()
        
        print(f"Found {len(metrics)} metrics to recalculate")
        
        updated = 0
        for metric in metrics:
            metric_id, model, tokens_in, tokens_out, old_cost = metric
            
            # Calculate new cost
            new_cost = calculate_cost(model, tokens_in or 0, tokens_out or 0)
            
            if new_cost != old_cost:
                # Update the record
                cursor.execute("""
                    UPDATE performance_metrics
                    SET cost_usd = ?
                    WHERE id = ?
                """, (new_cost, metric_id))
                
                updated += 1
                print(f"  Updated metric {metric_id}: {model} - ${old_cost:.4f} -> ${new_cost:.4f}")
        
        conn.commit()
        
        print(f"\n✓ Updated {updated} metrics")
        
        # Show summary
        cursor.execute("""
            SELECT 
                llm_model,
                COUNT(*) as count,
                SUM(tokens_input) as total_input,
                SUM(tokens_output) as total_output,
                SUM(cost_usd) as total_cost
            FROM performance_metrics
            WHERE llm_model IS NOT NULL
            GROUP BY llm_model
        """)
        
        print("\nCost Summary by Model:")
        for row in cursor.fetchall():
            model, count, total_in, total_out, total_cost = row
            print(f"  {model}: {count} calls, {total_in:,} in / {total_out:,} out tokens, ${total_cost:.4f}")


if __name__ == "__main__":
    print("="*70)
    print("RECALCULATING COSTS WITH UPDATED PRICING")
    print("="*70)
    
    recalculate_all_costs()
    
    print("\n" + "="*70)
    print("✓ COMPLETE - Refresh the Analytics Dashboard to see updated costs")
    print("="*70)
