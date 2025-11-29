"""
File Manager for dynamic week-based folder structure.
Handles auto-detection of primary teacher files based on patterns.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.telemetry import logger


class FileManager:
    """Manages week-based folder structure and file detection."""

    def __init__(self, base_path: str = None):
        """
        Initialize file manager.

        Args:
            base_path: Base path for lesson plans (e.g., F:/path/to/Lesson Plan)
                      If None, reads from environment or uses default
        """
        self.base_path = Path(
            base_path
            or os.getenv(
                "LESSON_PLAN_BASE_PATH", r"F:/rodri/Documents/OneDrive/AS/Lesson Plan"
            )
        )

    def get_week_folder(self, week_of: str) -> Path:
        """
        Get folder path for a specific week.
        Uses most recent week folder if available, otherwise calculates from date.

        Args:
            week_of: Week date range (MM/DD-MM/DD) or None to use most recent

        Returns:
            Path to week folder (e.g., F:/path/to/25 W41)
        """
        # If week_of is provided, try to find matching folder
        if week_of:
            week_num = self._calculate_week_number(week_of)
            year = datetime.now().strftime("%y")

            # Try current year first
            folder_name = f"{year} W{week_num:02d}"
            folder_path = self.base_path / folder_name

            if folder_path.exists():
                return folder_path

            # Try other year formats
            for y in ["22", "23", "24", "25", "26", "27"]:
                folder_name = f"{y} W{week_num:02d}"
                folder_path = self.base_path / folder_name
                if folder_path.exists():
                    return folder_path

        # If not found or no week_of provided, use most recent week folder
        available_weeks = self.get_available_weeks(limit=1)
        if available_weeks:
            most_recent = available_weeks[0]
            logger.info(
                "week_folder_fallback",
                extra={"folder_name": most_recent["folder_name"]},
            )
            return Path(most_recent["path"])

        # Fallback: return expected path (will be created if needed)
        year = datetime.now().strftime("%y")
        week_num = self._calculate_week_number(week_of) if week_of else 1
        return self.base_path / f"{year} W{week_num:02d}"

    def _should_skip_file(self, filename: str) -> bool:
        """
        Check if file should be skipped.

        Args:
            filename: Filename to check

        Returns:
            True if file should be skipped
        """
        filename_lower = filename.lower()

        skip_patterns = [
            "~",  # Temp files
            "rodrigues",  # Maria's output files
            "silva",  # Daniela's output files
            "old ",  # Old versions
            "template",  # Templates
            "copy of",  # Copies
            "lesson plan template",  # Templates
            "with comments",  # Commented versions
        ]

        for pattern in skip_patterns:
            if pattern in filename_lower:
                return True

        return False

    def find_primary_teacher_file(
        self, week_folder: Path, teacher_pattern: str, subject: Optional[str] = None
    ) -> Optional[str]:
        """
        Find primary teacher's file in week folder with enhanced matching.

        Args:
            week_folder: Path to week folder
            teacher_pattern: Teacher name or pattern to match (e.g., "Davies", "Savoca", "Wilson Rodrigues")
            subject: Optional subject to help narrow search

        Returns:
            Full path to matched file, or None if not found
        """
        if not week_folder.exists():
            return None

        # Handle None or empty teacher pattern
        if not teacher_pattern:
            return None

        candidates = []
        teacher_lower = teacher_pattern.lower().strip()
        
        # Extract first and last name if pattern contains a space
        name_parts = teacher_lower.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else teacher_lower

        # Try with common prefixes and variations
        patterns_to_try = [
            teacher_pattern,  # Full name as-is
            f"Ms. {teacher_pattern}",
            f"Mr. {teacher_pattern}",
            f"Mrs. {teacher_pattern}",
            last_name,  # Try just last name
            f"Ms. {last_name}",
            f"Mr. {last_name}",
            f"Mrs. {last_name}",
        ]
        
        # If we have both first and last name, try last name first format
        if len(name_parts) > 1:
            patterns_to_try.extend([
                f"{last_name}, {first_name}",
                f"{last_name}, {first_name[0]}",  # Last, FirstInitial
                f"{last_name}_{first_name}",  # With underscore
                f"{first_name}_{last_name}",  # With underscore (first_last)
            ])

        for file in week_folder.glob("*.docx"):
            # Skip excluded files
            if self._should_skip_file(file.name):
                continue

            filename_lower = file.name.lower()

            # Check if any pattern matches
            for pattern in patterns_to_try:
                pattern_lower = pattern.lower()
                if pattern_lower in filename_lower:
                    score = 0

                    # Bonus points for subject match
                    if subject and subject.lower() in filename_lower:
                        score += 10

                    # Bonus for exact teacher name match (word boundary)
                    if f" {teacher_lower} " in f" {filename_lower} ":
                        score += 5
                    
                    # Bonus for last name match (word boundary)
                    if len(name_parts) > 1 and f" {last_name} " in f" {filename_lower} ":
                        score += 4

                    # Bonus for teacher name at start
                    if filename_lower.startswith(pattern_lower) or filename_lower.startswith(f"ms. {pattern_lower}"):
                        score += 3
                    
                    # Bonus for exact pattern match
                    if pattern_lower == teacher_lower:
                        score += 2

                    candidates.append((score, str(file)))
                    break

        # Return highest scoring match
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            return candidates[0][1]

        return None

    def list_primary_teacher_files(self, week_folder: Path) -> List[Dict[str, str]]:
        """
        List all potential primary teacher files in week folder.

        Args:
            week_folder: Path to week folder

        Returns:
            List of dicts with file info (name, path, size, modified)
        """
        if not week_folder.exists():
            return []

        files = []
        for file in week_folder.glob("*.docx"):
            # Skip excluded files
            if self._should_skip_file(file.name):
                continue

            files.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        file.stat().st_mtime
                    ).isoformat(),
                }
            )

        return sorted(files, key=lambda x: x["modified"], reverse=True)

    def get_output_path(self, week_folder: Path, user_name: str, week_of: str) -> str:
        """
        Generate output file path for combined lesson plan.

        Args:
            week_folder: Path to week folder
            user_name: User's name
            week_of: Week date range (MM/DD-MM/DD)

        Returns:
            Full path for output file
        """
        week_num = self._calculate_week_number(week_of)

        # Clean user name (replace spaces with underscores)
        clean_name = user_name.replace(" ", "_")

        # Format dates consistently (MM-DD-MM-DD)
        dates = week_of.replace("/", "-")

        # Consistent filename format
        filename = f"{clean_name}_Lesson_plan_W{week_num:02d}_{dates}.docx"

        # Ensure week folder exists
        week_folder.mkdir(parents=True, exist_ok=True)

        return str(week_folder / filename)

    def get_output_path_with_timestamp(
        self,
        week_folder: Path,
        user_name: str,
        week_of: str,
        timestamp_format: str = "%Y%m%d_%H%M%S"
    ) -> str:
        """
        Generate timestamped output file path for combined lesson plan.
        Prevents file overwrites by adding unique timestamp to filename.

        Args:
            week_folder: Path to week folder
            user_name: User's name
            week_of: Week date range (MM/DD-MM/DD)
            timestamp_format: strftime format for timestamp (default: YYYYMMDD_HHMMSS)

        Returns:
            Full path for timestamped output file

        Example:
            >>> fm = FileManager()
            >>> path = fm.get_output_path_with_timestamp(
            ...     Path("F:/Lesson Plan/25 W41"),
            ...     "Maria Rodrigues",
            ...     "10/6-10/10"
            ... )
            >>> # Returns: "F:/Lesson Plan/25 W41/Maria_Rodrigues_Lesson_plan_W41_10-6-10-10_20251018_153045.docx"
        """
        week_num = self._calculate_week_number(week_of)

        # Clean user name (replace spaces with underscores)
        clean_name = user_name.replace(" ", "_")

        # Format dates consistently (MM-DD-MM-DD)
        dates = week_of.replace("/", "-")

        # Generate timestamp
        timestamp = datetime.now().strftime(timestamp_format)

        # Timestamped filename format
        filename = f"{clean_name}_Lesson_plan_W{week_num:02d}_{dates}_{timestamp}.docx"

        # Ensure week folder exists
        week_folder.mkdir(parents=True, exist_ok=True)

        return str(week_folder / filename)

    def _calculate_week_number(self, week_of: str) -> int:
        """
        Calculate week number from date range.

        Args:
            week_of: Week date range (MM/DD-MM/DD or MM-DD-MM-DD)

        Returns:
            Week number (1-52)
        """
        try:
            # Handle both formats: MM/DD-MM/DD and MM-DD-MM-DD
            # Split by the middle separator to get first date
            if "/" in week_of:
                # Format: MM/DD-MM/DD
                first_date = week_of.split("-")[0].strip()
                month, day = map(int, first_date.split("/"))
            else:
                # Format: MM-DD-MM-DD (split into 4 parts)
                parts = week_of.split("-")
                if len(parts) >= 2:
                    month, day = int(parts[0]), int(parts[1])
                else:
                    return 1

            # Create date object (use current year)
            year = datetime.now().year
            date_obj = datetime(year, month, day)

            # Calculate week number (ISO week)
            week_num = date_obj.isocalendar()[1]

            return week_num
        except (ValueError, IndexError):
            return 1

    def ensure_week_folder_exists(self, week_of: str) -> Path:
        """
        Ensure week folder exists, create if needed.

        Args:
            week_of: Week date range (MM/DD-MM/DD)

        Returns:
            Path to week folder
        """
        week_folder = self.get_week_folder(week_of)
        week_folder.mkdir(parents=True, exist_ok=True)
        return week_folder

    def validate_base_path(self) -> bool:
        """
        Check if base path exists and is accessible.

        Returns:
            True if valid, False otherwise
        """
        return self.base_path.exists() and self.base_path.is_dir()

    def get_available_weeks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of available week folders.

        Args:
            limit: Maximum number of weeks to return

        Returns:
            List of week folder info
        """
        if not self.base_path.exists():
            return []

        weeks = []
        pattern = re.compile(r"(\d{2})\s+W(\d{2})")

        for folder in self.base_path.iterdir():
            if folder.is_dir():
                match = pattern.match(folder.name)
                if match:
                    year, week = match.groups()
                    weeks.append(
                        {
                            "folder_name": folder.name,
                            "path": str(folder),
                            "year": f"20{year}",
                            "week": int(week),
                            "file_count": len(list(folder.glob("*.docx"))),
                        }
                    )

        # Sort by year and week (newest first)
        weeks.sort(key=lambda x: (x["year"], x["week"]), reverse=True)

        return weeks[:limit]


# Global instance
_file_manager: Optional[FileManager] = None


def get_file_manager(base_path: str = None) -> FileManager:
    """
    Get or create global file manager instance.

    Args:
        base_path: Optional base path override

    Returns:
        FileManager instance
    """
    global _file_manager
    if _file_manager is None or base_path:
        _file_manager = FileManager(base_path)
    return _file_manager
