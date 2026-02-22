"""HTML generation for sentence frame pages."""

from __future__ import annotations

import html as html_module
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.config import settings
from backend.telemetry import logger
from backend.utils.metadata_utils import build_document_header, get_day_date


def get_css_template() -> str:
    """Return CSS for sentence frame pages.

    Layout assumptions:
    - Portrait US Letter (8.5" x 11") with no CSS margins (full page usage).
    - Content area: 8.5" wide x 11" tall (full page dimensions).
    - Header: 0.35" tall at the top of each page (positioned 1 cm from top/left for printer safety).
    - Three equal-height panels: each panel is exactly 3.67" tall.
    - Panels use explicit heights (not flexbox) for reliable print output.
    - English-only frames, with a mandatory function label.
    """
    return """
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');

        @page {
            size: 8.5in 11in; /* Portrait US Letter - exact size for printer */
            margin: 0; /* No margins - use full page for maximum space */
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
            width: 8.5in;  /* Full page width */
            height: 11in;  /* Full page height */
            position: relative;
            margin: 0;
            page-break-after: always;
            display: flex;
            flex-direction: column;
        }

        .header {
            position: absolute;
            top: 0.39in; /* 1 cm from top for printer safety */
            left: 0.39in; /* 1 cm from left for printer safety */
            height: 0.35in;
            font-size: 10pt;
            color: #808080; /* 50% gray */
            display: flex;
            align-items: center;
            justify-content: flex-start;
            z-index: 10;
            border: none;
            border-bottom: none;
        }

        .panels {
            position: relative;
            height: 11in;
            display: flex;
            flex-direction: column;
            border-top: none;
        }

        .panel {
            height: 3.67in; /* 11in / 3 */
            box-sizing: border-box;
            padding: 0.25in 0.3in;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            flex-shrink: 0;
            flex-grow: 0;
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

        .frame-text strong {
            font-weight: 700;
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

        .bundle-frame-text strong {
            font-weight: 700;
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
            border-top: 1px solid rgba(128, 128, 128, 0.4);
            z-index: 1;
        }

        .fold-line-1 {
            top: 3.67in;
        }

        .fold-line-2 {
            top: 7.33in;
        }

        @media print {
            .frames-page {
                page-break-after: always;
                width: 8.5in !important;
                height: 11in !important;
            }
            .frames-page:last-child {
                page-break-after: auto;
            }
            .panels {
                height: 11in !important;
            }
            .panel {
                height: 3.67in !important;
                flex-shrink: 0 !important;
                flex-grow: 0 !important;
            }
        }
        """


def get_html_template() -> str:
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


def convert_markdown_to_html(text: str) -> str:
    """Convert markdown bold syntax (**word**) to HTML <strong> tags."""
    text = html_module.escape(text)
    pattern = r"\*\*(.+?)\*\*"
    text = re.sub(pattern, r"<strong>\1</strong>", text)
    return text


def extract_bold_words_from_markdown(text: str) -> Tuple[str, List[str]]:
    """Extract bold words from markdown and return cleaned text with list of bold words."""
    bold_words: List[str] = []
    pattern = r"\*\*([^*]+?)\*\*"
    matches = re.finditer(pattern, text)
    for match in matches:
        bold_words.append(match.group(1))
    cleaned_text = re.sub(pattern, r"\1", text)
    return cleaned_text, bold_words


def pretty_function(label: str) -> str:
    """Format language function label for display."""
    if not label:
        return ""
    text = label.replace("_", " ").strip()
    return text[:1].upper() + text[1:]


def _calculate_day_date(week_of: str, day: str) -> str:
    """Calculate the specific date for a given day in the week."""
    config_school_year = None
    if settings.SCHOOL_YEAR_START_YEAR and settings.SCHOOL_YEAR_END_YEAR:
        config_school_year = (
            settings.SCHOOL_YEAR_START_YEAR,
            settings.SCHOOL_YEAR_END_YEAR,
        )

    full_date = get_day_date(week_of, day, config_school_year=config_school_year)

    if full_date and full_date != week_of:
        try:
            date_obj = datetime.strptime(full_date, "%m/%d/%Y")
            return date_obj.strftime("%m/%d/%y")
        except ValueError:
            return full_date

    return week_of


def build_header_text(payload: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Build standardized header text using metadata_utils helper."""
    week_of = payload.get("week_of", "Unknown")
    day_name = payload.get("day", "Unknown")
    day_date = None
    if week_of and week_of != "Unknown" and day_name and day_name != "Unknown":
        day_date = _calculate_day_date(week_of, day_name)

    slot_dict = None
    if (
        payload.get("subject")
        or payload.get("grade")
        or payload.get("homeroom")
        or payload.get("room")
    ):
        slot_dict = {
            "subject": payload.get("subject"),
            "grade": payload.get("grade"),
            "homeroom": payload.get("homeroom"),
            "room": payload.get("room"),
        }

    return build_document_header(
        metadata=metadata,
        slot=slot_dict,
        day_date=day_date,
        day_name=day_name if day_name != "Unknown" else None,
        include_time=False,
        include_day_name=True,
    )


def _render_page_pair(payload: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Render the two pages (front/back) for a single day's frames."""
    header_text = build_header_text(payload, metadata)

    levels_3_4 = payload.get("levels_3_4") or []
    levels_1_2 = payload.get("levels_1_2") or []
    levels_5_6 = payload.get("levels_5_6") or []

    levels_3_4 = list(levels_3_4)[:3]
    levels_1_2 = list(levels_1_2)[:3]
    levels_5_6 = list(levels_5_6)[:2]

    def _frame_text(frame: Dict[str, Any]) -> Tuple[str, str]:
        english = str(frame.get("english", "")).strip()
        english = convert_markdown_to_html(english)
        func = pretty_function(str(frame.get("language_function", "")).strip())
        return english, func

    page1_panels: List[str] = []
    for idx in range(3):
        english, func = ("", "")
        if idx < len(levels_3_4):
            english, func = _frame_text(levels_3_4[idx])
        panel_html = f"""
                <div class=\"panel panel-{idx + 1}\">
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
                {"".join(page1_panels)}
            </div>
        </div>
        """

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


def build_pages(payloads: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
    """Build full HTML content for all page pairs."""
    css = get_css_template()
    html_tpl = get_html_template()
    pages: List[str] = []
    for payload in payloads:
        pages.append(_render_page_pair(payload, metadata))
    week_of = payloads[0]["week_of"] if payloads else "Unknown"
    return html_tpl.format(css=css, pages="\n".join(pages), week_of=week_of)
