"""
Helpers for auto-generating per-plan JSON backups after successful rendering.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.telemetry import logger

_ARTIFACT_TS_RE = re.compile(r"_(\d{8}_\d{6})\.docx$", re.IGNORECASE)


def extract_artifact_timestamp(output_file: str) -> Optional[datetime]:
    """Extract generation timestamp from DOCX filename."""
    if not output_file:
        return None
    name = Path(output_file).name
    match = _ARTIFACT_TS_RE.search(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def build_artifact_metadata(output_file: str, generated_at: Optional[datetime]) -> Dict[str, Any]:
    """Build artifact metadata block for lesson_json and backup payload."""
    output_path = Path(output_file)
    stem = output_path.stem
    ts_token = None
    if generated_at:
        ts_token = generated_at.strftime("%Y%m%d_%H%M%S")

    return {
        "artifact_timestamp_token": ts_token,
        "artifact_generated_at": generated_at.isoformat() if generated_at else None,
        "artifact_files": {
            "lesson_plan_docx": str(output_path),
            "objectives_docx": str(output_path.with_name(f"{stem}_objectives.docx")),
            "objectives_pdf": str(output_path.with_name(f"{stem}_objectives.pdf")),
            "objectives_html": str(output_path.with_name(f"{stem}_objectives.html")),
            "sentence_frames_docx": str(output_path.with_name(f"{stem}_sentence_frames.docx")),
            "sentence_frames_pdf": str(output_path.with_name(f"{stem}_sentence_frames.pdf")),
            "sentence_frames_html": str(output_path.with_name(f"{stem}_sentence_frames.html")),
        },
    }


def _normalize_lesson_json(lesson_json: Any) -> Dict[str, Any]:
    if isinstance(lesson_json, dict):
        return lesson_json
    return {}


def create_auto_backup_payload(plan: Any, artifact_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create backup payload compatible with restore format plus metadata."""
    lesson_json = _normalize_lesson_json(getattr(plan, "lesson_json", None))
    metadata = lesson_json.setdefault("metadata", {})
    metadata.update(artifact_metadata)

    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "week_of": plan.week_of,
        "status": plan.status or "pending",
        "output_file": plan.output_file,
        "week_folder_path": getattr(plan, "week_folder_path", None),
        "consolidated": int(getattr(plan, "consolidated", 0) or 0),
        "total_slots": int(getattr(plan, "total_slots", 1) or 1),
        "generated_at": plan.generated_at.isoformat() if getattr(plan, "generated_at", None) else None,
        "processing_time_ms": getattr(plan, "processing_time_ms", None),
        "total_tokens": getattr(plan, "total_tokens", None),
        "total_cost_usd": getattr(plan, "total_cost_usd", None),
        "llm_model": getattr(plan, "llm_model", None),
        "error_message": getattr(plan, "error_message", None),
        "lesson_json": lesson_json,
        "auto_backup_created_at": datetime.utcnow().isoformat(),
        "auto_backup_type": "post_generation",
    }


def write_auto_backup_file(plan: Any, output_file: str, artifact_metadata: Dict[str, Any]) -> Optional[str]:
    """Write auto backup JSON beside generated DOCX."""
    if not output_file:
        return None

    output_path = Path(output_file)
    backup_path = output_path.with_name(f"{output_path.stem}_plan-backup.json")
    payload = create_auto_backup_payload(plan, artifact_metadata)

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with backup_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    logger.info(
        "weekly_plan_auto_backup_created",
        extra={
            "plan_id": getattr(plan, "id", None),
            "backup_path": str(backup_path),
        },
    )
    return str(backup_path)
