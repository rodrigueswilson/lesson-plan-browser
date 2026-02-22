"""Supabase class slot CRUD mixin."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import ClassSlot

logger = logging.getLogger(__name__)


class SupabaseSlotsMixin:
    """Mixin for class slot operations. Expects self.client (Supabase Client)."""

    def create_class_slot(
        self,
        user_id: str,
        slot_number: int,
        subject: str,
        grade: str,
        homeroom: Optional[str] = None,
        plan_group_label: Optional[str] = None,
        proficiency_levels: Optional[str] = None,
        primary_teacher_file: Optional[str] = None,
        primary_teacher_first_name: Optional[str] = None,
        primary_teacher_last_name: Optional[str] = None,
    ) -> str:
        """Create a class slot configuration."""
        slot_id = str(uuid.uuid4())

        primary_teacher_name = None
        if primary_teacher_first_name or primary_teacher_last_name:
            primary_teacher_name = f"{primary_teacher_first_name or ''} {primary_teacher_last_name or ''}".strip()

        insert_data = {
            "id": slot_id,
            "user_id": user_id,
            "slot_number": slot_number,
            "subject": subject,
            "grade": grade,
        }
        if homeroom is not None:
            insert_data["homeroom"] = homeroom
        if plan_group_label is not None:
            insert_data["plan_group_label"] = plan_group_label
        if proficiency_levels is not None:
            insert_data["proficiency_levels"] = proficiency_levels
        if primary_teacher_file is not None:
            insert_data["primary_teacher_file"] = primary_teacher_file
        if primary_teacher_first_name is not None:
            insert_data["primary_teacher_first_name"] = primary_teacher_first_name
        if primary_teacher_last_name is not None:
            insert_data["primary_teacher_last_name"] = primary_teacher_last_name
        if primary_teacher_name is not None:
            insert_data["primary_teacher_name"] = primary_teacher_name

        try:
            self.client.table("class_slots").insert(insert_data).execute()
            logger.info(
                "class_slot_created", extra={"slot_id": slot_id, "user_id": user_id}
            )
            return slot_id
        except APIError as e:
            error_str = str(e)
            if "plan_group_label" in error_str and "PGRST204" in error_str:
                logger.warning(
                    "plan_group_label column not found, retrying without it",
                    extra={"slot_id": slot_id, "user_id": user_id},
                )
                insert_data_without_field = {
                    k: v for k, v in insert_data.items() if k != "plan_group_label"
                }
                self.client.table("class_slots").insert(
                    insert_data_without_field
                ).execute()
                logger.info(
                    "class_slot_created", extra={"slot_id": slot_id, "user_id": user_id}
                )
                return slot_id
            logger.error(
                "class_slot_creation_failed",
                extra={"error": str(e), "slot_id": slot_id},
            )
            raise

    def get_user_slots(self, user_id: str) -> List[ClassSlot]:
        """Get all class slots for a user."""
        try:
            response = (
                self.client.table("class_slots")
                .select("*")
                .eq("user_id", user_id)
                .order("slot_number")
                .execute()
            )
            return [ClassSlot.model_validate(row) for row in response.data]
        except APIError as e:
            logger.error(
                "user_slots_fetch_failed", extra={"error": str(e), "user_id": user_id}
            )
            raise

    def get_slot(self, slot_id: str) -> Optional[ClassSlot]:
        """Get a specific class slot."""
        try:
            logger.info(
                "get_slot_attempt",
                extra={"slot_id": slot_id, "slot_id_length": len(slot_id) if slot_id else 0},
            )
            response = (
                self.client.table("class_slots").select("*").eq("id", slot_id).execute()
            )
            if response.data:
                logger.info("get_slot_found", extra={"slot_id": slot_id})
                return ClassSlot.model_validate(response.data[0])
            logger.warning("get_slot_not_found", extra={"slot_id": slot_id})
            return None
        except APIError as e:
            logger.error(
                "slot_fetch_failed",
                extra={"error": str(e), "slot_id": slot_id, "error_repr": repr(e)},
            )
            raise

    def update_class_slot(self, slot_id: str, **kwargs) -> bool:
        """Update class slot configuration."""
        logger.info(
            "update_class_slot_attempt",
            extra={"slot_id": slot_id, "update_fields": list(kwargs.keys())},
        )
        existing_slot = self.get_slot(slot_id)
        if not existing_slot:
            logger.warning(
                "class_slot_not_found_for_update",
                extra={
                    "slot_id": slot_id,
                    "slot_id_type": type(slot_id).__name__,
                    "kwargs_keys": list(kwargs.keys()),
                },
            )
            return False
        logger.info(
            "class_slot_found_for_update",
            extra={"slot_id": slot_id, "existing_user_id": existing_slot.user_id},
        )

        allowed_fields = [
            "subject",
            "grade",
            "homeroom",
            "proficiency_levels",
            "plan_group_label",
            "primary_teacher_file",
            "primary_teacher_name",
            "primary_teacher_file_pattern",
            "primary_teacher_first_name",
            "primary_teacher_last_name",
            "slot_number",
            "display_order",
        ]

        updates: Dict[str, Any] = {}
        updating_first = "primary_teacher_first_name" in kwargs
        updating_last = "primary_teacher_last_name" in kwargs

        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == "plan_group_label" and (value is None or value == ""):
                    continue
                updates[field] = value

        if updating_first or updating_last:
            slot = existing_slot
            if slot:
                f = kwargs.get(
                    "primary_teacher_first_name", slot.primary_teacher_first_name
                )
                l = kwargs.get(
                    "primary_teacher_last_name", slot.primary_teacher_last_name
                )
                computed_name = f"{f or ''} {l or ''}".strip()
                if computed_name:
                    updates["primary_teacher_name"] = computed_name
                if "primary_teacher_file_pattern" not in kwargs:
                    updates["primary_teacher_file_pattern"] = None

        filtered_updates = {}
        for key, value in updates.items():
            if key == "plan_group_label" and value is None:
                continue
            filtered_updates[key] = value

        if not filtered_updates:
            logger.info("class_slot_no_changes", extra={"slot_id": slot_id})
            return True

        filtered_updates["updated_at"] = datetime.now().isoformat()

        try:
            response = (
                self.client.table("class_slots")
                .update(filtered_updates)
                .eq("id", slot_id)
                .execute()
            )
            updated = len(response.data) > 0
            if not updated:
                logger.warning(
                    "class_slot_update_no_rows_affected",
                    extra={"slot_id": slot_id, "updates": list(filtered_updates.keys())},
                )
            return updated
        except APIError as e:
            error_str = str(e)
            error_repr = repr(e)
            if ("plan_group_label" in error_str or "plan_group_label" in error_repr) and (
                "PGRST204" in error_str
                or "PGRST204" in error_repr
                or "schema cache" in error_str.lower()
            ):
                logger.warning(
                    "plan_group_label column not found, retrying without it",
                    extra={"slot_id": slot_id, "error": error_str},
                )
                updates_without_field = {
                    k: v for k, v in filtered_updates.items() if k != "plan_group_label"
                }
                if updates_without_field:
                    try:
                        response = (
                            self.client.table("class_slots")
                            .update(updates_without_field)
                            .eq("id", slot_id)
                            .execute()
                        )
                        updated = len(response.data) > 0
                        return updated
                    except APIError as retry_error:
                        logger.error(
                            "class_slot_update_retry_failed",
                            extra={"error": str(retry_error), "slot_id": slot_id},
                        )
                        raise
            logger.error(
                "class_slot_update_failed",
                extra={"error": str(e), "error_repr": error_repr, "slot_id": slot_id},
            )
            raise

    def delete_class_slot(self, slot_id: str) -> bool:
        """Delete a class slot."""
        try:
            response = (
                self.client.table("class_slots").delete().eq("id", slot_id).execute()
            )
            deleted = len(response.data) > 0
            return deleted
        except APIError as e:
            logger.error(
                "slot_deletion_failed", extra={"error": str(e), "slot_id": slot_id}
            )
            raise

    def delete_user_slots(self, user_id: str) -> int:
        """Delete all class slots for a user."""
        try:
            slots = self.get_user_slots(user_id)
            count = len(slots)
            self.client.table("class_slots").delete().eq("user_id", user_id).execute()
            return count
        except APIError as e:
            logger.error(
                "user_slots_deletion_failed",
                extra={"error": str(e), "user_id": user_id},
            )
            raise
