"""
HTML + PDF generator for lesson plan objectives with precise layout control.

This module provides an alternative to DOCX generation for objectives,
offering pixel-perfect control over text positioning and page layout.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings
from backend.file_manager import get_file_manager
from backend.services.objectives_utils import normalize_objective_payload
from backend.services.sorting_utils import sort_slots
from backend.telemetry import logger
from backend.utils.metadata_utils import (
    build_document_header,
    get_day_date,
    get_homeroom,
    get_subject,
    get_teacher_name,
)


def extract_subject_from_unit_lesson(unit_lesson: str) -> str:
    """
    Extract the actual subject from the unit_lesson text.

    This function parses patterns like:
    - "Unit 3 Lesson 9: MEASURE TO FIND THE AREA" -> "Math"
    - "Math Chapter 5: MULTIPLICATION FACTS" -> "Math"
    - "ELA Unit 2: READING COMPREHENSION" -> "ELA"
    - "Science Lab: PLANT GROWTH" -> "Science"

    Args:
        unit_lesson: The unit/lesson text from the lesson plan

    Returns:
        Detected subject name or "Unknown" if not found
    """
    import re

    if not unit_lesson or not isinstance(unit_lesson, str):
        return "Unknown"

    unit_lesson = unit_lesson.strip().upper()

    # Pattern 1: Explicit subject prefixes
    subject_patterns = {
        r"\bMATH\b": "Math",
        r"\bELA\b": "ELA",
        r"\bENGLISH\b": "ELA",
        r"\bREADING\b": "ELA",
        r"\bWRITING\b": "ELA",
        r"\bSCIENCE\b": "Science",
        r"\bSOCIAL STUDIES\b": "Social Studies",
        r"\bHISTORY\b": "Social Studies",
        r"\bGEOGRAPHY\b": "Social Studies",
        r"\bART\b": "Art",
        r"\bMUSIC\b": "Music",
        r"\bPE\b": "Physical Education",
        r"\bPHYSICAL EDUCATION\b": "Physical Education",
        r"\bHEALTH\b": "Health",
        r"\bLIBRARY\b": "Library",
        r"\bTECH\b": "Technology",
        r"\bTECHNOLOGY\b": "Technology",
        r"\bCOMPUTER\b": "Technology",
    }

    for pattern, subject in subject_patterns.items():
        if re.search(pattern, unit_lesson):
            return subject

    # Pattern 2: Math-specific keywords
    math_keywords = [
        "MULTIPLICATION",
        "DIVISION",
        "ADDITION",
        "SUBTRACTION",
        "MEASURE",
        "AREA",
        "PERIMETER",
        "GEOMETRY",
        "FRACTIONS",
        "DECIMALS",
        "PLACE VALUE",
        "NUMBER",
        "CALCULATION",
        "EQUATION",
        "PROBLEM SOLVING",
        "MATH CHAPTER",
        "UNIT .* LESSON",
        "UNIT",  # Add standalone UNIT pattern
    ]

    for keyword in math_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Math"

    # Pattern 3: ELA-specific keywords
    ela_keywords = [
        "READING",
        "COMPREHENSION",
        "GRAMMAR",
        "SPELLING",
        "VOCABULARY",
        "WRITING",
        "PHONICS",
        "LITERATURE",
        "STORY",
        "POEM",
        "ESSAY",
        "LANGUAGE ARTS",
    ]

    for keyword in ela_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "ELA"

    # Pattern 4: Science-specific keywords
    science_keywords = [
        "EXPERIMENT",
        "LAB",
        "ORGANISM",
        "HABITAT",
        "ECOSYSTEM",
        "MATTER",
        "ENERGY",
        "FORCE",
        "MOTION",
        "PLANT",
        "ANIMAL",
    ]

    for keyword in science_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Science"

    # Pattern 5: Social Studies keywords
    ss_keywords = [
        "COMMUNITY",
        "GOVERNMENT",
        "HISTORY",
        "GEOGRAPHY",
        "CULTURE",
        "SOCIETY",
        "CIVICS",
        "ECONOMICS",
    ]

    for keyword in ss_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Social Studies"

    # Default: Return "Unknown"
    return "Unknown"


class ObjectivesPDFGenerator:
    """Generate objectives as HTML and convert to PDF with precise layout control."""

    def __init__(self):
        """Initialize the PDF generator."""
        self.css_template = self._get_css_template()
        self.html_template = self._get_html_template()
        self.file_manager = get_file_manager()
        self._default_output_dir = Path(self.file_manager.base_path)

    def _resolve_output_directory(self, lesson_json: Dict[str, Any]) -> Path:
        metadata = lesson_json.get("metadata", {})
        week_of = metadata.get("week_of")
        if week_of:
            try:
                week_folder = Path(self.file_manager.get_week_folder(week_of))
                week_folder.mkdir(parents=True, exist_ok=True)
                return week_folder
            except Exception as exc:
                logger.warning(
                    "objectives_week_folder_resolution_failed",
                    extra={"week_of": week_of, "error": str(exc)},
                )

        self._default_output_dir.mkdir(parents=True, exist_ok=True)
        return self._default_output_dir

    def _sanitize_for_filename(self, value: str, fallback: str) -> str:
        import re

        clean = re.sub(r"[^A-Za-z0-9]+", "_", (value or "")).strip("_")
        return clean or fallback

    def _build_default_basename(
        self, lesson_json: Dict[str, Any], user_name: Optional[str]
    ) -> str:
        metadata = lesson_json.get("metadata", {})
        teacher = get_teacher_name(metadata, user_name=user_name) or "Teacher"
        week_label = metadata.get("week_of") or datetime.now().strftime("%m-%d")
        teacher_slug = self._sanitize_for_filename(teacher, "Teacher")
        week_slug = self._sanitize_for_filename(week_label.replace("/", "-"), "Week")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{teacher_slug}_Objectives_{week_slug}_{timestamp}"

    def _resolve_html_path(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        output_path: Optional[str],
    ) -> Path:
        if output_path:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            return target

        directory = self._resolve_output_directory(lesson_json)
        base_name = self._build_default_basename(lesson_json, user_name)
        target = directory / f"{base_name}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _resolve_pdf_and_html_paths(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        pdf_path: Optional[str],
    ) -> Tuple[Path, Path]:
        if pdf_path:
            pdf_file = Path(pdf_path)
            html_file = pdf_file.with_suffix(".html")
            pdf_file.parent.mkdir(parents=True, exist_ok=True)
            html_file.parent.mkdir(parents=True, exist_ok=True)
            return html_file, pdf_file

        directory = self._resolve_output_directory(lesson_json)
        base_name = self._build_default_basename(lesson_json, user_name)
        html_file = directory / f"{base_name}.html"
        pdf_file = directory / f"{base_name}.pdf"
        html_file.parent.mkdir(parents=True, exist_ok=True)
        return html_file, pdf_file

    def _get_css_template(self) -> str:
        """Return CSS for precise layout control."""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');

        @page {
            size: 11in 8.5in;  /* Landscape US Letter */
            margin: 0.5in;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Source Sans Pro', 'Inter', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background: white;
        }
        
        .objectives-page {
            width: 10in;  /* 11" - 0.5" margins */
            height: 7.5in;  /* 8.5" - 0.5" margins */
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }
        
        .header {
            height: 0.3in;
            font-size: 10pt;
            color: #333;
            display: flex;
            align-items: center;
            margin-bottom: 0.05in;
        }
        
        .student-goal-section {
            flex: 3;  /* 75% of remaining space */
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
        }
        
        .student-goal {
            font-family: 'Source Sans Pro', 'Inter', sans-serif;
            font-weight: 600;
            color: #000;
            line-height: 1.35;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        .separator {
            height: 0.15in;
            margin: 0.1in 0;
            border-bottom: 1px solid #808080;
        }
        
        .wida-section {
            flex: 1;  /* 25% of remaining space */
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
            padding-top: 0.05in;
        }
        
        .wida-label {
            font-size: 11pt;
            font-weight: bold;
            color: #808080;
            margin-bottom: 0.05in;
        }
        
        .wida-objective {
            /* font-size set dynamically via inline style */
            color: #808080;
            line-height: 1.3;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-height: 100%;
            overflow: visible;
        }
        
        /* Print-specific styles */
        @media print {
            .objectives-page {
                page-break-after: always;
            }
            
            .objectives-page:last-child {
                page-break-after: auto;
            }
        }
        """

    def _get_html_template(self) -> str:
        """Return HTML template for objectives pages."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Lesson Plan Objectives - Week of {week_of}</title>
            <style>
                {css}
            </style>
        </head>
        <body>
            {pages}
        </body>
        </html>
        """

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
                    self._extract_from_slot(
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
                # Single-slot: extract directly from day
                self._extract_from_day(
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

    def _extract_from_slot(
        self,
        slot: Dict[str, Any],
        day_name: str,
        week_of: str,
        grade: str,
        homeroom: str,
        room: str,
        teacher_name: str,
        objectives: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """Extract objectives from a slot (multi-slot structure).

        Prioritizes slot-specific metadata over merged metadata.
        """
        unit_lesson = slot.get("unit_lesson", "")
        slot_teacher = get_teacher_name(metadata, slot=slot)

        # Extract slot-specific metadata (prioritize over merged metadata)
        slot_grade = slot.get("grade", grade)
        # Use standardized helper to prevent homeroom leakage
        slot_homeroom = get_homeroom(metadata, slot=slot)
        slot_room = slot.get("room", room)
        slot_time = slot.get("time", "")

        # Get subject using standardized helper (metadata only, no text detection)
        detected_subject = get_subject(metadata, slot=slot)

        # Check if slot has objectives - if not, still include it with empty objectives
        # This ensures slots that appear in DOCX also appear in objectives output
        slot_num = slot.get("slot_number", 0)
        objective_data = normalize_objective_payload(
            slot.get("objective", {}),
            {
                "day": day_name,
                "slot_number": slot_num,
                "subject": detected_subject,
            },
        )
        # If no objective data, create empty structure to include the slot
        if not objective_data:
            logger.debug(
                f"Slot {slot_num} ({day_name}) has no objective data - including with empty objectives"
            )
            objective_data = {
                "content_objective": "",
                "student_goal": "",
                "wida_objective": "",
            }

        # Skip "No School" entries
        if unit_lesson and unit_lesson.strip().lower() == "no school":
            return

        # Check if all objective fields are "No School"
        content_obj = objective_data.get("content_objective", "").strip().lower()
        student_goal = objective_data.get("student_goal", "").strip().lower()
        wida_obj = objective_data.get("wida_objective", "").strip().lower()

        if (
            content_obj == "no school"
            and student_goal == "no school"
            and wida_obj == "no school"
        ):
            return

        objectives.append(
            {
                "week_of": week_of,
                "day": day_name.capitalize(),
                "subject": detected_subject,  # Use detected subject
                "grade": slot_grade if slot_grade and slot_grade != "N/A" else grade,
                "homeroom": slot_homeroom,  # Already uses get_homeroom helper with proper fallback
                "room": slot_room if slot_room and slot_room != "N/A" else room,
                "time": slot_time if slot_time and slot_time != "N/A" else "",
                "teacher_name": slot_teacher,
                "slot_number": slot.get("slot_number", 0),
                "unit_lesson": unit_lesson,
                "content_objective": objective_data.get("content_objective", ""),
                "student_goal": objective_data.get("student_goal", ""),
                "wida_objective": objective_data.get("wida_objective", ""),
            }
        )

    def _extract_from_day(
        self,
        day_data: Dict[str, Any],
        day_name: str,
        week_of: str,
        grade: str,
        homeroom: str,
        room: str,
        metadata: Dict[str, Any],
        subject: str,
        objectives: List[Dict[str, Any]],
    ):
        """Extract objectives from a day (single-slot structure)."""
        # Skip if no objective
        objective_data = normalize_objective_payload(
            day_data.get("objective", {}),
            {
                "day": day_name,
                "subject": subject,
            },
        )
        if not objective_data:
            return

        unit_lesson = day_data.get("unit_lesson", "")

        # Skip "No School" entries
        if unit_lesson and unit_lesson.strip().lower() == "no school":
            return

        # Check if all objective fields are "No School"
        content_obj = objective_data.get("content_objective", "").strip().lower()
        student_goal = objective_data.get("student_goal", "").strip().lower()
        wida_obj = objective_data.get("wida_objective", "").strip().lower()

        if (
            content_obj == "no school"
            and student_goal == "no school"
            and wida_obj == "no school"
        ):
            return

        # Get subject using standardized helper (metadata only, no text detection)
        detected_subject = get_subject(metadata)

        objectives.append(
            {
                "week_of": week_of,
                "day": day_name.capitalize(),
                "subject": detected_subject,  # Use detected subject instead of metadata
                "grade": grade,
                "homeroom": get_homeroom(metadata),  # Use standardized helper
                "room": room if room and room != "N/A" else "",
                "teacher_name": get_teacher_name(metadata),
                "unit_lesson": unit_lesson,
                "content_objective": objective_data.get("content_objective", ""),
                "student_goal": objective_data.get("student_goal", ""),
                "wida_objective": objective_data.get("wida_objective", ""),
            }
        )

    def _get_day_date(self, week_of: str, day_name: str) -> str:
        """Get the date for a specific day of the week using standardized utility."""
        # Get school year from config if available
        config_school_year = None
        if settings.SCHOOL_YEAR_START_YEAR and settings.SCHOOL_YEAR_END_YEAR:
            config_school_year = (
                settings.SCHOOL_YEAR_START_YEAR,
                settings.SCHOOL_YEAR_END_YEAR,
            )

        return get_day_date(week_of, day_name, config_school_year=config_school_year)

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
