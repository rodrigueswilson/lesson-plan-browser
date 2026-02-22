"""
CSS/HTML templates and day-date helper for objectives PDF generation.

Extracted from objectives_pdf_generator to keep the generator slim.
"""

from __future__ import annotations

from backend.config import settings
from backend.utils.metadata_utils import get_day_date


def get_css_template() -> str:
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


def get_html_template() -> str:
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


def get_day_date_for_objectives(week_of: str, day_name: str) -> str:
    """Get the date for a specific day of the week using standardized utility."""
    config_school_year = None
    if settings.SCHOOL_YEAR_START_YEAR and settings.SCHOOL_YEAR_END_YEAR:
        config_school_year = (
            settings.SCHOOL_YEAR_START_YEAR,
            settings.SCHOOL_YEAR_END_YEAR,
        )
    return get_day_date(week_of, day_name, config_school_year=config_school_year)
