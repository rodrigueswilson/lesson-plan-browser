"""
Render a single-slot combined lesson to DOCX and add signature/objectives/sentence frames.
"""

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from docx import Document

from backend.telemetry import logger
from tools.batch_processor_pkg.render_helpers import (
    normalize_lesson_json_for_render,
    resolve_signature_image_path,
)


def _render_single_slot(
    processor: Any,
    user: Dict[str, Any],
    lessons: List[Dict[str, Any]],
    week_of: str,
    output_path: str,
    template_path: str,
    generated_at: datetime,
    plan_id: Optional[str],
    renderer: Any,
    safe_finalize: Callable[[], None],
) -> str:
    """Render a single-slot combined lesson to DOCX and add signature/objectives."""
    from tools.diagnostic_logger import get_diagnostic_logger

    lesson = lessons[0]
    slot_num = lesson["slot_number"]
    subject = lesson["subject"]
    lesson_json = normalize_lesson_json_for_render(
        lesson["lesson_json"], slot_num, subject
    )

    logger.info(
        "batch_render_single_slot",
        extra={"output_file": Path(output_path).name, "week_of": week_of},
    )

    diag = get_diagnostic_logger()
    diag.log_before_render(slot_num, subject, lesson_json, "single_slot")

    output_dir = Path(output_path).parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as perm_error:
            raise PermissionError(
                f"Cannot write to output directory '{output_dir}': {perm_error}"
            )
    except Exception as dir_error:
        error_msg = f"Failed to create or access output directory '{output_dir}': {str(dir_error)}"
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        raise RuntimeError(error_msg) from dir_error

    try:
        render_success = renderer.render(
            lesson_json, output_path, plan_id=plan_id
        )
        if not render_success:
            raise RuntimeError(
                "Renderer returned False - rendering failed silently. Check logs for details."
            )
    except Exception as e:
        error_msg = (
            f"Renderer failed to generate file '{output_path}': {str(e)}"
        )
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

    if not Path(output_path).exists():
        error_msg = f"Renderer failed to create output file: {output_path}. File does not exist after render() call."
        print(f"ERROR: {error_msg}")
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            error_msg += f" Parent directory does not exist: {output_dir}"
        else:
            error_msg += f" Parent directory exists: {output_dir}"
        raise FileNotFoundError(error_msg)

    try:
        doc = Document(output_path)
    except Exception as e:
        error_msg = f"Failed to open rendered file '{output_path}': {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        raise FileNotFoundError(error_msg)

    signature_image_path = resolve_signature_image_path(user)

    try:
        processor._modify_existing_signature_table(
            doc, generated_at, signature_image_path, user.get("name")
        )
        doc.save(output_path)
    except Exception as e:
        error_msg = f"Failed to modify/save document '{output_path}': {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        raise

    try:
        from backend.services.objectives_printer import ObjectivesPrinter

        objectives_printer = ObjectivesPrinter()
        objectives_output_path = Path(output_path).with_name(
            Path(output_path).stem + "_objectives.docx"
        )
        objectives_printer.generate_docx(
            lesson_json,
            str(objectives_output_path),
            user_name=user.get("name"),
            week_of=week_of,
        )
        logger.info(
            "batch_objectives_docx_generated",
            extra={"objectives_path": str(objectives_output_path)},
        )
    except Exception as e:
        logger.warning(
            "batch_objectives_docx_failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )

    debug_marker = (
        Path(output_path).parent
        / f"{Path(output_path).stem}_objectives_debug.txt"
    )
    try:
        with open(debug_marker, "w", encoding="utf-8") as f:
            f.write(f"Objectives generation started at {datetime.now()}\n")
            f.write(f"Output path: {output_path}\n")
    except Exception:
        pass

    try:
        from backend.services.objectives_pdf_generator import (
            generate_objectives_pdf,
        )

        objectives_pdf_path = Path(output_path).with_name(
            Path(output_path).stem + "_objectives.pdf"
        )
        from backend.utils.lesson_times import enrich_lesson_json_with_times

        user_id = user.get("id") or user.get("user_id")
        if user_id:
            enrich_lesson_json_with_times(lesson_json, user_id)

        lesson_json_for_pdf = processor._sanitize_value(lesson_json)

        logger.info(
            "batch_objectives_pdf_html_starting",
            extra={"objectives_pdf_path": str(objectives_pdf_path)},
        )
        generate_objectives_pdf(
            lesson_json_for_pdf,
            str(objectives_pdf_path),
            user_name=user.get("name"),
            keep_html=True,
        )
        objectives_html_path = objectives_pdf_path.with_suffix(".html")

        if not objectives_pdf_path.exists():
            logger.error(
                "batch_objectives_pdf_not_created",
                extra={"expected_path": str(objectives_pdf_path)},
            )
        if not objectives_html_path.exists():
            logger.error(
                "batch_objectives_html_not_created",
                extra={"expected_path": str(objectives_html_path)},
            )

        logger.info(
            "batch_objectives_pdf_html_generated",
            extra={
                "objectives_pdf_path": str(objectives_pdf_path),
                "objectives_html_path": str(objectives_html_path),
                "pdf_exists": objectives_pdf_path.exists(),
                "html_exists": objectives_html_path.exists(),
            },
        )

        try:
            from backend.services.sentence_frames_pdf_generator import (
                generate_sentence_frames_pdf,
                generate_sentence_frames_docx,
            )

            output_dir = Path(output_path).parent
            output_stem = Path(output_path).stem
            sentence_frames_pdf_path = (
                output_dir / f"{output_stem}_sentence_frames.pdf"
            )

            has_frames = False
            frames_count = 0
            if "days" in lesson_json:
                for day_name, day in lesson_json["days"].items():
                    if not isinstance(day, dict):
                        continue
                    day_frames = day.get("sentence_frames")
                    if (
                        day_frames
                        and isinstance(day_frames, list)
                        and len(day_frames) > 0
                    ):
                        has_frames = True
                        frames_count += len(day_frames)
                    slots = day.get("slots", [])
                    if isinstance(slots, list):
                        for slot in slots:
                            if not isinstance(slot, dict):
                                continue
                            slot_frames = slot.get("sentence_frames")
                            if (
                                slot_frames
                                and isinstance(slot_frames, list)
                                and len(slot_frames) > 0
                            ):
                                has_frames = True
                                frames_count += len(slot_frames)

            if not has_frames and "days" in lesson_json_for_pdf:
                for day in lesson_json_for_pdf["days"].values():
                    if not isinstance(day, dict):
                        continue
                    if "sentence_frames" in day and day["sentence_frames"]:
                        has_frames = True
                        frames_count += len(day.get("sentence_frames", []))
                        break
                    if "slots" in day:
                        for s in day["slots"]:
                            if not isinstance(s, dict):
                                continue
                            if "sentence_frames" in s and s["sentence_frames"]:
                                has_frames = True
                                frames_count += len(
                                    s.get("sentence_frames", [])
                                )
                                break

            if has_frames:
                output_dir.mkdir(parents=True, exist_ok=True)
                generate_sentence_frames_pdf(
                    lesson_json_for_pdf,
                    str(sentence_frames_pdf_path),
                    user_name=user.get("name"),
                    keep_html=True,
                )
                sentence_frames_docx_path = (
                    sentence_frames_pdf_path.with_suffix(".docx")
                )
                generate_sentence_frames_docx(
                    lesson_json_for_pdf,
                    str(sentence_frames_docx_path),
                    user_name=user.get("name"),
                )
                logger.info(
                    "batch_sentence_frames_pdf_generated",
                    extra={
                        "path": str(sentence_frames_pdf_path),
                        "pdf_exists": sentence_frames_pdf_path.exists(),
                        "frames_count": frames_count,
                    },
                )
            else:
                logger.warning(
                    "batch_sentence_frames_skipped_no_data",
                    extra={
                        "plan_id": plan_id,
                        "output_path": str(output_path),
                        "has_days": "days" in lesson_json,
                    },
                )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(
                "batch_sentence_frames_pdf_html_failed",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
    except Exception as e:
        logger.warning(
            "batch_objectives_pdf_html_failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )

    logger.info(
        "batch_render_single_slot_success", extra={"output_path": output_path}
    )
    safe_finalize()
    return output_path
