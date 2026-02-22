"""
Combine lessons into a single DOCX, merge DOCX files, and convert/reconstruct lesson JSON.
Extracted from orchestrator for single responsibility and testability.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from docx import Document

from backend.telemetry import logger
from tools.batch_processor_pkg.combine_render import (
    _render_multi_slot,
    _render_single_slot,
)
from tools.batch_processor_pkg.originals_json import (
    convert_originals_to_json,
    reconstruct_slots_from_json,
)


def merge_docx_files(
    file_paths: List[str],
    output_path: str,
    master_template_path: Optional[str] = None,
) -> None:
    """
    Merge multiple DOCX files into one using docxcompose.
    Each document is separated by a page break.

    Args:
        file_paths: List of DOCX file paths to merge
        output_path: Path for merged output file
        master_template_path: Optional path to a template to use as the base
    """
    from docxcompose.composer import Composer

    if not file_paths:
        raise ValueError("No files to merge")

    logger.debug("batch_merge_docx_start", extra={"file_count": len(file_paths)})

    if master_template_path:
        master = Document(master_template_path)
        for p in list(master.paragraphs):
            p._element.getparent().remove(p._element)
        for t in list(master.tables):
            t._element.getparent().remove(t._element)
        composer = Composer(master)
        start_idx = 0
    else:
        master = Document(file_paths[0])
        composer = Composer(master)
        start_idx = 1

    for i, file_path in enumerate(file_paths[start_idx:], start_idx + 1):
        logger.debug(
            "batch_merge_docx_append",
            extra={"index": i, "file_name": Path(file_path).name},
        )
        doc = Document(file_path)

        if i > 1:
            page_break_para = doc.add_page_break()
            para_element = page_break_para._element
            para_element.getparent().remove(para_element)
            doc._element.body.insert(0, para_element)

        composer.append(doc)

    logger.debug(
        "batch_merge_docx_save", extra={"output_file": Path(output_path).name}
    )
    composer.save(output_path)


def combine_lessons(
    processor: Any,
    user: Dict[str, Any],
    lessons: List[Dict[str, Any]],
    week_of: str,
    generated_at: datetime,
    plan_id: Optional[str] = None,
    get_file_manager_fn: Optional[Callable[..., Any]] = None,
) -> str:
    """
    Combine multiple lessons into a single DOCX using JSON merging.
    Delegates to combine_lessons_impl; wraps with tracking when plan_id is set.
    """
    lessons.sort(key=lambda x: x["slot_number"])

    logger.info(
        "batch_combining_lessons",
        extra={"lesson_count": len(lessons), "user_id": user["id"]},
    )

    if plan_id:
        with processor.tracker.track_operation(
            plan_id,
            "render_combine_lessons",
            metadata={
                "slot_count": len(lessons),
                "consolidated": len(lessons) > 1,
            },
        ):
            return combine_lessons_impl(
                processor,
                user,
                lessons,
                week_of,
                generated_at,
                plan_id,
                get_file_manager_fn,
            )
    return combine_lessons_impl(
        processor,
        user,
        lessons,
        week_of,
        generated_at,
        plan_id,
        get_file_manager_fn,
    )


def combine_lessons_impl(
    processor: Any,
    user: Dict[str, Any],
    lessons: List[Dict[str, Any]],
    week_of: str,
    generated_at: datetime,
    plan_id: Optional[str] = None,
    get_file_manager_fn: Optional[Callable[..., Any]] = None,
) -> str:
    """
    Internal implementation of combine_lessons (without tracking wrapper).
    Merges lesson JSONs, validates, enriches with times, renders to DOCX (single or multi-slot).
    """
    from tools.diagnostic_logger import finalize_diagnostics
    from tools.json_merger import (
        get_merge_summary,
        merge_lesson_jsons,
        validate_merged_json,
    )

    if get_file_manager_fn is None:
        from tools.batch_processor import get_file_manager as _get_fm
        get_file_manager_fn = _get_fm

    def _safe_finalize():
        try:
            finalize_diagnostics()
        except Exception:
            logger.warning("diagnostic_finalize_failed", exc_info=True)

    merged_json = merge_lesson_jsons(lessons)

    is_valid, error_msg = validate_merged_json(merged_json)
    if not is_valid:
        raise ValueError(f"Merged JSON validation failed: {error_msg}")

    logger.debug(
        "batch_merge_summary", extra={"summary": get_merge_summary(merged_json)}
    )

    from backend.utils.lesson_times import enrich_lesson_json_with_times

    user_id = user.get("id") or user.get("user_id")
    if user_id:
        enrich_lesson_json_with_times(merged_json, user_id)

    merged_json["metadata"]["user_name"] = user["name"]

    file_mgr = get_file_manager_fn(base_path=user.get("base_path_override"))
    week_folder = file_mgr.get_week_folder(week_of)

    if len(lessons) > 1:
        week_num = None
        folder_name = week_folder.name
        week_match = re.search(
            r"(\d{2})\s*W\s*(\d{1,2})\b", folder_name, re.IGNORECASE
        )
        if week_match:
            week_num = int(week_match.group(2))
            logger.debug(
                "week_number_extracted_from_folder",
                extra={"folder_name": folder_name, "week_num": week_num},
            )

        if week_num is None:
            week_num = processor._get_week_num(week_of)
            logger.debug(
                "week_number_calculated_from_date",
                extra={"week_of": week_of, "week_num": week_num},
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user['name'].replace(' ', '_')}_Weekly_W{week_num:02d}_{week_of.replace('/', '-')}_{timestamp}.docx"
        output_path = str(week_folder / filename)

        merged_json["metadata"]["total_slots"] = len(lessons)

        teachers = set()
        subjects = set()
        for lesson in lessons:
            if (
                lesson.get("lesson_json", {})
                .get("metadata", {})
                .get("teacher_name")
            ):
                teachers.add(lesson["lesson_json"]["metadata"]["teacher_name"])
            if lesson.get("subject"):
                subjects.add(lesson["subject"])

        if len(teachers) > 1:
            merged_json["metadata"]["teacher_name"] = " / ".join(sorted(teachers))
        if len(subjects) > 1:
            merged_json["metadata"]["subject"] = " / ".join(sorted(subjects))
    else:
        output_path = file_mgr.get_output_path_with_timestamp(
            week_folder, user["name"], week_of
        )

    template_path = (
        user.get("template_path") or "input/Lesson Plan Template SY'25-26.docx"
    )
    if not Path(template_path).exists():
        logger.warning(
            "user_template_not_found",
            extra={"user_id": user.get("id"), "template_path": template_path},
        )
        template_path = "input/Lesson Plan Template SY'25-26.docx"

    if not Path(template_path).exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}. "
            f"Please ensure the template exists at this path."
        )

    from tools.docx_renderer import DOCXRenderer

    renderer = DOCXRenderer(template_path)

    if len(lessons) == 1:
        return _render_single_slot(
            processor,
            user,
            lessons,
            week_of,
            output_path,
            template_path,
            generated_at,
            plan_id,
            renderer,
            _safe_finalize,
        )
    return _render_multi_slot(
        processor,
        user,
        lessons,
        week_of,
        output_path,
        template_path,
        generated_at,
        plan_id,
        merged_json,
        renderer,
        file_mgr,
        _safe_finalize,
    )
