"""
Helpers for batch render (signature path, etc.). Used by combine_render.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from backend.telemetry import logger


def resolve_signature_image_path(user: Dict[str, Any]) -> Optional[str]:
    """
    Resolve the signature image path for a user. Normalizes empty string to None.
    For user "Wilson Rodrigues", falls back to known default paths if DB path
    is missing or invalid.
    """
    signature_image_path = user.get("signature_image_path")
    if signature_image_path and not signature_image_path.strip():
        signature_image_path = None

    user_name = user.get("name", "")
    if user_name and "Wilson Rodrigues" in user_name:
        if signature_image_path and not Path(signature_image_path).exists():
            logger.warning(
                "wilson_signature_db_path_not_found",
                extra={
                    "user": user_name,
                    "db_path": signature_image_path,
                    "falling_back_to_default": True,
                },
            )
            signature_image_path = None

        if not signature_image_path:
            possible_paths = [
                r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\wilson_rodrigues_signature.PNG",
                r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\wilson_rodrigues_signature.png",
                r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\wilson_rodrigues_signature.Png",
            ]
            for sig_path in possible_paths:
                if Path(sig_path).exists():
                    signature_image_path = sig_path
                    logger.info(
                        "using_default_wilson_signature",
                        extra={"path": sig_path, "user": user_name},
                    )
                    break
            else:
                logger.warning(
                    "wilson_signature_not_found",
                    extra={
                        "user": user_name,
                        "attempted_paths": possible_paths,
                    },
                )

    return signature_image_path
