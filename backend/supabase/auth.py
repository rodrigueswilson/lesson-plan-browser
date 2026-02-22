"""Supabase client creation and schema verification."""

import logging
from typing import Any, Optional

from postgrest.exceptions import APIError
from supabase import Client, create_client

logger = logging.getLogger(__name__)


def create_supabase_client(settings: Any) -> Client:
    """
    Create a Supabase client from settings.

    Args:
        settings: Object with supabase_url and supabase_key (e.g. backend.config.Settings).

    Returns:
        Supabase Client instance.

    Raises:
        ValueError: If URL or key are missing.
    """
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_key

    if not supabase_url or not supabase_key:
        project = getattr(settings, "SUPABASE_PROJECT", "project1")
        raise ValueError(
            f"Supabase credentials must be set for {project}. "
            f"Set SUPABASE_URL_{project.upper()} and SUPABASE_KEY_{project.upper()}"
        )

    return create_client(supabase_url, supabase_key)


def verify_schema(client: Client) -> None:
    """
    Verify that required tables exist by querying the users table.

    Logs a warning if the users table is missing; logs an error for other API errors.
    Does not raise so the app can start when offline/misconfigured.
    """
    try:
        client.table("users").select("id").limit(1).execute()
        logger.info("supabase_schema_verified")
    except APIError as e:
        if e.code == "42P01":
            logger.warning(
                "supabase_schema_missing",
                extra={
                    "error": str(e),
                    "message": "Tables do not exist. Please run schema migration in Supabase dashboard.",
                },
            )
        else:
            logger.error("supabase_schema_check_failed", extra={"error": str(e)})
