"""
Tests for standardized error handling in supabase_database.py
"""
import pytest
from backend.supabase_database import (
    LessonStepsTableMissingError,
    LessonModeSessionsTableMissingError,
)


class TestSupabaseErrorHandling:
    """Test that error handling is standardized."""

    def test_lesson_steps_table_missing_error_exists(self):
        """Test that LessonStepsTableMissingError exception exists."""
        assert issubclass(LessonStepsTableMissingError, Exception)
        error = LessonStepsTableMissingError("Test message")
        assert str(error) == "Test message"

    def test_lesson_mode_sessions_table_missing_error_exists(self):
        """Test that LessonModeSessionsTableMissingError exception exists."""
        assert issubclass(LessonModeSessionsTableMissingError, Exception)
        error = LessonModeSessionsTableMissingError("Test message")
        assert str(error) == "Test message"

    def test_error_types_are_different(self):
        """Test that the two error types are different."""
        assert LessonStepsTableMissingError != LessonModeSessionsTableMissingError

