"""
Migration script to export data from SQLite and import to Supabase.

Usage:
    python tools/migrate_to_supabase.py [--sqlite-path PATH] [--dry-run]

This script:
1. Connects to SQLite database
2. Exports all data from users, class_slots, weekly_plans, performance_metrics
3. Imports data to Supabase
4. Validates data integrity
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings
from backend.database import SQLiteDatabase
from backend.supabase_database import SupabaseDatabase
from backend.telemetry import logger


def export_sqlite_data(db: SQLiteDatabase, user_ids: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Export data from SQLite database.
    
    Args:
        db: SQLite database instance
        user_ids: Optional list of user IDs to export. If None, exports all users.
    """
    print("Exporting data from SQLite...")
    
    data = {
        "users": [],
        "class_slots": [],
        "weekly_plans": [],
        "performance_metrics": [],
    }
    
    # Export users
    all_users = db.list_users()
    if user_ids:
        users = [u for u in all_users if u["id"] in user_ids]
        print(f"  Filtering to {len(users)} specified user(s) out of {len(all_users)} total")
    else:
        users = all_users
        print(f"  Found {len(users)} users (exporting all)")
    
    data["users"] = users
    
    if not users:
        print("  No users to export!")
        return data
    
    # Export class slots
    for user in users:
        slots = db.get_user_slots(user["id"])
        data["class_slots"].extend(slots)
    print(f"  Found {len(data['class_slots'])} class slots")
    
    # Export weekly plans
    for user in users:
        plans = db.get_user_plans(user["id"], limit=10000)  # Get all plans
        data["weekly_plans"].extend(plans)
    print(f"  Found {len(data['weekly_plans'])} weekly plans")
    
    # Export performance metrics
    for plan in data["weekly_plans"]:
        metrics = db.get_plan_metrics(plan["id"])
        data["performance_metrics"].extend(metrics)
    print(f"  Found {len(data['performance_metrics'])} performance metrics")
    
    return data


def import_to_supabase(db: SupabaseDatabase, data: Dict[str, List[Dict[str, Any]]], dry_run: bool = False, clear_first: bool = False) -> None:
    """Import data to Supabase.
    
    Args:
        db: Supabase database instance
        data: Data dictionary with users, class_slots, weekly_plans, performance_metrics
        dry_run: If True, only show what would be imported
        clear_first: If True, delete existing data for these users before importing
    """
    if dry_run:
        print("\n[DRY RUN] Would import the following:")
        for table, records in data.items():
            print(f"  {table}: {len(records)} records")
        return
    
    print("\nImporting data to Supabase...")
    
    # Clear existing data if requested
    if clear_first and data["users"]:
        user_ids = [u["id"] for u in data["users"]]
        print(f"  Clearing existing data for {len(user_ids)} user(s)...")
        try:
            # Delete performance metrics first (they reference weekly_plans)
            for user_id in user_ids:
                plans = db.get_user_plans(user_id, limit=10000)
                plan_ids = [p["id"] for p in plans]
                if plan_ids:
                    db.client.table("performance_metrics").delete().in_("plan_id", plan_ids).execute()
            # Delete weekly plans
            db.client.table("weekly_plans").delete().in_("user_id", user_ids).execute()
            # Delete class slots
            db.client.table("class_slots").delete().in_("user_id", user_ids).execute()
            # Delete users
            db.client.table("users").delete().in_("id", user_ids).execute()
            print("  Existing data cleared.")
        except Exception as e:
            print(f"  Warning: Error clearing data (may not exist): {e}")
    
    # Import users (use upsert to handle duplicates)
    print(f"  Importing {len(data['users'])} users...")
    for user in data["users"]:
        try:
            user_data = dict(user)
            db.client.table("users").upsert(user_data).execute()
        except Exception as e:
            print(f"    Error importing user {user.get('id')}: {e}")
    
    # Import class slots (use upsert)
    print(f"  Importing {len(data['class_slots'])} class slots...")
    for slot in data["class_slots"]:
        try:
            slot_data = dict(slot)
            db.client.table("class_slots").upsert(slot_data).execute()
        except Exception as e:
            print(f"    Error importing slot {slot.get('id')}: {e}")
    
    # Import weekly plans
    print(f"  Importing {len(data['weekly_plans'])} weekly plans...")
    for plan in data["weekly_plans"]:
        try:
            plan_data = dict(plan)
            # Convert consolidated from boolean/string to integer (0 or 1)
            if "consolidated" in plan_data:
                consolidated = plan_data["consolidated"]
                if isinstance(consolidated, bool):
                    plan_data["consolidated"] = 1 if consolidated else 0
                elif isinstance(consolidated, str):
                    # Handle string "true"/"false"
                    plan_data["consolidated"] = 1 if consolidated.lower() == "true" else 0
                elif consolidated is None:
                    plan_data["consolidated"] = 0
                # If it's already an integer, leave it as is
            db.client.table("weekly_plans").upsert(plan_data).execute()
        except Exception as e:
            print(f"    Error importing plan {plan.get('id')}: {e}")
    
    # Import performance metrics
    print(f"  Importing {len(data['performance_metrics'])} performance metrics...")
    # Batch insert for better performance
    batch_size = 100
    for i in range(0, len(data["performance_metrics"]), batch_size):
        batch = data["performance_metrics"][i:i + batch_size]
        try:
            metrics_data = [dict(m) for m in batch]
            db.client.table("performance_metrics").insert(metrics_data).execute()
        except Exception as e:
            print(f"    Error importing metrics batch {i//batch_size + 1}: {e}")


