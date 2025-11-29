"""
Display summary of telemetry metrics.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.telemetry import get_metrics_summary


def main():
    """Display metrics summary."""
    summary = get_metrics_summary()
    
    if not summary:
        print("No metrics available")
        return
    
    print("=" * 50)
    print("JSON Pipeline Metrics Summary")
    print("=" * 50)
    print()
    
    print(f"📊 Total Requests:     {summary.get('total_requests', 0):,}")
    print(f"✅ Successful:         {summary.get('successful', 0):,}")
    print(f"📈 Success Rate:       {summary.get('success_rate', 0):.1f}%")
    print()
    
    print(f"🎯 Avg Token Count:    {summary.get('avg_token_count', 0):.0f}")
    print(f"⏱️  Median Duration:    {summary.get('median_duration_ms', 0):.0f}ms")
    print(f"🔄 Avg Retry Count:    {summary.get('avg_retry_count', 0):.2f}")
    print()
    
    # Health indicators
    success_rate = summary.get('success_rate', 0)
    avg_retries = summary.get('avg_retry_count', 0)
    
    print("🏥 Health Indicators:")
    
    if success_rate >= 95:
        print("   ✓ Success rate: HEALTHY")
    elif success_rate >= 90:
        print("   ⚠ Success rate: WARNING")
    else:
        print("   ✗ Success rate: CRITICAL")
    
    if avg_retries < 1.5:
        print("   ✓ Retry count: HEALTHY")
    elif avg_retries < 2.0:
        print("   ⚠ Retry count: WARNING")
    else:
        print("   ✗ Retry count: CRITICAL")
    
    print()
    print("=" * 50)


if __name__ == '__main__':
    main()
