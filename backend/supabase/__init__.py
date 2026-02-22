"""
Supabase package: auth (client creation), query helpers, sync logic, client helpers, and database implementation.

Public API for external callers remains backend.supabase_database (facade).
"""

from backend.supabase import auth
from backend.supabase import client as client_module
from backend.supabase import query_helpers
from backend.supabase import sync as sync_module
from backend.supabase.database import (
    LessonModeSessionsTableMissingError,
    LessonStepsTableMissingError,
    SupabaseDatabase,
)

__all__ = [
    "auth",
    "client_module",
    "query_helpers",
    "sync_module",
    "SupabaseDatabase",
    "LessonStepsTableMissingError",
    "LessonModeSessionsTableMissingError",
]
