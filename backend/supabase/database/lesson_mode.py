"""Supabase lesson mode session operations mixin."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from postgrest.exceptions import APIError

from backend.schema import LessonModeSession
from backend.supabase.query_helpers import (
    hydrate_session_payload,
    normalize_day,
)

from .exceptions import LessonModeSessionsTableMissingError

logger = logging.getLogger(__name__)


class SupabaseLessonModeMixin:
    """Mixin for lesson mode session operations. Expects self.client and type(self) to have _lesson_mode_sessions_table_warned."""

    def create_lesson_mode_session(self, session_data: Dict[str, Any]) -> str:
        """Create a lesson mode session."""
        try:
            payload = session_data.copy()
            if "day_of_week" in payload:
                payload["day_of_week"] = normalize_day(payload["day_of_week"])
            if (
                "adjusted_durations" in payload
                and payload["adjusted_durations"] is None
            ):
                payload.pop("adjusted_durations")

            response = (
                self.client.table("lesson_mode_sessions").insert(payload).execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            raise ValueError("Failed to create session")
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_mode_sessions" in error_msg.lower()
            ):
                cls = type(self)
                if not cls._lesson_mode_sessions_table_warned:
                    logger.warning(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "plan_id": session_data.get("lesson_plan_id"),
                            "details": "lesson_mode_sessions table does not exist, cannot create session. This warning will only appear once.",
                        },
                    )
                    cls._lesson_mode_sessions_table_warned = True
                else:
                    logger.debug(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "plan_id": session_data.get("lesson_plan_id"),
                            "details": "lesson_mode_sessions table does not exist (suppressed repeated warnings)",
                        },
                    )
                raise LessonModeSessionsTableMissingError(
                    "lesson_mode_sessions table does not exist in this Supabase project"
                )
            logger.error("lesson_mode_session_creation_failed", extra={"error": str(e)})
            raise

    def get_lesson_mode_session(self, session_id: str) -> Optional[LessonModeSession]:
        """Get a lesson mode session by ID."""
        try:
            response = (
                self.client.table("lesson_mode_sessions")
                .select("*")
                .eq("id", session_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return LessonModeSession.model_validate(
                    hydrate_session_payload(row)
                )
            return None
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_mode_sessions" in error_msg.lower()
            ):
                cls = type(self)
                if not cls._lesson_mode_sessions_table_warned:
                    logger.warning(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "details": "lesson_mode_sessions table does not exist. This warning will only appear once."
                        },
                    )
                    cls._lesson_mode_sessions_table_warned = True
                else:
                    logger.debug(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "details": "lesson_mode_sessions table does not exist (suppressed repeated warnings)"
                        },
                    )
                return None
            logger.error("lesson_mode_session_fetch_failed", extra={"error": str(e)})
            return None

    def get_active_lesson_mode_session(
        self,
        user_id: str,
        lesson_plan_id: Optional[str] = None,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> Optional[LessonModeSession]:
        """Get the active (not ended) lesson mode session for a user/lesson."""
        try:
            query = (
                self.client.table("lesson_mode_sessions")
                .select("*")
                .eq("user_id", user_id)
                .is_("ended_at", "null")
                .order("last_updated", desc=True)
            )

            if lesson_plan_id:
                query = query.eq("lesson_plan_id", lesson_plan_id)
            if day_of_week:
                normalized_day = normalize_day(day_of_week)
                query = query.eq("day_of_week", normalized_day)
            if slot_number is not None:
                query = query.eq("slot_number", slot_number)

            response = query.limit(1).execute()
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return LessonModeSession.model_validate(
                    hydrate_session_payload(row)
                )
            return None
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_mode_sessions" in error_msg.lower()
            ):
                cls = type(self)
                if not cls._lesson_mode_sessions_table_warned:
                    logger.warning(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "details": "lesson_mode_sessions table does not exist. This warning will only appear once."
                        },
                    )
                    cls._lesson_mode_sessions_table_warned = True
                else:
                    logger.debug(
                        "lesson_mode_sessions_table_missing",
                        extra={
                            "details": "lesson_mode_sessions table does not exist (suppressed repeated warnings)"
                        },
                    )
                return None
            logger.error(
                "active_lesson_mode_session_fetch_failed", extra={"error": str(e)}
            )
            return None

    def update_lesson_mode_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a lesson mode session."""
        try:
            payload = updates.copy()
            if "day_of_week" in payload:
                payload["day_of_week"] = normalize_day(payload["day_of_week"])
            if (
                "adjusted_durations" in payload
                and payload["adjusted_durations"] is None
            ):
                payload.pop("adjusted_durations")

            payload["last_updated"] = datetime.utcnow().isoformat()

            response = (
                self.client.table("lesson_mode_sessions")
                .update(payload)
                .eq("id", session_id)
                .execute()
            )
            return response.data is not None and len(response.data) > 0
        except APIError as e:
            logger.error("lesson_mode_session_update_failed", extra={"error": str(e)})
            return False

    def end_lesson_mode_session(self, session_id: str) -> bool:
        """Mark a lesson mode session as ended."""
        try:
            now = datetime.utcnow().isoformat()
            response = (
                self.client.table("lesson_mode_sessions")
                .update({"ended_at": now, "last_updated": now})
                .eq("id", session_id)
                .execute()
            )
            return response.data is not None and len(response.data) > 0
        except APIError as e:
            logger.error("lesson_mode_session_end_failed", extra={"error": str(e)})
            return False
