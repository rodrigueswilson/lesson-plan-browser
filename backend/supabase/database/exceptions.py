"""Exceptions for Supabase database (missing tables)."""


class LessonStepsTableMissingError(Exception):
    """Raised when lesson_steps table is missing in Supabase."""

    pass


class LessonModeSessionsTableMissingError(Exception):
    """Raised when lesson_mode_sessions table is missing in Supabase."""

    pass
