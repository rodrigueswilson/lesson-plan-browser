"""Supabase user CRUD mixin."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import User

logger = logging.getLogger(__name__)


class SupabaseUsersMixin:
    """Mixin for user CRUD operations. Expects self.client (Supabase Client)."""

    def create_user(
        self,
        first_name: str = None,
        last_name: str = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a new user."""
        user_id = str(uuid.uuid4())

        if name and not (first_name and last_name):
            parts = name.strip().split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                first_name = parts[0]
                last_name = ""

        computed_name = f"{first_name or ''} {last_name or ''}".strip() or name or ""

        try:
            self.client.table("users").insert(
                {
                    "id": user_id,
                    "name": computed_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                }
            ).execute()
            logger.info("user_created", extra={"user_id": user_id})
            return user_id
        except APIError as e:
            logger.error(
                "user_creation_failed", extra={"error": str(e), "user_id": user_id}
            )
            raise

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            response = (
                self.client.table("users").select("*").eq("id", user_id).execute()
            )
            if response.data:
                return User.model_validate(response.data[0])
            return None
        except APIError as e:
            logger.error(
                "user_fetch_failed", extra={"error": str(e), "user_id": user_id}
            )
            raise

    def get_user_by_name(self, name: str) -> Optional[User]:
        """Get user by name."""
        try:
            response = self.client.table("users").select("*").eq("name", name).execute()
            if response.data:
                return User.model_validate(response.data[0])
            return None
        except APIError as e:
            logger.error(
                "user_fetch_by_name_failed", extra={"error": str(e), "name": name}
            )
            raise

    def list_users(self) -> List[User]:
        """Get all users."""
        try:
            response = self.client.table("users").select("*").order("name").execute()
            return [User.model_validate(row) for row in response.data]
        except APIError as e:
            logger.error("users_list_failed", extra={"error": str(e)})
            raise

    def update_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> bool:
        """Update user information."""
        if name and not (first_name or last_name):
            parts = name.strip().split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                first_name = parts[0]
                last_name = ""

        updates: Dict[str, Any] = {}

        if first_name is not None:
            updates["first_name"] = first_name
        if last_name is not None:
            updates["last_name"] = last_name

        if first_name is not None or last_name is not None:
            user = self.get_user(user_id)
            if user:
                f = first_name if first_name is not None else user.first_name
                l = last_name if last_name is not None else user.last_name
                computed_name = f"{f or ''} {l or ''}".strip()
                updates["name"] = computed_name

        if email is not None:
            updates["email"] = email

        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()

        try:
            response = (
                self.client.table("users").update(updates).eq("id", user_id).execute()
            )
            updated = len(response.data) > 0
            logger.info("user_updated", extra={"user_id": user_id, "updated": updated})
            return updated
        except APIError as e:
            logger.error(
                "user_update_failed", extra={"error": str(e), "user_id": user_id}
            )
            raise

    def update_user_base_path(self, user_id: str, base_path: str) -> bool:
        """Update user's base path override."""
        try:
            response = (
                self.client.table("users")
                .update(
                    {
                        "base_path_override": base_path,
                        "updated_at": datetime.now().isoformat(),
                    }
                )
                .eq("id", user_id)
                .execute()
            )
            updated = len(response.data) > 0
            logger.info(
                "user_base_path_updated", extra={"user_id": user_id, "updated": updated}
            )
            return updated
        except APIError as e:
            logger.error(
                "user_base_path_update_failed",
                extra={"error": str(e), "user_id": user_id},
            )
            raise

    def update_user_template_paths(
        self,
        user_id: str,
        template_path: Optional[str] = None,
        signature_image_path: Optional[str] = None,
    ) -> bool:
        """Update user's template path and/or signature image path."""
        try:
            updates = {"updated_at": datetime.now().isoformat()}
            if template_path is not None:
                updates["template_path"] = template_path
            if signature_image_path is not None:
                updates["signature_image_path"] = (
                    signature_image_path if signature_image_path.strip() else None
                )

            if len(updates) == 1:
                return False

            response = (
                self.client.table("users").update(updates).eq("id", user_id).execute()
            )
            updated = len(response.data) > 0
            return updated
        except APIError as e:
            logger.error(
                "user_template_paths_update_failed",
                extra={"error": str(e), "user_id": user_id},
            )
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data."""
        try:
            response = self.client.table("users").delete().eq("id", user_id).execute()
            deleted = len(response.data) > 0
            logger.info("user_deleted", extra={"user_id": user_id, "deleted": deleted})
            return deleted
        except APIError as e:
            logger.error(
                "user_deletion_failed", extra={"error": str(e), "user_id": user_id}
            )
            raise
