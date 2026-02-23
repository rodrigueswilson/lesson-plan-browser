"""
HTML + PDF generator for lesson plan objectives with precise layout control.

This module provides an alternative to DOCX generation for objectives,
offering pixel-perfect control over text positioning and page layout.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.file_manager import get_file_manager
from backend.services.objectives_pdf_extraction import (
    extract_from_day as extract_from_day_fn,
    extract_from_slot as extract_from_slot_fn,
)
from backend.services.objectives_pdf_resolve import (
    resolve_html_path as resolve_html_path_fn,
    resolve_output_directory as resolve_output_directory_fn,
    resolve_pdf_and_html_paths as resolve_pdf_and_html_paths_fn,
)
from backend.services.objectives_pdf_templates import (
    get_css_template as get_css_template_fn,
    get_day_date_for_objectives,
    get_html_template as get_html_template_fn,
)
from backend.services.objectives_utils import normalize_objective_payload
from backend.services.sorting_utils import sort_slots
from backend.telemetry import logger
from backend.utils.metadata_utils import build_document_header, get_teacher_name

from backend.services.objectives_pdf_subject import extract_subject_from_unit_lesson

__all__ = [
    "ObjectivesPDFGenerator",
    "extract_subject_from_unit_lesson",
    "generate_objectives_pdf",
    "generate_objectives_html",
]


class ObjectivesPDFGenerator:
    """Generate objectives as HTML and convert to PDF with precise layout control."""

    def __init__(self):
        """Initialize the PDF generator."""
        self.css_template = get_css_template_fn()
        self.html_template = get_html_template_fn()
        self.file_manager = get_file_manager()
        self._default_output_dir = Path(self.file_manager.base_path)

    def _resolve_output_directory(self, lesson_json: Dict[str, Any]) -> Path:
        return resolve_output_directory_fn(
            self.file_manager, lesson_json, self._default_output_dir
        )

    def _resolve_html_path(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        output_path: Optional[str],
    ) -> Path:
        return resolve_html_path_fn(
            self.file_manager,
            self._default_output_dir,
            lesson_json,
            user_name,
            output_path,
        )

    def _resolve_pdf_and_html_paths(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        pdf_path: Optional[str],
    ) -> Tuple[Path, Path]:
        return resolve_pdf_and_html_paths_fn(
            self.file_manager,
            self._default_output_dir,
            lesson_json,
            user_name,
            pdf_path,
        )

    def _get_day_date(self, week_of: str, day_name: str) -> str:
        """Get the date for a specific day of the week using standardized utility."""
        return get_day_date_for_objectives(week_of, day_name)

    def _calculate_font_size(
        self,
        text: str,
        available_width: float,  # inches
        available_height: float,  # inches
        min_font_size: int = 12,
        max_font_size: int = 60,
    ) -> int:
        """
        Calculate optimal font size to fill available space.

        Uses conservative estimates to ensure text fits within bounds.
        """
        if not text or not text.strip():
            return min_font_size

        # Estimate character count and lines needed
        words = text.split()
        total_chars = len(text.replace(" ", ""))

        # Conservative character width ratio (Verdana is wider)
        char_width_ratio = 0.6
        line_height_ratio = 1.3

        # Calculate font size using area-based approach
        # Formula derived from: height = (chars * font_size^2 * ratios) / (width * 72^2)
        numerator = available_height * available_width * 72 * 72
        denominator = total_chars * char_width_ratio * line_height_ratio

        if denominator > 0:
            font_size_squared = numerator / denominator
            font_size = font_size_squared**0.5

            # Apply 75% safety factor for rendering differences
            font_size = font_size * 0.75
        else:
            font_size = min_font_size

        # Clamp to bounds
        return max(min_font_size, min(int(font_size), max_font_size))

    def extract_objectives(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract objectives from lesson plan JSON.

        Handles both single-slot and multi-slot structures:
        - Single-slot: days.monday.unit_lesson
        - Multi-slot: days.monday.slots[0].unit_lesson
        """
        objectives = []

        if "days" not in lesson_json:
            return objectives

        metadata = lesson_json.get("metadata", {})
        week_of = metadata.get("week_of", "Unknown")
        grade = metadata.get("grade", "Unknown")
        subject = metadata.get("subject", "Unknown")
        homeroom = metadata.get("homeroom", "Unknown")
        room = metadata.get("room", "")
        teacher_name = get_teacher_name(metadata)

        days = lesson_json["days"]
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]

        for day_name in day_names:
            if day_name not in days:
                continue

            day_data = days[day_name]

            # Check if this is a multi-slot structure
            if "slots" in day_data and isinstance(day_data["slots"], list):
                # Multi-slot: iterate through slots
                # Sort slots by start_time (chronological) with slot_number as fallback
                sorted_slots = sort_slots(day_data["slots"])
                logger.debug(
                    f"Extracting objectives for {day_name}: {len(sorted_slots)} slots found (slot_numbers: {[s.get('slot_number', 0) for s in sorted_slots]})"
                )
                for slot in sorted_slots:
                    slot_num = slot.get("slot_number", 0)
                    logger.debug(
                        f"Processing slot {slot_num} ({day_name}) for objectives extraction"
                    )
                    extract_from_slot_fn(
                        slot,
                        day_name,
                        week_of,
                        grade,
                        homeroom,
                        room,
                        teacher_name,
                        objectives,
                        metadata,
                    )
            else:
                extract_from_day_fn(
                    day_data,
                    day_name,
                    week_of,
                    grade,
                    homeroom,
                    room,
                    metadata,
                    subject,
                    objectives,
                )

        return objectives

    def generate_html(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> str:
        """Generate HTML file with objectives, one lesson per page."""

        objectives = self.extract_objectives(lesson_json)
        if not objectives:
            raise ValueError("No objectives found in lesson plan")

        # Get metadata for header building
        metadata = lesson_json.get("metadata", {})

        pages = []
        for obj in objectives:
            day_date = self._get_day_date(obj["week_of"], obj["day"])

            student_goal_text = (
                obj.get("student_goal", "").strip() or "No Student Goal specified"
            )
            student_goal_font_size = self._calculate_font_size(
                student_goal_text, 10.0, 5.29, min_font_size=14, max_font_size=70
            )

            wida_text = (
                obj.get("wida_objective", "").strip() or "No WIDA Objective specified"
            )
            wida_font_size = self._calculate_font_size(
                wida_text, 10.0, 1.76, min_font_size=10, max_font_size=20
            )

            # Build standardized header using metadata_utils helper
            # Reconstruct slot dict for header builder (if slot-specific)
            slot_dict = None
            if obj.get("slot_number"):
                slot_dict = {
                    "subject": obj.get("subject"),
                    "grade": obj.get("grade"),
                    "homeroom": obj.get("homeroom"),
                    "room": obj.get("room"),
                    "time": obj.get("time"),
                }

            header_text = build_document_header(
                metadata=metadata,
                slot=slot_dict,
                day_date=day_date,
                day_name=obj.get("day"),
                include_time=True,  # Objectives PDF includes time if present
                include_day_name=True,  # Include day name for consistency
            )

            pages.append(f"""
            <div class="objectives-page">
                <div class="header">{header_text}</div>
                <div class="student-goal-section">
                    <div class="student-goal" style="font-size: {student_goal_font_size}pt;">
                        {student_goal_text}
                    </div>
                </div>
                <div class="separator"></div>
                <div class="wida-section">
                    <div class="wida-label">WIDA/Bilingual:</div>
                    <div class="wida-objective" style="font-size: {wida_font_size}pt;">{wida_text}</div>
                </div>
            </div>
            """)

        final_html = self.html_template.format(
            css=self.css_template,
            pages="\n".join(pages),
            week_of=objectives[0]["week_of"],
        )

        output_file = self._resolve_html_path(lesson_json, user_name, output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        logger.info(
            "objectives_html_generated",
            extra={
                "output_path": str(output_file),
                "objective_count": len(objectives),
                "week_of": objectives[0]["week_of"],
            },
        )

        return str(output_file)

    def convert_to_pdf(self, html_path: str, pdf_path: str) -> str:
        """Convert HTML file to PDF using WeasyPrint with Playwright fallback."""

        html_file = Path(html_path)
        pdf_file = Path(pdf_path)
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        if pdf_file.exists():
            try:
                pdf_file.unlink()
            except OSError:
                pass

        try:
            import weasyprint

            weasyprint.HTML(filename=str(html_file)).write_pdf(
                str(pdf_file), stylesheets=[weasyprint.CSS(string=self.css_template)]
            )
            logger.info(
                "weasyprint_pdf_generated",
                extra={"html_path": str(html_file), "pdf_path": str(pdf_file)},
            )
            return str(pdf_file)
        except Exception as exc:
            logger.warning(
                "weasyprint_failed",
                extra={
                    "html_path": str(html_file),
                    "pdf_path": str(pdf_file),
                    "error": str(exc),
                },
            )

        return self._convert_html_with_playwright(str(html_file), str(pdf_file))

    def _convert_html_with_playwright(self, html_path: str, pdf_path: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            logger.error("playwright_not_installed", extra={"error": str(exc)})
            raise

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{html_path}", wait_until="networkidle")
            page.pdf(
                path=pdf_path, format="Letter", landscape=True, print_background=True
            )
            browser.close()

        logger.info(
            "playwright_pdf_generated",
            extra={"html_path": html_path, "pdf_path": pdf_path},
        )
        return pdf_path

    def generate_pdf(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
        keep_html: bool = False,
    ) -> str:
        """Generate PDF file with objectives (HTML + PDF conversion)."""

        html_path, pdf_path = self._resolve_pdf_and_html_paths(
            lesson_json, user_name, output_path
        )
        generated_html = self.generate_html(lesson_json, str(html_path), user_name)
        final_pdf = self.convert_to_pdf(generated_html, str(pdf_path))
        if not keep_html:
            try:
                Path(generated_html).unlink()
            except OSError:
                pass
        return final_pdf


def generate_objectives_pdf(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
    keep_html: bool = False,
) -> str:
    """
    Convenience function to generate objectives PDF from lesson JSON.

    Args:
        lesson_json: Lesson plan JSON structure
        output_path: Path to save PDF file
        user_name: Optional teacher name for file naming
        keep_html: Whether to keep the intermediate HTML file

    Returns:
        Path to generated PDF file
    """
    generator = ObjectivesPDFGenerator()
    return generator.generate_pdf(lesson_json, output_path, user_name, keep_html)


def generate_objectives_html(
    lesson_json: Dict[str, Any], output_path: str, user_name: Optional[str] = None
) -> str:
    """
    Convenience function to generate objectives HTML from lesson JSON.

    Args:
        lesson_json: Lesson plan JSON structure
        output_path: Path to save HTML file
        user_name: Optional teacher name for file naming

    Returns:
        Path to generated HTML file
    """
    generator = ObjectivesPDFGenerator()
    return generator.generate_html(lesson_json, output_path, user_name)
