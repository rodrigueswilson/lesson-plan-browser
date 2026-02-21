#!/usr/bin/env python3
"""
Clean up duplicate weekly plans in the SQLite database.

For each user and week combination, keeps only the most recent plan
(based on generated_at timestamp) and deletes older versions.
Also removes associated lesson_steps for deleted plans.
"""

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def backup_database(db_path: Path, backup_dir: Path = None) -> Path:
    """Create a timestamped backup of the database."""
    if backup_dir is None:
        backup_dir = db_path.parent / "backups"
    
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_path.stem}_backup_{timestamp}.db"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    return backup_path


def cleanup_duplicate_plans(db_path: str, dry_run: bool = False, skip_backup: bool = False) -> None:
    """Remove duplicate plans, keeping only the most recent per week per user."""
    db_path_obj = Path(db_path)
    
    # Create backup before making changes (unless dry-run or skip-backup)
    if not dry_run and not skip_backup:
        backup_path = backup_database(db_path_obj)
        print(f"  Backup created: {backup_path.name}\n")
    
    conn = sqlite3.connect(db_path)
    try:
        # Find duplicate plans (same user_id and week_of)
        cursor = conn.cursor()
        
        # Get all plans grouped by user_id and week_of
        query = """
            SELECT 
                user_id,
                week_of,
                COUNT(*) as count
            FROM weekly_plans
            GROUP BY user_id, week_of
            HAVING COUNT(*) > 1
            ORDER BY user_id, week_of
        """
        
        duplicates = cursor.execute(query).fetchall()
        
        if not duplicates:
            print("No duplicate plans found. Database is clean!")
            return
        
        print(f"Found {len(duplicates)} week(s) with multiple plans:")
        total_deleted = 0
        
        for user_id, week_of, count in duplicates:
            print(f"\n  User: {user_id[:8]}... | Week: {week_of} | {count} plans")
            
            # Get all plans for this user/week, ordered by generated_at (newest first)
            plans_query = """
                SELECT id, generated_at
                FROM weekly_plans
                WHERE user_id = ? AND week_of = ?
                ORDER BY generated_at DESC
            """
            plans = cursor.execute(plans_query, (user_id, week_of)).fetchall()
            
            if len(plans) <= 1:
                continue
            
            # Keep the first one (most recent), delete the rest
            keep_id = plans[0][0]
            delete_ids = [plan[0] for plan in plans[1:]]
            
            print(f"    Keeping: {keep_id} (generated_at: {plans[0][1]})")
            for plan_id, gen_at in plans[1:]:
                print(f"    Will delete: {plan_id} (generated_at: {gen_at})")
            
            if not dry_run:
                # Delete associated lesson_steps first (foreign key constraint)
                for plan_id in delete_ids:
                    cursor.execute(
                        "DELETE FROM lesson_steps WHERE lesson_plan_id = ?",
                        (plan_id,)
                    )
                
                # Delete the old plans
                placeholders = ",".join("?" * len(delete_ids))
                cursor.execute(
                    f"DELETE FROM weekly_plans WHERE id IN ({placeholders})",
                    delete_ids
                )
                
                deleted_count = cursor.rowcount
                total_deleted += deleted_count
                print(f"    ✓ Deleted {deleted_count} plan(s) and their lesson_steps")
            else:
                total_deleted += len(delete_ids)
                print(f"    [DRY RUN] Would delete {len(delete_ids)} plan(s)")
        
        if not dry_run:
            conn.commit()
            print(f"\n✓ Cleanup complete! Deleted {total_deleted} duplicate plan(s).")
        else:
            print(f"\n[DRY RUN] Would delete {total_deleted} duplicate plan(s).")
            print("Run without --dry-run to actually delete them.")
        
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Clean up duplicate weekly plans, keeping only the most recent per week per user"
    )
    parser.add_argument(
        "--db-path",
        default="data/lesson_planner.db",
        help="Path to the SQLite database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating a backup before cleanup (not recommended)",
    )
    args = parser.parse_args()
    
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    cleanup_duplicate_plans(str(db_path), dry_run=args.dry_run, skip_backup=args.skip_backup)


if __name__ == "__main__":
    main()

