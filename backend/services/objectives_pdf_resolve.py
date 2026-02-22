"""
Path resolution helpers for objectives PDF/HTML output.

Extracted from objectives_pdf_generator to keep the generator slim.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.telemetry import logger
from backend.utils.metadata_utils import get_teacher_name


def sanitize_for_filename(value: str, fallback: str) -> str:
    """Make a string safe for use in filenames."""
    clean = re.sub(r"[^A-Za-z0-9]+", "_", (value or "")).strip("_")
    return clean or fallback


def build_default_basename(
    lesson_json: Dict[str, Any],
    user_name: Optional[str],
) -> str:
    """Build default base filename from lesson metadata."""
    metadata = lesson_json.get("metadata", {})
    teacher = get_teacher_name(metadata, user_name=user_name) or "Teacher"
    week_label = metadata.get("week_of") or datetime.now().strftime("%m-%d")
    teacher_slug = sanitize_for_filename(teacher, "Teacher")
    week_slug = sanitize_for_filename(week_label.replace("/", "-"), "Week")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{teacher_slug}_Objectives_{week_slug}_{timestamp}"


def resolve_output_directory(
    file_manager: Any,
    lesson_json: Dict[str, Any],
    default_dir: Path,
) -> Path:
    """Resolve output directory from week_of or use default."""
    metadata = lesson_json.get("metadata", {})
    week_of = metadata.get("week_of")
    if week_of:
        try:
            week_folder = Path(file_manager.get_week_folder(week_of))
            week_folder.mkdir(parents=True, exist_ok=True)
            return week_folder
        except Exception as exc:
            logger.warning(
                "objectives_week_folder_resolution_failed",
                extra={"week_of": week_of, "error": str(exc)},
            )
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir


def resolve_html_path(
    file_manager: Any,
    default_dir: Path,
    lesson_json: Dict[str, Any],
    user_name: Optional[str],
    output_path: Optional[str],
) -> Path:
    """Resolve path for HTML output file."""
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    directory = resolve_output_directory(file_manager, lesson_json, default_dir)
    base_name = build_default_basename(lesson_json, user_name)
    target = directory / f"{base_name}.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def resolve_pdf_and_html_paths(
    file_manager: Any,
    default_dir: Path,
    lesson_json: Dict[str, Any],
    user_name: Optional[str],
    pdf_path: Optional[str],
) -> Tuple[Path, Path]:
    """Resolve paths for both HTML and PDF output files."""
    if pdf_path:
        pdf_file = Path(pdf_path)
        html_file = pdf_file.with_suffix(".html")
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        html_file.parent.mkdir(parents=True, exist_ok=True)
        return html_file, pdf_file
    directory = resolve_output_directory(file_manager, lesson_json, default_dir)
    base_name = build_default_basename(lesson_json, user_name)
    html_file = directory / f"{base_name}.html"
    pdf_file = directory / f"{base_name}.pdf"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    return html_file, pdf_file
