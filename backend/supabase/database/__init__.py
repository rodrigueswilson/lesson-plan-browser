"""
Supabase database package: mixins by domain and main SupabaseDatabase class.

Public API: SupabaseDatabase, LessonStepsTableMissingError, LessonModeSessionsTableMissingError.
"""

import logging
from contextlib import contextmanager
from typing import Any

from supabase import Client

from backend.config import settings
from backend.database_interface import DatabaseInterface
from backend.supabase.auth import create_supabase_client, verify_schema

from .exceptions import (
    LessonModeSessionsTableMissingError,
    LessonStepsTableMissingError,
)
from .lesson_mode import SupabaseLessonModeMixin
from .lesson_steps import SupabaseLessonStepsMixin
from .metrics import SupabaseMetricsMixin
from .plans import SupabasePlansMixin
from .schedule import SupabaseScheduleMixin
from .slots import SupabaseSlotsMixin
from .users import SupabaseUsersMixin

logger = logging.getLogger(__name__)


class SupabaseDatabase(
    SupabaseUsersMixin,
    SupabaseSlotsMixin,
    SupabasePlansMixin,
    SupabaseMetricsMixin,
    SupabaseScheduleMixin,
    SupabaseLessonStepsMixin,
    SupabaseLessonModeMixin,
    DatabaseInterface,
):
    """Supabase PostgreSQL database manager for user profiles and class slots."""

    _lesson_steps_table_warned = False
    _lesson_mode_sessions_table_warned = False

    def __init__(self, custom_settings: Any = None):
        """Initialize Supabase connection."""
        active_settings = custom_settings if custom_settings is not None else settings
        self.client: Client = create_supabase_client(active_settings)
        verify_schema(self.client)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        try:
            yield self.client
        except Exception as e:
            logger.error("supabase_connection_error", extra={"error": str(e)})
            raise

    def init_db(self):
        """Initialize database schema."""
        verify_schema(self.client)


__all__ = [
    "SupabaseDatabase",
    "LessonStepsTableMissingError",
    "LessonModeSessionsTableMissingError",
]
