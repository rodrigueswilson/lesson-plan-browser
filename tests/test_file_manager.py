"""
Tests for FileManager functionality.
"""

import time
from pathlib import Path
from datetime import datetime
import pytest

from backend.file_manager import FileManager


class TestFileManager:
    """Test FileManager class."""

    def test_get_output_path_basic(self):
        """Test basic output path generation."""
        fm = FileManager()
        
        path = fm.get_output_path(
            week_folder=Path("test_folder"),
            user_name="John Doe",
            week_of="10/6-10/10"
        )
        
        # Check format
        assert "John_Doe" in path
        assert "Lesson_plan" in path
        assert ".docx" in path
        assert "10-6-10-10" in path
        
    def test_get_output_path_spaces_in_name(self):
        """Test that spaces in user name are replaced with underscores."""
        fm = FileManager()
        
        path = fm.get_output_path(
            week_folder=Path("test_folder"),
            user_name="Maria Rodrigues Silva",
            week_of="10/6-10/10"
        )
        
        assert "Maria_Rodrigues_Silva" in path
        assert " " not in Path(path).name  # No spaces in filename
        
    def test_get_output_path_with_timestamp_basic(self):
        """Test timestamped output path generation."""
        fm = FileManager()
        
        path = fm.get_output_path_with_timestamp(
            week_folder=Path("test_folder"),
            user_name="John Doe",
            week_of="10/6-10/10"
        )
        
        # Check format
        assert "John_Doe" in path
        assert "Lesson_plan" in path
        assert ".docx" in path
        assert "10-6-10-10" in path
        
        # Check timestamp is present (YYYYMMDD_HHMMSS format)
        filename = Path(path).name
        # Should have pattern like: Name_Lesson_plan_W##_dates_YYYYMMDD_HHMMSS.docx
        parts = filename.split("_")
        assert len(parts) >= 7  # At least: Name, Lesson, plan, W##, dates, timestamp, timestamp.docx
        
    def test_get_output_path_with_timestamp_uniqueness(self):
        """Test that timestamps make filenames unique."""
        fm = FileManager()
        
        # Generate first path
        path1 = fm.get_output_path_with_timestamp(
            week_folder=Path("test_folder"),
            user_name="John Doe",
            week_of="10/6-10/10"
        )
        
        # Wait a moment to ensure different timestamp
        time.sleep(1.1)
        
        # Generate second path with same parameters
        path2 = fm.get_output_path_with_timestamp(
            week_folder=Path("test_folder"),
            user_name="John Doe",
            week_of="10/6-10/10"
        )
        
        # Paths should be different due to timestamp
        assert path1 != path2
        
        # Both should have valid format
        assert path1.endswith(".docx")
        assert path2.endswith(".docx")
        
    def test_get_output_path_with_timestamp_custom_format(self):
        """Test custom timestamp format."""
        fm = FileManager()
        
        path = fm.get_output_path_with_timestamp(
            week_folder=Path("test_folder"),
            user_name="John Doe",
            week_of="10/6-10/10",
            timestamp_format="%Y%m%d"  # Date only, no time
        )
        
        # Should have date but not time
        filename = Path(path).name
        today = datetime.now().strftime("%Y%m%d")
        assert today in filename
        
    def test_calculate_week_number(self):
        """Test week number calculation."""
        fm = FileManager()
        
        # Test various dates
        test_cases = [
            ("1/1-1/5", 1),      # Week 1 (approx)
            ("10/6-10/10", 40),  # Week 40 (approx)
            ("12/25-12/29", 52), # Week 52 (approx)
        ]
        
        for week_of, expected_week in test_cases:
            week_num = fm._calculate_week_number(week_of)
            # Allow +/- 1 week tolerance due to ISO week calculation
            assert abs(week_num - expected_week) <= 1, \
                f"Week {week_of} calculated as {week_num}, expected ~{expected_week}"
    
    def test_output_path_comparison(self):
        """Compare regular vs timestamped output paths."""
        fm = FileManager()
        week_folder = Path("test_folder")
        user_name = "John Doe"
        week_of = "10/6-10/10"
        
        # Regular path
        regular_path = fm.get_output_path(week_folder, user_name, week_of)
        
        # Timestamped path
        timestamped_path = fm.get_output_path_with_timestamp(
            week_folder, user_name, week_of
        )
        
        # Both should have same base structure
        assert "John_Doe" in regular_path
        assert "John_Doe" in timestamped_path
        assert "Lesson_plan" in regular_path
        assert "Lesson_plan" in timestamped_path
        
        # Timestamped should be longer (has timestamp)
        assert len(timestamped_path) > len(regular_path)
        
        # Regular path should NOT have timestamp pattern
        regular_filename = Path(regular_path).name
        timestamped_filename = Path(timestamped_path).name
        assert len(timestamped_filename) > len(regular_filename)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
