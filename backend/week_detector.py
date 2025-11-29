"""
Week Detection Utility for Bilingual Lesson Plan Builder.

Scans user's lesson plan folder to detect available weeks and auto-fill dates.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from backend.telemetry import logger


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
        
        # Sort by most recent (parse dates and sort)
        weeks.sort(key=lambda x: parse_week_for_sorting(x['week_of']), reverse=True)
        
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
        "10-06-10-10" -> "10-06-10-10"
        "Week 10-06" -> None (need to scan files)
    """
    # Pattern 1: YY W## (e.g., "25 W43")
    iso_pattern = r'(\d{2})\s+W(\d{1,2})'
    match = re.search(iso_pattern, folder_name)
    
    if match:
        year_short, week_num = match.groups()
        year = 2000 + int(year_short)
        week = int(week_num)
        
        # Convert ISO week to date range (Monday to Friday)
        try:
            # Get Monday of the ISO week
            from datetime import datetime, timedelta
            jan_4 = datetime(year, 1, 4)
            week_start = jan_4 + timedelta(days=-jan_4.weekday(), weeks=week-1)
            monday = week_start
            friday = monday + timedelta(days=4)
            
            # Format as MM-DD-MM-DD
            return f"{monday.month:02d}-{monday.day:02d}-{friday.month:02d}-{friday.day:02d}"
        except Exception as e:
            logger.error(f"Error converting ISO week {year} W{week}: {e}")
            return None
    
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


def parse_week_for_sorting(week_str: str) -> datetime:
    """
    Parse MM-DD-MM-DD format to datetime for sorting.
    
    Uses current year for sorting. Handles year boundary.
    """
    try:
        parts = week_str.split('-')
        if len(parts) != 4:
            return datetime.min
        
        month1, day1 = int(parts[0]), int(parts[1])
        
        # Use current year
        current_year = datetime.now().year
        
        # Handle year boundary (e.g., December to January)
        return datetime(current_year, month1, day1)
        
    except Exception:
        return datetime.min


def format_week_display(week_info: Dict[str, str]) -> str:
    """
    Format week info for display in dropdown.
    
    Args:
        week_info: Dict with 'week_of' and 'folder_name'
        
    Returns:
        Display string like "W43 (10-06 to 10-10)" or "10-06 to 10-10"
    """
    week_of = week_info['week_of']
    folder_name = week_info.get('folder_name', '')
    
    # Extract week number from folder name if present (e.g., "25 W43")
    week_match = re.search(r'W(\d{1,2})', folder_name)
    week_label = f"W{week_match.group(1)}" if week_match else ""
    
    try:
        parts = week_of.split('-')
        if len(parts) == 4:
            start = f"{parts[0]}/{parts[1]}"
            end = f"{parts[2]}/{parts[3]}"
            
            if week_label:
                return f"{week_label} ({start}-{end})"
            else:
                return f"{start} to {end}"
    except Exception:
        pass
    
    return week_of
