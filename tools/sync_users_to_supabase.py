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
from datetime import datetime
from typing import Dict, Iterable, List

from postgrest.exceptions import APIError

from backend.config import Settings
from backend.database import get_db
from backend.schema import User
from backend.supabase_database import SupabaseDatabase


def isoformat(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def serialize_user(user: User) -> Dict[str, object]:
    """Convert a SQLModel User into a flat dict for Supabase."""
    return {
        "id": user.id,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "base_path_override": user.base_path_override,
        "template_path": user.template_path,
        "signature_image_path": user.signature_image_path,
        "created_at": isoformat(user.created_at),
        "updated_at": isoformat(user.updated_at),
    }


def chunked(items: Iterable[Dict[str, object]], size: int) -> Iterable[List[Dict[str, object]]]:
    """Yield batches of dictionaries to avoid large payloads."""
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def get_target_projects(selected: str) -> List[str]:
    """Resolve which Supabase projects should be updated."""
    settings = Settings()
    available = []
    env_map = {
        "project1": (
            settings.SUPABASE_URL_PROJECT1,
            settings.SUPABASE_SERVICE_ROLE_KEY_PROJECT1 or settings.SUPABASE_KEY_PROJECT1,
        ),
        "project2": (
            settings.SUPABASE_URL_PROJECT2,
            settings.SUPABASE_SERVICE_ROLE_KEY_PROJECT2 or settings.SUPABASE_KEY_PROJECT2,
        ),
    }

    if selected in {"project1", "project2"}:
        url, key = env_map[selected]
        if url and key:
            return [selected]
        raise SystemExit(f"Supabase credentials for {selected} are not configured.")

    # Default: include every project that has credentials configured
    for project, (url, key) in env_map.items():
        if url and key:
            available.append(project)

    if not available:
        raise SystemExit("No Supabase projects are configured. Set SUPABASE_URL_PROJECT* and SUPABASE_SERVICE_ROLE_KEY_PROJECT*.")

    return available


def build_project_settings(project: str) -> Settings:
    project_settings = Settings()
    project_settings.SUPABASE_PROJECT = project
    return project_settings


def sync_project(project: str, users: List[User], dry_run: bool = False) -> None:
    if not users:
        print(f"[{project}] Nothing to sync; SQLite returned zero users.")
        return

    project_settings = build_project_settings(project)
    print(f"[{project}] Connecting to Supabase project '{project_settings.SUPABASE_PROJECT}'")

    if dry_run:
        print(f"[{project}] DRY RUN - no changes will be written.")
        for user in users:
            print(f"  - would sync user {user.id} ({user.name})")
        return

    db = SupabaseDatabase(custom_settings=project_settings)
    payloads = [serialize_user(u) for u in users]
    total_synced = 0

    for batch in chunked(payloads, size=50):
        try:
            db.client.table("users").upsert(batch, on_conflict="id").execute()
            total_synced += len(batch)
        except APIError as exc:
            raise SystemExit(f"[{project}] Supabase upsert failed: {exc.message}") from exc

    print(f"[{project}] Synced {total_synced} users.")


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

    projects = get_target_projects(args.project)
    for project in projects:
        sync_project(project, sqlite_users, dry_run=args.dry_run)

    print("Sync complete.")


if __name__ == "__main__":
    main()

