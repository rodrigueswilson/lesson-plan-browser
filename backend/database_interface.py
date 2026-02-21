"""
Database interface abstraction for multiple database backends.
Defines the common interface that all database implementations must follow.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

from backend.schema import (
    ClassSlot,
    LessonModeSession,
    LessonStep,
    ScheduleEntry,
    User,
    WeeklyPlan,
)


class DatabaseInterface(ABC):
    """Abstract base class for database implementations."""

    # Core lifecycle ------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        pass

    @abstractmethod
    def init_db(self):
        """Initialize database schema if it does not exist."""
        pass

    # User CRUD -----------------------------------------------------------------------
    @abstractmethod
    def create_user(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a new user and return its ID."""
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """Fetch a user by ID."""
        pass

    @abstractmethod
    def get_user_by_name(self, name: str) -> Optional[User]:
        """Fetch a user by legacy full name."""
        pass

    @abstractmethod
    def list_users(self) -> List[User]:
        """List all users."""
        pass

    @abstractmethod
    def update_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> bool:
        """Update user attributes."""
        pass

    @abstractmethod
    def update_user_base_path(self, user_id: str, base_path: str) -> bool:
        """Update a user's base path override."""
        pass

    @abstractmethod
    def update_user_template_paths(
        self,
        user_id: str,
        template_path: Optional[str] = None,
        signature_image_path: Optional[str] = None,
    ) -> bool:
        """Update template/signature paths for a user."""
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and all dependent data."""
        pass

    # Class slot operations -----------------------------------------------------------
    @abstractmethod
    def create_class_slot(
        self,
        user_id: str,
        slot_number: int,
        subject: str,
        grade: str,
        homeroom: Optional[str] = None,
        proficiency_levels: Optional[str] = None,
        primary_teacher_file: Optional[str] = None,
        primary_teacher_first_name: Optional[str] = None,
        primary_teacher_last_name: Optional[str] = None,
    ) -> str:
        """Create a class slot configuration."""
        pass

    @abstractmethod
    def get_user_slots(self, user_id: str) -> List[ClassSlot]:
        """Return all slots for a user."""
        pass

    @abstractmethod
    def get_slot(self, slot_id: str) -> Optional[ClassSlot]:
        """Fetch a single slot by ID."""
        pass

    @abstractmethod
    def update_class_slot(self, slot_id: str, **kwargs) -> bool:
        """Update slot attributes."""
        pass

    @abstractmethod
    def delete_class_slot(self, slot_id: str) -> bool:
        """Delete a slot."""
        pass

    @abstractmethod
    def delete_user_slots(self, user_id: str) -> int:
        """Delete all slots for a user."""
        pass

    # Weekly plan operations ----------------------------------------------------------
    @abstractmethod
    def create_weekly_plan(
        self,
        user_id: str,
        week_of: str,
        output_file: str,
        week_folder_path: str,
        consolidated: bool = False,
        total_slots: int = 1,
    ) -> str:
        """Create a weekly plan record."""
        pass

    @abstractmethod
    def get_weekly_plan(self, plan_id: str) -> Optional[WeeklyPlan]:
        """Fetch a weekly plan."""
        pass

    @abstractmethod
    def get_user_plans(
        self,
        user_id: str,
        limit: Optional[int] = None,
    ) -> List[WeeklyPlan]:
        """List plans for a user."""
        pass

    @abstractmethod
    def update_weekly_plan(
        self,
        plan_id: str,
        status: Optional[str] = None,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        lesson_json: Optional[Dict[str, Any]] = None,
        total_slots: Optional[int] = None,
    ) -> bool:
        """Update plan state."""
        pass

    # Metrics & analytics -------------------------------------------------------------
    @abstractmethod
    def save_performance_metric(
        self,
        operation_id: str,
        plan_id: str,
        operation_type: str,
        started_at: Any,
        completed_at: Any,
        duration_ms: float,
        tokens_input: int,
        tokens_output: int,
        tokens_total: int,
        llm_provider: str,
        llm_model: str,
        cost_usd: float,
        error_message: Optional[str],
        slot_number: Optional[int] = None,
        day_number: Optional[int] = None,
    ) -> None:
        """Persist an LLM performance metric."""
        pass

    @abstractmethod
    def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
        """Return metrics for a plan."""
        pass

    @abstractmethod
    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """Return aggregate metrics for a plan."""
        pass

    @abstractmethod
    def update_plan_summary(
        self,
        plan_id: str,
        processing_time_ms: Optional[float],
        total_tokens: Optional[int],
        total_cost_usd: Optional[float],
        llm_model: Optional[str],
    ) -> bool:
        """Update cached summary fields on a plan."""
        pass

    @abstractmethod
    def get_aggregate_stats(
        self,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return aggregate usage stats."""
        pass

    @abstractmethod
    def get_daily_breakdown(
        self,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return per-day usage stats."""
        pass

    @abstractmethod
    def get_session_breakdown(
        self,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return per-session stats."""
        pass

    # Schedule operations -------------------------------------------------------------
    @abstractmethod
    def create_schedule_entry(self, entry_data: Dict[str, Any]) -> str:
        """Create a schedule entry."""
        pass

    @abstractmethod
    def get_user_schedule(
        self,
        user_id: str,
        day_of_week: Optional[str] = None,
        homeroom: Optional[str] = None,
        grade: Optional[str] = None,
    ) -> List[ScheduleEntry]:
        """List schedule entries for a user."""
        pass

    @abstractmethod
    def get_current_lesson(self, user_id: str) -> Optional[ScheduleEntry]:
        """Return the active lesson for a user if one exists."""
        pass

    @abstractmethod
    def update_schedule_entry(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a schedule entry."""
        pass

    @abstractmethod
    def delete_schedule_entry(self, schedule_id: str) -> bool:
        """Delete a schedule entry."""
        pass

    @abstractmethod
    def bulk_create_schedule_entries(
        self,
        entries: List[Dict[str, Any]],
    ) -> Tuple[int, List[str]]:
        """Bulk insert schedule entries."""
        pass

    @abstractmethod
    def clear_user_schedule(self, user_id: str) -> int:
        """Remove all schedule entries for a user."""
        pass

    # Lesson step operations ----------------------------------------------------------
    @abstractmethod
    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
        """Create a lesson step row."""
        pass

    @abstractmethod
    def delete_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> int:
        """Delete lesson steps scoped by plan/day/slot."""
        pass

    @abstractmethod
    def get_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> List[LessonStep]:
        """Fetch lesson steps."""
        pass

    # Lesson Mode Session operations -------------------------------------------
    @abstractmethod
    def create_lesson_mode_session(self, session_data: Dict[str, Any]) -> str:
        """Create a lesson mode session."""
        pass

    @abstractmethod
    def get_lesson_mode_session(self, session_id: str) -> Optional["LessonModeSession"]:
        """Get a lesson mode session by ID."""
        pass

    @abstractmethod
    def get_active_lesson_mode_session(
        self,
        user_id: str,
        lesson_plan_id: Optional[str] = None,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> Optional["LessonModeSession"]:
        """Get the active (not ended) lesson mode session for a user/lesson."""
        pass

    @abstractmethod
    def update_lesson_mode_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a lesson mode session."""
        pass

    @abstractmethod
    def end_lesson_mode_session(self, session_id: str) -> bool:
        """Mark a lesson mode session as ended."""
        pass

