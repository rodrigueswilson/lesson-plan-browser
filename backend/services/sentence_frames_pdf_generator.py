"""HTML + PDF generator for sentence frames with precise layout control.

This module mirrors the ObjectivesPDFGenerator pattern but focuses on
printable, English-only sentence frame sheets (two pages per lesson,
with fold lines and thirds).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.file_manager import get_file_manager
from backend.telemetry import logger


class SentenceFramesPDFGenerator:
    """Generate sentence frames as HTML and convert to PDF for printing."""

    def __init__(self) -> None:
        self.css_template = self._get_css_template()
        self.html_template = self._get_html_template()
        self.file_manager = get_file_manager()
        self._default_output_dir = Path(self.file_manager.base_path)

    # --- Path helpers (mirroring objectives generator) ---

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
                    "sentence_frames_week_folder_resolution_failed",
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
        return f"{teacher_slug}_SentenceFrames_{week_slug}_{timestamp}"

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

    # --- CSS / HTML templates ---

    def _get_css_template(self) -> str:
        """Return CSS for sentence frame pages.

        Layout assumptions:
        - Portrait US Letter with 0.5" margins.
        - Each .frames-page has three equal-height panels, separated by
          two fold lines positioned at 1/3 and 2/3 of the usable height.
        - English-only frames, with a mandatory function label.
        """
        return """
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');

        @page {
            size: 8.5in 11in; /* Portrait US Letter */
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

        .frames-page {
            width: 7.5in;  /* 8.5 - 1" margins */
            height: 10in;  /* 11 - 1" margins */
            position: relative;
            margin: 0 auto 0.25in auto;
            page-break-after: always;
            display: flex;
            flex-direction: column;
        }

        .header {
            height: 0.35in;
            font-size: 10pt;
            color: #808080; /* 50% gray */
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin-bottom: 0;
            border: none;
            border-bottom: none;
        }

        .panels {
            position: relative;
            flex: 1;
            display: flex;
            flex-direction: column;
            border-top: none;
        }

        .panel {
            flex: 1;
            padding: 0.25in 0.3in;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }

        .panel-title {
            font-size: 10pt;
            font-weight: 600;
            color: #808080;
            margin-bottom: 0.1in;
        }

        .frame-text {
            font-size: 28pt;
            font-weight: 600;
            color: #000000;
            line-height: 1.2;
            margin-bottom: 0.1in;
            word-wrap: break-word;
            max-width: 100%;
        }

        .frame-function {
            font-size: 11pt;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #808080;
        }

        .bundle-frame-row {
            margin: 0.05in 0;
        }

        .bundle-frame-text {
            font-size: 18pt;
            font-weight: 600;
            color: #000000;
            line-height: 1.2;
        }

        .bundle-frame-function {
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #808080;
        }

        .fold-line {
            position: absolute;
            left: 0;
            right: 0;
            height: 0;
            border-top: 1px solid #808080; /* Darker gray for better visibility */
            z-index: 1;
        }

        .fold-line-1 {
            top: 33.333%;
        }

        .fold-line-2 {
            top: 66.666%;
        }

        @media print {
            .frames-page {
                page-break-after: always;
            }
            .frames-page:last-child {
                page-break-after: auto;
            }
        }
        """

    def _get_html_template(self) -> str:
        """Return outer HTML template for sentence frame pages."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Sentence Frames - Week of {week_of}</title>
            <style>
                {css}
            </style>
        </head>
        <body>
            {pages}
        </body>
        </html>
        """

    # --- Extraction ---

    def extract_sentence_frames(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sentence frame payloads from lesson JSON, ordered by schedule (day and slot).

        Each item is a dict with metadata and three level buckets:
        - levels_1_2: list of 3 frames
        - levels_3_4: list of 3 frames
        - levels_5_6: list of 2 frames
        
        Frames are ordered by day (Monday-Friday) and then by slot_number to follow schedule order.
        """
        results: List[Dict[str, Any]] = []

        days = lesson_json.get("days") or {}
        if not isinstance(days, dict):
            return results

        metadata = lesson_json.get("metadata", {})
        week_of = metadata.get("week_of", "Unknown")
        default_grade = metadata.get("grade", "Unknown")
        default_subject = metadata.get("subject", "Unknown")
        default_homeroom = metadata.get("homeroom", "Unknown")
        default_teacher_name = metadata.get("teacher_name", "Unknown")

        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]

        for day_name in day_names:
            day_data = days.get(day_name)
            if not isinstance(day_data, dict):
                continue

            # Check if this is a multi-slot structure
            slots = day_data.get("slots") or []
            if isinstance(slots, list) and len(slots) > 0:
                # Multi-slot: process each slot individually, ordered by slot_number
                # Sort slots by slot_number to maintain schedule order
                sorted_slots = sorted(
                    slots,
                    key=lambda s: s.get("slot_number", 0) if isinstance(s, dict) else 0
                )
                
                for slot in sorted_slots:
                    if not isinstance(slot, dict):
                        continue
                    
                    slot_unit_lesson = slot.get("unit_lesson", "")
                    
                    # Skip "No School" entries
                    if slot_unit_lesson and slot_unit_lesson.strip().lower() == "no school":
                        continue
                    
                    # Get slot-specific sentence frames
                    slot_frames = slot.get("sentence_frames") or []
                    if not isinstance(slot_frames, list) or len(slot_frames) == 0:
                        continue
                    
                    # Use slot-specific metadata, fallback to defaults
                    slot_grade = slot.get("grade", default_grade)
                    slot_subject = slot.get("subject", default_subject)
                    slot_homeroom = slot.get("homeroom", default_homeroom)
                    slot_teacher = slot.get("teacher_name", default_teacher_name)
                    
                    # Organize frames by proficiency level
                    levels_1_2: List[Dict[str, Any]] = []
                    levels_3_4: List[Dict[str, Any]] = []
                    levels_5_6: List[Dict[str, Any]] = []
                    
                    for frame in slot_frames:
                        if not isinstance(frame, dict):
                            continue
                        level = frame.get("proficiency_level")
                        if level == "levels_1_2":
                            levels_1_2.append(frame)
                        elif level == "levels_3_4":
                            levels_3_4.append(frame)
                        elif level == "levels_5_6":
                            levels_5_6.append(frame)
                    
                    if not (levels_1_2 or levels_3_4 or levels_5_6):
                        continue
                    
                    results.append(
                        {
                            "week_of": week_of,
                            "day": day_name.capitalize(),
                            "grade": slot_grade if slot_grade and slot_grade != "N/A" else default_grade,
                            "subject": slot_subject if slot_subject and slot_subject != "Unknown" else default_subject,
                            "homeroom": slot_homeroom if slot_homeroom and slot_homeroom != "N/A" else default_homeroom,
                            "teacher_name": slot_teacher if slot_teacher else default_teacher_name,
                            "unit_lesson": slot_unit_lesson,
                            "slot_number": slot.get("slot_number", 0),
                            "levels_1_2": levels_1_2,
                            "levels_3_4": levels_3_4,
                            "levels_5_6": levels_5_6,
                        }
                    )
            else:
                # Single-slot or day-level frames: process day-level frames if present
                day_unit_lesson = day_data.get("unit_lesson", "")
                
                # Skip "No School" entries
                if day_unit_lesson and day_unit_lesson.strip().lower() == "no school":
                    continue
                
                day_level_frames = day_data.get("sentence_frames") or []
                if not isinstance(day_level_frames, list) or len(day_level_frames) == 0:
                    continue
                
                # Organize frames by proficiency level
                levels_1_2: List[Dict[str, Any]] = []
                levels_3_4: List[Dict[str, Any]] = []
                levels_5_6: List[Dict[str, Any]] = []
                
                for frame in day_level_frames:
                    if not isinstance(frame, dict):
                        continue
                    level = frame.get("proficiency_level")
                    if level == "levels_1_2":
                        levels_1_2.append(frame)
                    elif level == "levels_3_4":
                        levels_3_4.append(frame)
                    elif level == "levels_5_6":
                        levels_5_6.append(frame)
                
                if not (levels_1_2 or levels_3_4 or levels_5_6):
                    continue
                
                results.append(
                    {
                        "week_of": week_of,
                        "day": day_name.capitalize(),
                        "grade": default_grade,
                        "subject": default_subject,
                        "homeroom": default_homeroom,
                        "teacher_name": default_teacher_name,
                        "unit_lesson": day_data.get("unit_lesson", ""),
                        "slot_number": 0,
                        "levels_1_2": levels_1_2,
                        "levels_3_4": levels_3_4,
                        "levels_5_6": levels_5_6,
                    }
                )

        return results

    # --- HTML generation ---

    def _calculate_day_date(self, week_of: str, day: str) -> str:
        """Calculate the specific date for a given day in the week.
        
        Args:
            week_of: Week range string like "11/17-11/21" or "11-17-11-21"
            day: Day name like "Monday", "Tuesday", etc.
        
        Returns:
            Formatted date string "MM/DD/YY" (e.g., "11/17/25")
        """
        # Day name to offset mapping
        day_offsets = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
        }
        
        # Normalize day name to match dictionary keys (capitalize first letter)
        normalized_day = day.capitalize() if day else "Monday"
        offset = day_offsets.get(normalized_day, 0)
        
        try:
            # Parse week start date from week_of
            # Handle formats: "11/17-11/21" or "11-17-11-21"
            if "-" in week_of:
                first_part = week_of.split("-")[0].strip()
                # Normalize to MM/DD format
                if "/" in first_part:
                    month, day_str = first_part.split("/")
                elif "-" in first_part:
                    month, day_str = first_part.split("-")
                else:
                    # Fallback: use first date as-is
                    return f"{first_part}/25"
                
                # Create datetime object for week start (assuming 2025)
                start_date = datetime(2025, int(month), int(day_str))
                # Add offset days
                target_date = start_date + timedelta(days=offset)
                # Format as MM/DD/YY
                return target_date.strftime("%m/%d/%y")
            else:
                # Single date format - use as-is
                if "/" in week_of:
                    return f"{week_of}/25"
                else:
                    return f"{week_of}/25"
        except (ValueError, IndexError) as e:
            # Fallback: extract first date and use it
            if "-" in week_of:
                first_date = week_of.split("-")[0].strip()
                if "/" in first_date:
                    return f"{first_date}/25"
                elif "-" in first_date:
                    return f"{first_date.replace('-', '/')}/25"
            return "Unknown"

    def _build_header_text(self, payload: Dict[str, Any]) -> str:
        parts: List[str] = []
        # Date: calculate specific date for this day
        week_of = payload.get("week_of", "Unknown")
        day = payload.get("day", "Unknown")
        if week_of and week_of != "Unknown" and day and day != "Unknown":
            day_date = self._calculate_day_date(week_of, day)
            parts.append(day_date)
        else:
            parts.append("Unknown")

        # Day: add the day name (e.g., "Wednesday")
        day = payload.get("day")
        if day and day != "Unknown":
            parts.append(day)

        # Subject: take only the first subject if multiple are listed
        subject = payload.get("subject")
        if subject and subject != "Unknown":
            # Split by " / " and take the first subject
            if " / " in subject:
                first_subject = subject.split(" / ")[0].strip()
                parts.append(first_subject)
            else:
                parts.append(subject)
        else:
            parts.append("Unknown")

        grade = payload.get("grade")
        if grade and grade != "Unknown":
            parts.append(f"Grade {grade}")

        homeroom = payload.get("homeroom")
        if homeroom and homeroom != "Unknown":
            parts.append(homeroom)

        return " | ".join(parts)

    @staticmethod
    def _pretty_function(label: str) -> str:
        if not label:
            return ""
        text = label.replace("_", " ").strip()
        return text[:1].upper() + text[1:]

    def _render_page_pair(self, payload: Dict[str, Any]) -> str:
        """Render the two pages (front/back) for a single day's frames."""
        header_text = self._build_header_text(payload)

        levels_3_4 = payload.get("levels_3_4") or []
        levels_1_2 = payload.get("levels_1_2") or []
        levels_5_6 = payload.get("levels_5_6") or []

        # Ensure predictable ordering
        levels_3_4 = list(levels_3_4)[:3]
        levels_1_2 = list(levels_1_2)[:3]
        levels_5_6 = list(levels_5_6)[:2]

        # Helper to get safe english/function
        def _frame_text(frame: Dict[str, Any]) -> Tuple[str, str]:
            english = str(frame.get("english", "")).strip()
            func = self._pretty_function(str(frame.get("language_function", "")).strip())
            return english, func

        # Page 1: three Levels 3-4 frames, one per panel
        page1_panels: List[str] = []
        for idx in range(3):
            english, func = ("", "")
            if idx < len(levels_3_4):
                english, func = _frame_text(levels_3_4[idx])
            panel_html = f"""
                <div class=\"panel panel-{idx+1}\">
                    <div class=\"frame-text\">{english}</div>
                    <div class=\"frame-function\">{func}</div>
                </div>
            """
            page1_panels.append(panel_html)

        page1_html = f"""
        <div class=\"frames-page frames-page-1\">
            <div class=\"header\">{header_text}</div>
            <div class=\"panels\">
                <div class=\"fold-line fold-line-1\"></div>
                <div class=\"fold-line fold-line-2\"></div>
                {''.join(page1_panels)}
            </div>
        </div>
        """

        # Page 2: top third = all 1-2 frames, middle/bottom = 5-6 frames
        # Top panel: bundle
        bundle_rows: List[str] = []
        for frame in levels_1_2:
            english, func = _frame_text(frame)
            bundle_rows.append(
                f"""
                <div class=\"bundle-frame-row\">
                    <div class=\"bundle-frame-text\">{english}</div>
                    <div class=\"bundle-frame-function\">{func}</div>
                </div>
                """
            )

        bundle_html = "".join(bundle_rows) if bundle_rows else ""

        # Middle and bottom panels: 5-6 frames
        page2_panel2_text, page2_panel2_func = ("", "")
        page2_panel3_text, page2_panel3_func = ("", "")
        if len(levels_5_6) >= 1:
            page2_panel2_text, page2_panel2_func = _frame_text(levels_5_6[0])
        if len(levels_5_6) >= 2:
            page2_panel3_text, page2_panel3_func = _frame_text(levels_5_6[1])

        page2_html = f"""
        <div class=\"frames-page frames-page-2\">
            <div class=\"header\">{header_text}</div>
            <div class=\"panels\">
                <div class=\"fold-line fold-line-1\"></div>
                <div class=\"fold-line fold-line-2\"></div>
                <div class=\"panel panel-1\">
                    <div class=\"panel-title\">Levels 1-2</div>
                    {bundle_html}
                </div>
                <div class=\"panel panel-2\">
                    <div class=\"panel-title\">Levels 5-6</div>
                    <div class=\"frame-text\">{page2_panel2_text}</div>
                    <div class=\"frame-function\">{page2_panel2_func}</div>
                </div>
                <div class=\"panel panel-3\">
                    <div class=\"panel-title\">Levels 5-6</div>
                    <div class=\"frame-text\">{page2_panel3_text}</div>
                    <div class=\"frame-function\">{page2_panel3_func}</div>
                </div>
            </div>
        </div>
        """

        return page1_html + "\n" + page2_html

    def generate_html(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> str:
        """Generate HTML file with sentence frames pages.

        For now, we generate pages for every day that has sentence_frames.
        Each day contributes a two-page pair (front/back) to the output.
        """
        payloads = self.extract_sentence_frames(lesson_json)
        if not payloads:
            raise ValueError("No sentence_frames found in lesson plan")

        pages: List[str] = []
        for payload in payloads:
            pages.append(self._render_page_pair(payload))

        final_html = self.html_template.format(
            css=self.css_template,
            pages="\n".join(pages),
            week_of=payloads[0]["week_of"],
        )

        output_file = self._resolve_html_path(lesson_json, user_name, output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        logger.info(
            "sentence_frames_html_generated",
            extra={
                "output_path": str(output_file),
                "page_pairs": len(payloads),
                "week_of": payloads[0]["week_of"],
            },
        )

        return str(output_file)


    def convert_to_pdf(self, html_path: str, pdf_path: str) -> str:
        """Convert HTML file to PDF using WeasyPrint with Playwright fallback.

        This mirrors ObjectivesPDFGenerator.convert_to_pdf but uses the
        sentence-frames CSS template.
        """

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
                "sentence_frames_weasyprint_pdf_generated",
                extra={"html_path": str(html_file), "pdf_path": str(pdf_file)},
            )
            return str(pdf_file)
        except Exception as exc:
            logger.warning(
                "sentence_frames_weasyprint_failed",
                extra={
                    "html_path": str(html_file),
                    "pdf_path": str(pdf_file),
                    "error": str(exc),
                },
            )

        # Fallback to Playwright
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            logger.error(
                "sentence_frames_playwright_not_installed", extra={"error": str(exc)}
            )
            raise

        with sync_playwright() as p:  # type: ignore[name-defined]
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{html_file}", wait_until="networkidle")
            page.pdf(path=str(pdf_file), format="Letter", landscape=False, print_background=True)
            browser.close()

        logger.info(
            "sentence_frames_playwright_pdf_generated",
            extra={"html_path": str(html_file), "pdf_path": str(pdf_file)},
        )
        return str(pdf_file)

    def generate_pdf(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
        keep_html: bool = True,
    ) -> str:
        """Generate PDF file with sentence frames (HTML + PDF conversion)."""

        html_path, pdf_path = self._resolve_pdf_and_html_paths(
            lesson_json, user_name, output_path
        )
        generated_html = self.generate_html(
            lesson_json, str(html_path), user_name=user_name
        )
        final_pdf = self.convert_to_pdf(generated_html, str(pdf_path))
        if not keep_html:
            try:
                Path(generated_html).unlink()
            except OSError:
                pass
        return final_pdf


def generate_sentence_frames_html(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
) -> str:
    """Convenience wrapper to generate sentence frames HTML."""
    generator = SentenceFramesPDFGenerator()
    return generator.generate_html(
        lesson_json, output_path=output_path, user_name=user_name
    )


def generate_sentence_frames_pdf(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
    keep_html: bool = True,
) -> str:
    """Convenience wrapper to generate sentence frames PDF from lesson JSON."""
    generator = SentenceFramesPDFGenerator()
    return generator.generate_pdf(lesson_json, output_path, user_name, keep_html)
