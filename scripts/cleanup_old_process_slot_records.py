"""
Cleanup script to remove old 'process_slot' performance metric records.

Since we've replaced the top-level 'process_slot' tracking with detailed
sub-operations (parse_*, llm_*, render_*), the old 'process_slot' records
are no longer needed and clutter the analytics.

This script:
- Deletes all 'process_slot' operations from performance_metrics table
- Works with both SQLite and Supabase
- Provides statistics before/after
- Supports dry-run mode to preview changes
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import Settings
from backend.database import get_db
from backend.telemetry import logger


def get_process_slot_count(db) -> int:
    """Get count of 'process_slot' records."""
    if hasattr(db, 'client'):  # Supabase
        try:
            response = (
                db.client.table("performance_metrics")
                .select("id", count="exact")
                .eq("operation_type", "process_slot")
                .execute()
            )
            return response.count if hasattr(response, 'count') else len(response.data)
        except Exception as e:
            logger.error("count_failed", extra={"error": str(e)})
            return 0
    else:  # SQLite
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM performance_metrics WHERE operation_type = ?",
                    ("process_slot",)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error("count_failed", extra={"error": str(e)})
            return 0


def delete_process_slot_records(db, dry_run: bool = True) -> int:
    """
    Delete all 'process_slot' records from performance_metrics table.
    
    Args:
        db: Database instance
        dry_run: If True, only count records without deleting
        
    Returns:
        Number of records deleted (or would be deleted if dry_run=True)
    """
    if hasattr(db, 'client'):  # Supabase
        try:
            if dry_run:
                # Count records that would be deleted
                response = (
                    db.client.table("performance_metrics")
                    .select("id", count="exact")
                    .eq("operation_type", "process_slot")
                    .execute()
                )
                count = response.count if hasattr(response, 'count') else len(response.data)
                print(f"  [DRY RUN] Would delete {count} 'process_slot' records from Supabase")
                return count
            else:
                # Delete records
                response = (
                    db.client.table("performance_metrics")
                    .delete()
                    .eq("operation_type", "process_slot")
                    .execute()
                )
                # Supabase delete returns the deleted records
                deleted_count = len(response.data) if response.data else 0
                print(f"  Deleted {deleted_count} 'process_slot' records from Supabase")
                return deleted_count
        except Exception as e:
            logger.error("delete_failed", extra={"error": str(e)})
            print(f"  ERROR: Failed to delete records: {e}")
            return 0
    else:  # SQLite
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                if dry_run:
                    # Count records that would be deleted
                    cursor.execute(
                        "SELECT COUNT(*) FROM performance_metrics WHERE operation_type = ?",
                        ("process_slot",)
                    )
                    count = cursor.fetchone()[0]
                    print(f"  [DRY RUN] Would delete {count} 'process_slot' records from SQLite")
                    return count
                else:
                    # Delete records
                    cursor.execute(
                        "DELETE FROM performance_metrics WHERE operation_type = ?",
                        ("process_slot",)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    print(f"  Deleted {deleted_count} 'process_slot' records from SQLite")
                    return deleted_count
        except Exception as e:
            logger.error("delete_failed", extra={"error": str(e)})
            print(f"  ERROR: Failed to delete records: {e}")
            return 0


def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up old 'process_slot' performance metric records"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Actually delete records (required if not using --dry-run)",
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.force:
        print("ERROR: Must specify either --dry-run (to preview) or --force (to delete)")
        print("Usage: python scripts/cleanup_old_process_slot_records.py --dry-run")
        print("   or: python scripts/cleanup_old_process_slot_records.py --force")
        sys.exit(1)
    
    settings = Settings()
    db = get_db()
    
    db_type = "Supabase" if settings.USE_SUPABASE else "SQLite"
    print(f"\n{'='*60}")
    print(f"Cleanup Old 'process_slot' Records")
    print(f"{'='*60}")
    print(f"Database: {db_type}")
    if settings.USE_SUPABASE:
        print(f"Project: {settings.SUPABASE_PROJECT}")
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'DELETE (permanent)'}")
    print(f"{'='*60}\n")
    
    # Get count before deletion
    print("Counting 'process_slot' records...")
    before_count = get_process_slot_count(db)
    print(f"  Found {before_count} 'process_slot' records")
    
    if before_count == 0:
        print("\nNo 'process_slot' records found. Nothing to clean up.")
        return
    
    # Get total metrics count for context
    try:
        if hasattr(db, 'client'):  # Supabase
            total_response = (
                db.client.table("performance_metrics")
                .select("id", count="exact")
                .execute()
            )
            total_count = total_response.count if hasattr(total_response, 'count') else len(total_response.data)
        else:  # SQLite
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM performance_metrics")
                total_count = cursor.fetchone()[0]
        print(f"  Total performance_metrics records: {total_count}")
        print(f"  'process_slot' records: {before_count} ({before_count/total_count*100:.1f}% of total)")
    except Exception as e:
        print(f"  Could not get total count: {e}")
    
    # Delete (or preview deletion)
    print(f"\n{'Previewing deletion...' if args.dry_run else 'Deleting records...'}")
    deleted_count = delete_process_slot_records(db, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No records were deleted")
        print(f"{'='*60}")
        print(f"\nTo actually delete these records, run:")
        print(f"  python scripts/cleanup_old_process_slot_records.py --force")
    else:
        # Verify deletion
        print(f"\nVerifying deletion...")
        after_count = get_process_slot_count(db)
        print(f"  Remaining 'process_slot' records: {after_count}")
        
        if after_count == 0:
            print(f"\n{'='*60}")
            print("CLEANUP COMPLETE")
            print(f"{'='*60}")
            print(f"Successfully deleted {deleted_count} 'process_slot' records")
            print(f"All old 'process_slot' records have been removed.")
        else:
            print(f"\n{'='*60}")
            print("CLEANUP PARTIAL")
            print(f"{'='*60}")
            print(f"Deleted {deleted_count} records, but {after_count} still remain.")
            print(f"This may indicate an issue with the deletion process.")


if __name__ == "__main__":
    main()

