"""
Facade for backward compatibility: re-export SupabaseDatabase and exceptions from backend.supabase.

All existing imports (from backend.supabase_database import SupabaseDatabase, etc.) continue to work.
"""

from backend.supabase.client import get_project1_db, get_project2_db
from backend.supabase.database import (
    LessonModeSessionsTableMissingError,
    LessonStepsTableMissingError,
    SupabaseDatabase,
)

__all__ = [
    "SupabaseDatabase",
    "LessonStepsTableMissingError",
    "LessonModeSessionsTableMissingError",
    "get_project1_db",
    "get_project2_db",
]
