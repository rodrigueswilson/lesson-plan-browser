"""
Helpers for batch render (signature path, lesson JSON normalization). Used by combine_render.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from backend.telemetry import logger


def normalize_lesson_json_for_render(
    lesson_json: Any,
    slot_num: Any,
    subject: str,
) -> Dict[str, Any]:
    """
    Ensure lesson_json is a dict with metadata and _source_slot/_source_subject on media.
    Mutates and returns the same dict.
    """
    if not isinstance(lesson_json, dict):
        if hasattr(lesson_json, "model_dump"):
            lesson_json = lesson_json.model_dump()
        elif hasattr(lesson_json, "dict"):
            lesson_json = lesson_json.dict()
        else:
            lesson_json = dict(lesson_json) if lesson_json else {}

    if "metadata" not in lesson_json:
        lesson_json["metadata"] = {}
    lesson_json["metadata"]["slot_number"] = slot_num
    lesson_json["metadata"]["subject"] = subject

    if "_hyperlinks" in lesson_json:
        for link in lesson_json.get("_hyperlinks", []):
            if isinstance(link, dict):
                link["_source_slot"] = slot_num
                link["_source_subject"] = subject

    if "_images" in lesson_json:
        for image in lesson_json.get("_images", []):
            if isinstance(image, dict):
                image["_source_slot"] = slot_num
                image["_source_subject"] = subject

    return lesson_json


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
