"""
Export telemetry metrics to CSV for analysis.
"""

import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.telemetry import export_metrics_to_csv, get_metrics_summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Export telemetry metrics to CSV')
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('metrics') / 'export.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print summary statistics'
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Export metrics
    export_metrics_to_csv(args.output)
    print(f"✓ Metrics exported to {args.output}")
    
    # Print summary if requested
    if args.summary:
        summary = get_metrics_summary()
        print("\n=== Metrics Summary ===")
        print(f"Total Requests: {summary.get('total_requests', 0)}")
        print(f"Successful: {summary.get('successful', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Avg Token Count: {summary.get('avg_token_count', 0):.0f}")
        print(f"Median Duration: {summary.get('median_duration_ms', 0):.0f}ms")
        print(f"Avg Retry Count: {summary.get('avg_retry_count', 0):.2f}")


if __name__ == '__main__':
    main()
