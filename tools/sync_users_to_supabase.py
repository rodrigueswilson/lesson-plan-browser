"""
Utility script to seed Supabase user tables with the records stored in the
local SQLite database.

Usage examples:

    # Sync every configured project
    python tools/sync_users_to_supabase.py

    # Only sync Wilson's project (project1)
    python tools/sync_users_to_supabase.py --project project1

    # Preview changes without writing to Supabase
    python tools/sync_users_to_supabase.py --dry-run
"""

from __future__ import annotations

import argparse

from backend.database import get_db
from backend.supabase import sync as supabase_sync


def main():
    parser = argparse.ArgumentParser(description="Sync SQLite users into Supabase.")
    parser.add_argument(
        "--project",
        choices=["project1", "project2", "all"],
        default="all",
        help="Target Supabase project (default: all configured projects).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rows that would be synced without writing to Supabase.",
    )
    args = parser.parse_args()

    sqlite_db = get_db()
    sqlite_users = sqlite_db.list_users()

    print(f"Loaded {len(sqlite_users)} user(s) from SQLite.")

    projects = supabase_sync.get_target_projects(args.project)
    for project in projects:
        supabase_sync.sync_users_to_supabase(
            project, sqlite_users, dry_run=args.dry_run
        )

    print("Sync complete.")


if __name__ == "__main__":
    main()
