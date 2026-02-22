"""Project-specific Supabase database instances (get_project1_db, get_project2_db)."""

from backend.config import Settings
from backend.supabase.database import SupabaseDatabase


def get_project1_db() -> SupabaseDatabase:
    """Return a SupabaseDatabase instance configured for project1."""
    settings = Settings()
    settings.SUPABASE_PROJECT = "project1"
    return SupabaseDatabase(custom_settings=settings)


def get_project2_db() -> SupabaseDatabase:
    """Return a SupabaseDatabase instance configured for project2."""
    settings = Settings()
    settings.SUPABASE_PROJECT = "project2"
    return SupabaseDatabase(custom_settings=settings)