def validate_migration(sqlite_db: SQLiteDatabase, supabase_db: SupabaseDatabase, expected_user_ids: Optional[List[str]] = None) -> bool:
    """Validate that migration was successful.
    
    Args:
        sqlite_db: SQLite database instance
        supabase_db: Supabase database instance
        expected_user_ids: Optional list of user IDs that should be migrated
    """
    print("\nValidating migration...")
    
    # Compare counts
    if expected_user_ids:
        sqlite_users = len([u for u in sqlite_db.list_users() if u["id"] in expected_user_ids])
    else:
        sqlite_users = len(sqlite_db.list_users())
    supabase_users = len(supabase_db.list_users())
    
    print(f"  Users: SQLite={sqlite_users}, Supabase={supabase_users}")
    
    if expected_user_ids and sqlite_users != supabase_users:
        print(f"  WARNING: User count mismatch! Expected {sqlite_users} user(s), found {supabase_users}")
        # Don't fail validation if we're migrating specific users
        if len(expected_user_ids) == 1:
            print("  (This is OK if migrating a single user)")
    
    # Validate a sample user
    if expected_user_ids and len(expected_user_ids) > 0:
        # Validate the migrated user(s)
        for user_id in expected_user_ids:
            sqlite_user = sqlite_db.get_user(user_id)
            if sqlite_user:
                supabase_user = supabase_db.get_user(user_id)
                if not supabase_user:
                    print(f"  ERROR: User {sqlite_user.get('name', user_id)} not found in Supabase!")
                    return False
                # Compare key fields
                if sqlite_user.get("name") != supabase_user.get("name"):
                    print(f"  WARNING: User name mismatch for {user_id}")
                    return False
                print(f"  Verified user: {sqlite_user.get('name', user_id)}")
    elif sqlite_users > 0:
        # Fallback: validate first user if no specific IDs provided
        sqlite_user = sqlite_db.list_users()[0]
        supabase_user = supabase_db.get_user(sqlite_user["id"])
        if not supabase_user:
            print(f"  WARNING: User {sqlite_user['id']} not found in Supabase!")
            return False
        if sqlite_user.get("name") != supabase_user.get("name"):
            print(f"  WARNING: User name mismatch for {sqlite_user['id']}")
            return False
    
    print("  Validation passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to Supabase")
    parser.add_argument(
        "--sqlite-path",
        type=str,
        default=None,
        help="Path to SQLite database file (defaults to settings.DATABASE_URL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually importing data",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        action="append",
        help="User ID(s) to migrate. Can be specified multiple times. If not specified, migrates all users.",
    )
    parser.add_argument(
        "--user-name",
        type=str,
        action="append",
        help="User name(s) to migrate (searches by name). Can be specified multiple times.",
    )
    parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Clear existing data for these users before importing (useful for re-migration)",
    )
    
    args = parser.parse_args()
    
    # Check Supabase configuration
    if not settings.USE_SUPABASE or not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("ERROR: Supabase is not configured. Please set USE_SUPABASE=True, SUPABASE_URL, and SUPABASE_KEY")
        sys.exit(1)
    
    # Initialize databases
    print("Initializing databases...")
    sqlite_db = SQLiteDatabase(db_path=args.sqlite_path)
    supabase_db = SupabaseDatabase()
    
    # Determine which users to migrate
    user_ids_to_migrate = None
    if args.user_id:
        user_ids_to_migrate = args.user_id
        print(f"\nMigrating specific user IDs: {user_ids_to_migrate}")
    elif args.user_name:
        # Find user IDs by name
        all_users = sqlite_db.list_users()
        user_ids_to_migrate = []
        for name_search in args.user_name:
            found = [u for u in all_users if name_search.lower() in u.get('name', '').lower()]
            if found:
                user_ids_to_migrate.extend([u['id'] for u in found])
                print(f"\nFound user(s) matching '{name_search}': {[u.get('name') for u in found]}")
            else:
                print(f"\nWARNING: No user found matching '{name_search}'")
        if not user_ids_to_migrate:
            print("\nERROR: No users found to migrate!")
            sys.exit(1)
        print(f"\nMigrating user IDs: {user_ids_to_migrate}")
    
    # Export from SQLite
    data = export_sqlite_data(sqlite_db, user_ids=user_ids_to_migrate)
    
    # Import to Supabase
    import_to_supabase(supabase_db, data, dry_run=args.dry_run, clear_first=args.clear_first)
    
    if not args.dry_run:
        # Validate migration
        if validate_migration(sqlite_db, supabase_db, expected_user_ids=user_ids_to_migrate):
            print("\n[SUCCESS] Migration completed successfully!")
        else:
            print("\n[ERROR] Migration validation failed. Please review the errors above.")
            sys.exit(1)
    else:
        print("\n[SUCCESS] Dry run completed. Use without --dry-run to perform actual migration.")


if __name__ == "__main__":
    main()

