"""Supabase lesson step operations mixin."""

import logging
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import LessonStep
from backend.supabase.query_helpers import (
    hydrate_lesson_step_payload,
    normalize_day,
    prepare_lesson_step_payload,
)

from .exceptions import LessonStepsTableMissingError

logger = logging.getLogger(__name__)


class SupabaseLessonStepsMixin:
    """Mixin for lesson step operations. Expects self.client and type(self) to have _lesson_steps_table_warned."""

    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
        """Create a lesson step."""
        try:
            payload = prepare_lesson_step_payload(step_data)
            self.client.table("lesson_steps").insert(payload).execute()
            return payload.get("id")
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
            ):
                cls = type(self)
                if not cls._lesson_steps_table_warned:
                    logger.warning(
                        "lesson_steps_table_missing_for_create",
                        extra={
                            "plan_id": step_data.get("lesson_plan_id"),
                            "step_name": step_data.get("step_name"),
                            "details": "lesson_steps table does not exist, cannot create step. This warning will only appear once.",
                        },
                    )
                    cls._lesson_steps_table_warned = True
                else:
                    logger.debug(
                        "lesson_steps_table_missing_for_create",
                        extra={
                            "plan_id": step_data.get("lesson_plan_id"),
                            "step_name": step_data.get("step_name"),
                            "details": "lesson_steps table does not exist (suppressed repeated warnings)",
                        },
                    )
                raise LessonStepsTableMissingError(
                    "lesson_steps table does not exist in this Supabase project"
                )
            logger.error("lesson_step_creation_failed", extra={"error": str(e)})
            raise

    def delete_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> int:
        """Delete lesson steps scoped by plan/day/slot."""
        try:
            query = (
                self.client.table("lesson_steps").delete().eq("lesson_plan_id", plan_id)
            )
            normalized_day = normalize_day(day_of_week)
            if normalized_day:
                query = query.eq("day_of_week", normalized_day)
            if slot_number is not None:
                query = query.eq("slot_number", slot_number)
            response = query.execute()
            return len(response.data or [])
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
            ):
                logger.warning(
                    "lesson_steps_table_missing_for_delete",
                    extra={
                        "plan_id": plan_id,
                        "details": "lesson_steps table does not exist, skipping delete",
                    },
                )
                return 0
            logger.error("lesson_steps_delete_failed", extra={"error": str(e)})
            return 0

    def get_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> List[LessonStep]:
        """Get lesson steps."""
        try:
            query = (
                self.client.table("lesson_steps")
                .select("*")
                .eq("lesson_plan_id", plan_id)
            )
            normalized_day = normalize_day(day_of_week)
            if normalized_day:
                query = query.eq("day_of_week", normalized_day)
            if slot_number is not None:
                query = query.eq("slot_number", slot_number)

            response = query.order("step_number").execute()
            return [
                LessonStep.model_validate(hydrate_lesson_step_payload(row))
                for row in response.data
            ]
        except APIError as e:
            error_msg = str(e)
            if (
                "PGRST205" in error_msg
                or "Could not find the table" in error_msg
                or "lesson_steps" in error_msg.lower()
            ):
                cls = type(self)
                if not cls._lesson_steps_table_warned:
                    logger.warning(
                        "lesson_steps_table_missing",
                        extra={
                            "plan_id": plan_id,
                            "error": error_msg,
                            "details": "lesson_steps table does not exist in this Supabase project. Steps may need to be generated first. This warning will only appear once.",
                        },
                    )
                    cls._lesson_steps_table_warned = True
                else:
                    logger.debug(
                        "lesson_steps_table_missing",
                        extra={
                            "plan_id": plan_id,
                            "details": "lesson_steps table does not exist (suppressed repeated warnings)",
                        },
                    )
                return []
            logger.error("lesson_steps_fetch_failed", extra={"error": str(e)})
            raise
