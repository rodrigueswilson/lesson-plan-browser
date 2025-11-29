"""
HTML + PDF generator for lesson plan objectives with precise layout control.

This module provides an alternative to DOCX generation for objectives,
offering pixel-perfect control over text positioning and page layout.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.file_manager import get_file_manager
from backend.services.objectives_utils import normalize_objective_payload
from backend.telemetry import logger


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
        teacher = user_name or metadata.get("teacher_name") or "Teacher"
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
        teacher_name = metadata.get("teacher_name", "Unknown")

        days = lesson_json["days"]
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]

        for day_name in day_names:
            if day_name not in days:
                continue

            day_data = days[day_name]

            # Check if this is a multi-slot structure
            if "slots" in day_data and isinstance(day_data["slots"], list):
                # Multi-slot: iterate through slots
                for slot in day_data["slots"]:
                    self._extract_from_slot(
                        slot,
                        day_name,
                        week_of,
                        grade,
                        homeroom,
                        teacher_name,
                        objectives,
                    )
            else:
                # Single-slot: extract directly from day
                self._extract_from_day(
                    day_data,
                    day_name,
                    week_of,
                    grade,
                    homeroom,
                    teacher_name,
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
        teacher_name: str,
        objectives: List[Dict[str, Any]],
    ):
        """Extract objectives from a slot (multi-slot structure).

        Prioritizes slot-specific metadata over merged metadata.
        """
        unit_lesson = slot.get("unit_lesson", "")
        slot_subject = slot.get("subject", "Unknown")
        slot_teacher = slot.get("teacher_name", teacher_name)

        # Extract slot-specific metadata (prioritize over merged metadata)
        slot_grade = slot.get("grade", grade)
        slot_homeroom = slot.get("homeroom", homeroom)
        slot_time = slot.get("time", "")

        # Skip if no objective
        objective_data = normalize_objective_payload(
            slot.get("objective", {}),
            {
                "day": day_name,
                "slot_number": slot.get("slot_number"),
                "subject": slot_subject,
            },
        )
        if not objective_data:
            return

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

        # *** THE FIX: Prioritize slot subject over detection ***
        # Only use detection if slot subject is Unknown/missing but we have content
        detected_subject = "Unknown"

        if slot_subject and slot_subject != "Unknown":
            detected_subject = slot_subject
        elif unit_lesson and unit_lesson.strip():
            # Only try to detect if we don't have a valid slot subject
            detected_subject = extract_subject_from_unit_lesson(unit_lesson)

            # If detection failed but we have content, fallback to "Unknown"
            # (or could fallback to metadata subject if we wanted, but slot_subject was already checked)
            if detected_subject == "Unknown":
                detected_subject = "Unknown"
        else:
            detected_subject = "Unknown"

        objectives.append(
            {
                "week_of": week_of,
                "day": day_name.capitalize(),
                "subject": detected_subject,  # Use detected subject
                "grade": slot_grade if slot_grade and slot_grade != "N/A" else grade,
                "homeroom": slot_homeroom
                if slot_homeroom and slot_homeroom != "N/A"
                else homeroom,
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
        teacher_name: str,
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

        # *** THE FIX: Prioritize metadata subject over detection ***
        detected_subject = "Unknown"

        if subject and subject != "Unknown":
            detected_subject = subject
        elif unit_lesson and unit_lesson.strip():
            detected_subject = extract_subject_from_unit_lesson(unit_lesson)

            if detected_subject == "Unknown":
                detected_subject = "Unknown"
        else:
            detected_subject = "Unknown"

        objectives.append(
            {
                "week_of": week_of,
                "day": day_name.capitalize(),
                "subject": detected_subject,  # Use detected subject instead of metadata
                "grade": grade,
                "homeroom": homeroom,
                "teacher_name": teacher_name,
                "unit_lesson": unit_lesson,
                "content_objective": objective_data.get("content_objective", ""),
                "student_goal": objective_data.get("student_goal", ""),
                "wida_objective": objective_data.get("wida_objective", ""),
            }
        )

    def _get_day_date(self, week_of: str, day_name: str) -> str:
        """Get the date for a specific day of the week."""
        import re
        from datetime import timedelta

        # Parse week_of date range (e.g., "11/17-11/21" or "11-17-11-21")
        # Try slash format first
        match = re.search(r"(\d{1,2})/(\d{1,2})-", week_of)
        if not match:
            # Try dash format
            match = re.search(r"(\d{1,2})-(\d{1,2})-", week_of)

        if not match:
            return week_of

        month, day = match.groups()
        current_year = datetime.now().year

        try:
            monday_date = datetime(current_year, int(month), int(day))
            # If date is in the future, assume previous year
            if monday_date > datetime.now():
                monday_date = datetime(current_year - 1, int(month), int(day))

            day_index = ["monday", "tuesday", "wednesday", "thursday", "friday"].index(
                day_name.lower()
            )
            target_date = monday_date + timedelta(days=day_index)
            return target_date.strftime("%m/%d/%Y")
        except ValueError:
            return week_of

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

            header_parts = [day_date]
            if obj.get("time"):
                header_parts.append(obj["time"])
            header_parts.append(obj["subject"])
            if obj.get("grade") and obj["grade"] != "Unknown":
                header_parts.append(f"Grade {obj['grade']}")
            if obj.get("homeroom") and obj["homeroom"] != "Unknown":
                header_parts.append(obj["homeroom"])

            header_text = " | ".join(header_parts)

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
