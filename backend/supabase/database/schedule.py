"""Supabase schedule operations mixin."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import ScheduleEntry

logger = logging.getLogger(__name__)


class SupabaseScheduleMixin:
    """Mixin for schedule entry operations. Expects self.client (Supabase Client)."""

    def create_schedule_entry(self, entry_data: Dict[str, Any]) -> str:
        """Create a new schedule entry."""
        entry_id = f"sched_{uuid.uuid4()}"
        try:
            data = entry_data.copy()
            data["id"] = entry_id
            self.client.table("schedules").insert(data).execute()
            return entry_id
        except APIError as e:
            logger.error("schedule_create_failed", extra={"error": str(e)})
            raise

    def get_user_schedule(
        self,
        user_id: str,
        day_of_week: Optional[str] = None,
        homeroom: Optional[str] = None,
        grade: Optional[str] = None,
    ) -> List[ScheduleEntry]:
        """Get schedule entries for a user."""
        try:
            query = self.client.table("schedules").select("*").eq("user_id", user_id)
            if day_of_week:
                query = query.eq("day_of_week", day_of_week)
            if homeroom:
                query = query.eq("homeroom", homeroom)
            if grade:
                query = query.eq("grade", grade)

            response = query.order("day_of_week").order("start_time").execute()
            return [ScheduleEntry.model_validate(row) for row in response.data]
        except APIError as e:
            logger.error("schedule_fetch_failed", extra={"error": str(e)})
            raise

    def get_current_lesson(self, user_id: str) -> Optional[ScheduleEntry]:
        """Get current lesson based on current time."""
        try:
            now = datetime.now()
            current_day = now.strftime("%A").lower()
            current_time = now.strftime("%H:%M")

            response = (
                self.client.table("schedules")
                .select("*")
                .eq("user_id", user_id)
                .eq("day_of_week", current_day)
                .lte("start_time", current_time)
                .gt("end_time", current_time)
                .eq("is_active", True)
                .execute()
            )

            if response.data:
                return ScheduleEntry.model_validate(response.data[0])
            return None
        except APIError as e:
            logger.error("current_lesson_fetch_failed", extra={"error": str(e)})
            return None

    def update_schedule_entry(
        self, schedule_id: str, updates: Dict[str, Any]
    ) -> bool:
        """Update a schedule entry."""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = (
                self.client.table("schedules")
                .update(updates)
                .eq("id", schedule_id)
                .execute()
            )
            return len(response.data) > 0
        except APIError as e:
            logger.error("schedule_update_failed", extra={"error": str(e)})
            return False

    def delete_schedule_entry(self, schedule_id: str) -> bool:
        """Delete a schedule entry."""
        try:
            response = (
                self.client.table("schedules").delete().eq("id", schedule_id).execute()
            )
            return len(response.data) > 0
        except APIError as e:
            logger.error("schedule_delete_failed", extra={"error": str(e)})
            return False

    def bulk_create_schedule_entries(
        self, entries: List[Dict[str, Any]]
    ) -> tuple[int, List[str]]:
        """Bulk create schedule entries."""
        created_count = 0
        errors = []

        try:
            for entry in entries:
                if "id" not in entry:
                    entry["id"] = f"sched_{uuid.uuid4()}"

            self.client.table("schedules").insert(entries).execute()
            created_count = len(entries)
        except APIError as e:
            errors.append(str(e))

        return created_count, errors

    def clear_user_schedule(self, user_id: str) -> int:
        """Delete all schedule entries for a user."""
        try:
            response = (
                self.client.table("schedules").delete().eq("user_id", user_id).execute()
            )
            return len(response.data or [])
        except APIError as e:
            logger.error(
                "schedule_clear_failed", extra={"user_id": user_id, "error": str(e)}
            )
            raise
