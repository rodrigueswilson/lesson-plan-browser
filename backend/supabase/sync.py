"""Reusable sync logic: serialize users and push to Supabase in chunks."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List

from postgrest.exceptions import APIError

from backend.schema import User


def _isoformat(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def serialize_user(user: User) -> Dict[str, object]:
    """Convert a SQLModel User into a flat dict for Supabase upsert."""
    return {
        "id": user.id,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "base_path_override": user.base_path_override,
        "template_path": user.template_path,
        "signature_image_path": user.signature_image_path,
        "created_at": _isoformat(user.created_at),
        "updated_at": _isoformat(user.updated_at),
    }


def chunked(
    items: Iterable[Dict[str, object]], size: int
) -> Iterable[List[Dict[str, object]]]:
    """Yield batches of dictionaries to avoid large payloads."""
    batch: List[Dict[str, object]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def get_target_projects(selected: str) -> List[str]:
    """
    Resolve which Supabase projects should be updated.

    Args:
        selected: One of "project1", "project2", or "all".

    Returns:
        List of project names to sync.

    Raises:
        SystemExit: If selected project has no credentials or no projects configured.
    """
    from backend.config import Settings

    settings = Settings()
    available: List[str] = []
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

    for project, (url, key) in env_map.items():
        if url and key:
            available.append(project)

    if not available:
        raise SystemExit(
            "No Supabase projects are configured. Set SUPABASE_URL_PROJECT* and SUPABASE_SERVICE_ROLE_KEY_PROJECT*."
        )

    return available


def build_project_settings(project: str):
    """Build Settings instance with SUPABASE_PROJECT set."""
    from backend.config import Settings

    project_settings = Settings()
    project_settings.SUPABASE_PROJECT = project
    return project_settings


def sync_users_to_supabase(
    project: str,
    users: List[User],
    dry_run: bool = False,
    *,
    _print=print,
    _batch_size: int = 50,
) -> None:
    """
    Sync a list of users from SQLite shape to Supabase for the given project.

    Args:
        project: Project name ("project1" or "project2").
        users: List of User instances to sync.
        dry_run: If True, only report what would be synced; do not write.
        _print: Print function (default print); override for tests.
        _batch_size: Upsert batch size (default 50).

    Raises:
        SystemExit: On Supabase upsert failure.
    """
    from backend.supabase_database import SupabaseDatabase

    if not users:
        _print(f"[{project}] Nothing to sync; SQLite returned zero users.")
        return

    project_settings = build_project_settings(project)
    _print(f"[{project}] Connecting to Supabase project '{project_settings.SUPABASE_PROJECT}'")

    if dry_run:
        _print(f"[{project}] DRY RUN - no changes will be written.")
        for user in users:
            _print(f"  - would sync user {user.id} ({user.name})")
        return

    db = SupabaseDatabase(custom_settings=project_settings)
    payloads = [serialize_user(u) for u in users]
    total_synced = 0

    for batch in chunked(payloads, size=_batch_size):
        try:
            db.client.table("users").upsert(batch, on_conflict="id").execute()
            total_synced += len(batch)
        except APIError as exc:
            raise SystemExit(f"[{project}] Supabase upsert failed: {exc.message}") from exc

    _print(f"[{project}] Synced {total_synced} users.")
