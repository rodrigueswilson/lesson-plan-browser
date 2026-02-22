"""Supabase weekly plan CRUD mixin."""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import WeeklyPlan
from backend.services.objectives_utils import normalize_objectives_in_lesson

logger = logging.getLogger(__name__)


class SupabasePlansMixin:
    """Mixin for weekly plan operations. Expects self.client (Supabase Client)."""

    def create_weekly_plan(
        self,
        user_id: str,
        week_of: str,
        output_file: str,
        week_folder_path: str,
        consolidated: bool = False,
        total_slots: int = 1,
    ) -> str:
        """Create a new weekly plan record."""
        plan_id = str(uuid.uuid4())
        try:
            consolidated_int = int(1 if consolidated else 0)
            total_slots_int = int(total_slots) if total_slots is not None else 1

            self.client.table("weekly_plans").insert(
                {
                    "id": plan_id,
                    "user_id": user_id,
                    "week_of": week_of,
                    "output_file": output_file,
                    "week_folder_path": week_folder_path,
                    "consolidated": consolidated_int,
                    "total_slots": total_slots_int,
                    "status": "pending",
                }
            ).execute()
            logger.info(
                "weekly_plan_created", extra={"plan_id": plan_id, "user_id": user_id}
            )
            return plan_id
        except APIError as e:
            logger.error(
                "weekly_plan_creation_failed",
                extra={"error": str(e), "plan_id": plan_id},
            )
            raise

    def get_weekly_plan(self, plan_id: str) -> Optional[WeeklyPlan]:
        """Get a weekly plan by ID."""
        try:
            response = (
                self.client.table("weekly_plans")
                .select("*")
                .eq("id", plan_id)
                .execute()
            )
            if response.data:
                row = response.data[0]
                if "lesson_json" in row and isinstance(row["lesson_json"], str):
                    try:
                        row["lesson_json"] = json.loads(row["lesson_json"])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"Failed to parse lesson_json for plan {plan_id}"
                        )
                        row["lesson_json"] = None
                return WeeklyPlan.model_validate(row)
            return None
        except APIError as e:
            logger.error(
                "weekly_plan_fetch_failed", extra={"error": str(e), "plan_id": plan_id}
            )
            raise

    def get_user_plans(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[WeeklyPlan]:
        """Get weekly plans for a user."""
        from backend.config import settings

        limit = limit or settings.DEFAULT_PLAN_LIMIT
        try:
            response = (
                self.client.table("weekly_plans")
                .select("*")
                .eq("user_id", user_id)
                .order("generated_at", desc=True)
                .limit(limit)
                .execute()
            )
            plans = []
            for row in response.data:
                if "lesson_json" in row and isinstance(row["lesson_json"], str):
                    try:
                        row["lesson_json"] = json.loads(row["lesson_json"])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"Failed to parse lesson_json for plan {row.get('id', 'unknown')}"
                        )
                        row["lesson_json"] = None
                plans.append(WeeklyPlan.model_validate(row))
            return plans
        except APIError as e:
            logger.error(
                "user_plans_fetch_failed",
                extra={"error": str(e), "user_id": user_id},
            )
            raise

    def update_weekly_plan(
        self,
        plan_id: str,
        status: Optional[str] = None,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        lesson_json: Optional[Dict[str, Any]] = None,
        total_slots: Optional[int] = None,
    ) -> bool:
        """Update weekly plan status."""
        updates: Dict[str, Any] = {}
        if status is not None:
            updates["status"] = status
        if output_file is not None:
            updates["output_file"] = output_file
        if error_message is not None:
            updates["error_message"] = error_message
        if lesson_json is not None:
            normalize_objectives_in_lesson(lesson_json)
            updates["lesson_json"] = lesson_json
        if total_slots is not None:
            updates["total_slots"] = int(total_slots)

        if not updates:
            return False

        try:
            response = (
                self.client.table("weekly_plans")
                .update(updates)
                .eq("id", plan_id)
                .execute()
            )
            updated = len(response.data) > 0
            return updated
        except APIError as e:
            logger.error(
                "weekly_plan_update_failed",
                extra={"error": str(e), "plan_id": plan_id},
            )
            raise
