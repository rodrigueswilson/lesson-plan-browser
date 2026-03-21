"""
Week Detection Utility for Bilingual Lesson Plan Builder.

Scans user's lesson plan folder to detect available weeks and auto-fill dates.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from backend.telemetry import logger
from backend.utils.date_formatter import parse_iso_year_week_string_to_hyphen_range


def detect_weeks_from_folder(base_path: str, limit: int = 3) -> List[Dict[str, str]]:
    """
    Scan folder for week subfolders and detect date ranges.
    
    Args:
        base_path: Path to lesson plan folder (e.g., F:/rodri/Documents/OneDrive/AS/Lesson Plan)
        limit: Maximum number of recent weeks to return
        
    Returns:
        List of dicts with 'week_of' (MM-DD-MM-DD format) and 'folder_path'
    """
    try:
        base = Path(base_path)
        logger.info(f"Scanning for weeks in: {base_path}")
        
        if not base.exists():
            logger.warning(f"Base path does not exist: {base_path}")
            return []
        
        weeks = []
        folder_count = 0
        
        # Look for week folders (various naming patterns)
        # Examples: "25 W43", "10-06-10-10", "Week of 10-06"
        for folder in base.iterdir():
            folder_count += 1
            if not folder.is_dir():
                logger.debug(f"Skipping non-directory: {folder.name}")
                continue
            
            logger.info(f"Checking folder: {folder.name}")
            
            # Try to extract dates from folder name
            week_dates = extract_week_dates_from_folder_name(folder.name)
            
            if week_dates:
                logger.info(f"Extracted dates from folder name '{folder.name}': {week_dates}")
            else:
                logger.debug(f"No dates in folder name '{folder.name}', scanning files...")
                # If not in folder name, scan files inside
                week_dates = extract_week_dates_from_files(folder)
                if week_dates:
                    logger.info(f"Extracted dates from files in '{folder.name}': {week_dates}")
            
            if week_dates:
                weeks.append({
                    'week_of': week_dates,
                    'folder_path': str(folder),
                    'folder_name': folder.name
                })
        
        logger.info(f"Scanned {folder_count} items, found {len(weeks)} week folders")
        
        # Sort by most recent (parse dates and sort, using folder name for year if available)
        weeks.sort(key=lambda x: parse_week_for_sorting(x['week_of'], x.get('folder_name', '')), reverse=True)
        
        return weeks[:limit]
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error detecting weeks: {e}", exc_info=True)
        logger.error(f"Traceback: {error_trace}")
        raise  # Re-raise to get better error message in API


def extract_week_dates_from_folder_name(folder_name: str) -> Optional[str]:
    """
    Extract MM-DD-MM-DD format from folder name.
    
    Examples:
        "25 W43" -> Calculates dates for week 43 of 2025
        "26 W02" -> Calculates dates for week 2 of 2026
        "10-06-10-10" -> "10-06-10-10"
        "Week 10-06" -> None (need to scan files)
    """
    # Pattern 1: YY W## (e.g., "25 W43", "26 W02", "25W43", "25 W 43")
    result = parse_iso_year_week_string_to_hyphen_range(folder_name)
    if result:
        logger.debug(f"Converted '{folder_name}' (YY W##) to dates: {result}")
        return result

    # Pattern 2: MM-DD-MM-DD (direct format)
    date_pattern = r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})'
    match = re.search(date_pattern, folder_name)
    
    if match:
        m1, d1, m2, d2 = match.groups()
        return f"{m1.zfill(2)}-{d1.zfill(2)}-{m2.zfill(2)}-{d2.zfill(2)}"
    
    return None


def extract_week_dates_from_files(folder: Path) -> Optional[str]:
    """
    Scan files in folder to detect week date range.
    
    Looks for 5 weekday files (Monday-Friday) and extracts dates.
    Assumes files contain dates in format: MM-DD or MM_DD
    
    Args:
        folder: Path to week folder
        
    Returns:
        Week range in MM-DD-MM-DD format (Monday to Friday)
    """
    try:
        # Get all .docx files
        docx_files = list(folder.glob("*.docx"))
        
        if len(docx_files) < 5:
            return None
        
        # Extract dates from filenames
        dates = []
        date_pattern = r'(\d{1,2})[-_](\d{1,2})'
        
        for file in docx_files:
            match = re.search(date_pattern, file.name)
            if match:
                month, day = match.groups()
                dates.append((int(month), int(day)))
        
        if len(dates) < 5:
            return None
        
        # Sort dates to find Monday (first) and Friday (last)
        dates.sort()
        
        # Assume first 5 dates are the weekdays
        monday = dates[0]
        friday = dates[4] if len(dates) >= 5 else dates[-1]
        
        # Format as MM-DD-MM-DD
        return f"{monday[0]:02d}-{monday[1]:02d}-{friday[0]:02d}-{friday[1]:02d}"
        
    except Exception as e:
        logger.error(f"Error extracting dates from files in {folder}: {e}")
        return None


def parse_week_for_sorting(week_str: str, folder_name: str = '') -> datetime:
    """
    Parse MM-DD-MM-DD format to datetime for sorting.
    
    If folder_name contains YY W## pattern, extract year from folder name.
    Otherwise, handle year boundary by detecting if date is likely in next year.
    
    Args:
        week_str: Week date string in MM-DD-MM-DD format
        folder_name: Optional folder name (e.g., "26 W02") to extract year from
    """
    try:
        parts = week_str.split('-')
        if len(parts) != 4:
            return datetime.min
        
        month1, day1 = int(parts[0]), int(parts[1])
        
        # Try to extract year from folder name first (most accurate)
        if folder_name:
            year_match = re.search(r'^(\d{2})\s*W\s*\d{1,2}\b', folder_name, re.IGNORECASE)
            if year_match:
                year_short = year_match.group(1)
                year = 2000 + int(year_short)
                return datetime(year, month1, day1)
        
        # Fallback: infer year from current date and month
        current_date = datetime.now()
        current_year = current_date.year
        
        # Handle year boundary: if we're in December and see January dates,
        # assume they're for next year. Otherwise use current year.
        # This handles the transition from 2025 to 2026 correctly.
        if current_date.month == 12 and month1 <= 2:
            # We're in December, and seeing Jan/Feb dates - likely next year
            year = current_year + 1
        elif current_date.month == 1 and month1 == 12:
            # We're in January, and seeing December dates - likely previous year
            year = current_year - 1
        else:
        # Use current year
            year = current_year
        
        return datetime(year, month1, day1)
        
    except Exception:
        return datetime.min


def _parse_week_of(week_of: str):
    """
    Parse week_of to (m1, d1, m2, d2) for start and end month/day.
    Handles both MM-DD-MM-DD and MM/DD-MM/DD formats.
    Returns None if parsing fails.
    """
    if not week_of:
        return None
    parts = week_of.split('-')
    if len(parts) == 4:
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            pass
    if len(parts) == 2:
        try:
            start = parts[0].split('/')
            end = parts[1].split('/')
            if len(start) == 2 and len(end) == 2:
                return (int(start[0]), int(start[1]), int(end[0]), int(end[1]))
        except ValueError:
            pass
    return None


def _iso_week_from_week_of(week_of: str) -> Optional[int]:
    """Get ISO week number from week_of (MM-DD-MM-DD or MM/DD-MM/DD). Infers year from current date."""
    parsed = _parse_week_of(week_of)
    if parsed is None:
        return None
    month, day = parsed[0], parsed[1]
    now = datetime.now()
    year = now.year
    if now.month == 12 and month <= 2:
        year = now.year + 1
    elif now.month == 1 and month == 12:
        year = now.year - 1
    try:
        d = datetime(year, month, day)
        _, iso_week, _ = d.isocalendar()
        return iso_week
    except ValueError:
        return None


def format_week_display(week_info: Dict[str, str]) -> str:
    """
    Format week info for display in dropdown.

    Args:
        week_info: Dict with 'week_of' and 'folder_name'

    Returns:
        Display string like "W12 03/16-03/20"
    """
    week_of = week_info['week_of']
    folder_name = week_info.get('folder_name', '')

    week_label = ""
    week_match = re.search(r'W(\d{1,2})', folder_name)
    if week_match:
        week_label = f"W{int(week_match.group(1)):02d}"
    else:
        w = _iso_week_from_week_of(week_of)
        if w is not None:
            week_label = f"W{w:02d}"

    parsed = _parse_week_of(week_of)
    if parsed is not None:
        m1, d1, m2, d2 = parsed
        start = f"{m1:02d}/{d1:02d}"
        end = f"{m2:02d}/{d2:02d}"
        date_range = f"{start}-{end}"
        return f"{week_label} {date_range}".strip() if week_label else date_range

    return week_of
