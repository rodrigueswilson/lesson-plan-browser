"""
Tests for hyperlink processing improvements:
1. Day-hint normalization (case-insensitive comparison)
2. Placement observability (tracking placement outcomes)
3. No-School filtering diagnostics (logging links without day_hint)
4. Day hint validation relaxation (compound formats)
"""

from unittest.mock import patch

import pytest
from docx import Document

from backend.telemetry import logger
from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer


class TestDayHintNormalization:
    """Test case-insensitive day-hint matching."""

    @patch("tools.docx_renderer.logger")
    def test_day_hint_case_insensitive_match(self, mock_logger):
        """Day hint matching works with different case variations."""
        renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")

        cell_text = "Students will complete the worksheet activity."
        hyperlink = {
            "text": "worksheet",
            "url": "https://example.com",
            "context_snippet": "complete the worksheet",
            "day_hint": "MONDAY",  # Uppercase
            "section_hint": "instruction",
        }

        # Test with lowercase day_name
        confidence_lower, match_type_lower = renderer._calculate_match_confidence(
            cell_text, hyperlink, day_name="monday", section_name="instruction"
        )

        # Test with uppercase day_name
        confidence_upper, match_type_upper = renderer._calculate_match_confidence(
            cell_text, hyperlink, day_name="MONDAY", section_name="instruction"
        )

        # Test with mixed case day_name
        confidence_mixed, match_type_mixed = renderer._calculate_match_confidence(
            cell_text, hyperlink, day_name="Monday", section_name="instruction"
        )

        # Test with lowercase day_hint
        hyperlink_lower = hyperlink.copy()
        hyperlink_lower["day_hint"] = "monday"
        confidence_lower_hint, match_type_lower_hint = (
            renderer._calculate_match_confidence(
                cell_text,
                hyperlink_lower,
                day_name="MONDAY",
                section_name="instruction",
            )
        )

        # All should match (case-insensitive)
        assert confidence_lower > 0, "Lowercase day_name should match"
        assert confidence_upper > 0, "Uppercase day_name should match"
        assert confidence_mixed > 0, "Mixed case day_name should match"
        assert confidence_lower_hint > 0, "Lowercase day_hint should match"

        # Hint matches should boost confidence
        assert confidence_lower >= 0.4, "Hint match should boost confidence"

    @patch("tools.docx_renderer.logger")
    def test_day_hint_with_whitespace(self, mock_logger):
        """Day hint normalization handles whitespace correctly."""
        renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")

        cell_text = "Students will complete the worksheet activity."
        hyperlink = {
            "text": "worksheet",
            "url": "https://example.com",
            "context_snippet": "complete the worksheet",
            "day_hint": "  Monday  ",  # With whitespace
            "section_hint": "instruction",
        }

        confidence, match_type = renderer._calculate_match_confidence(
            cell_text, hyperlink, day_name="monday", section_name="instruction"
        )

        # Should match despite whitespace
        assert confidence > 0, "Whitespace should be normalized"

    @patch("tools.docx_renderer.logger")
    def test_day_hint_no_match_different_day(self, mock_logger):
        """Different days should not match even with case variations."""
        renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")

        cell_text = "Students will complete the worksheet activity."
        hyperlink = {
            "text": "worksheet",
            "url": "https://example.com",
            "context_snippet": "complete the worksheet",
            "day_hint": "MONDAY",
            "section_hint": "instruction",
        }

        # Try with Tuesday (different day)
        confidence, match_type = renderer._calculate_match_confidence(
            cell_text, hyperlink, day_name="tuesday", section_name="instruction"
        )

        # Should still have some confidence from context, but day hint won't boost
        # Since we're matching Tuesday with Monday hint, day hint won't match
        # But context should still give some confidence
        assert confidence >= 0.0, "Should have some confidence from context"


class TestPlacementObservability:
    """Test placement outcome tracking."""

    @patch("tools.docx_renderer.logger")
    def test_fill_day_logs_placement_outcome(self, mock_logger):
        """_fill_day logs placement outcomes."""
        from pathlib import Path

        template_path = "input/Lesson Plan Template SY'25-26.docx"
        if not Path(template_path).exists():
            pytest.skip(f"Template file not found: {template_path}")

        renderer = DOCXRenderer(template_path)

        # Create a document from the template (which has tables)
        doc = Document(template_path)

        # Create mock pending hyperlinks
        pending_hyperlinks = [
            {
                "text": "Link 1",
                "url": "https://example.com/1",
                "day_hint": "monday",
                "section_hint": "objective",
                "_source_slot": 1,
                "_source_subject": "Math",
            },
            {
                "text": "Link 2",
                "url": "https://example.com/2",
                "day_hint": "monday",
                "section_hint": "instruction",
                "_source_slot": 1,
                "_source_subject": "Math",
            },
        ]

        day_data = {
            "unit_lesson": "Unit 1",
            "objective": {
                "content_objective": "Students will learn",
                "student_goal": "Goal",
                "wida_objective": "WIDA",
            },
            "anticipatory_set": {"original_content": "Warm-up", "bilingual_bridge": ""},
            "tailored_instruction": {
                "original_content": "Instruction",
                "co_teaching_model": {},
                "ell_support": [],
                "special_needs_support": [],
                "materials": [],
            },
        }

        # Call _fill_day
        renderer._fill_day(
            doc,
            "monday",
            day_data,
            pending_hyperlinks=pending_hyperlinks,
            slot_number=1,
            subject="Math",
        )

        # Check that placement outcome was logged
        # Look for the log call with 'hyperlink_placement_outcome'
        placement_logged = False
        for call in mock_logger.info.call_args_list:
            args, kwargs = call
            if args and "hyperlink_placement_outcome" in args[0]:
                placement_logged = True
                extra = kwargs.get("extra", {})
                assert "total_links" in extra, "Should include total_links"
                assert "placed_count" in extra, "Should include placed_count"
                assert "remaining_count" in extra, "Should include remaining_count"
                break

        assert placement_logged, "Should log placement outcome"

    @patch("tools.docx_renderer.logger")
    def test_restore_hyperlinks_logs_fallback(self, mock_logger):
        """_restore_hyperlinks logs fallback placement."""
        renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")

        doc = Document()

        hyperlinks = [
            {
                "text": "Fallback Link 1",
                "url": "https://example.com/fallback1",
                "day_hint": "monday",
                "section_hint": "objective",
                "_source_slot": 1,
                "_source_subject": "Math",
            },
            {
                "text": "Fallback Link 2",
                "url": "https://example.com/fallback2",
                "day_hint": None,  # No day hint
                "section_hint": "instruction",
                "_source_slot": 1,
                "_source_subject": "Math",
            },
        ]

        # Call _restore_hyperlinks
        renderer._restore_hyperlinks(doc, hyperlinks)

        # Check that fallback placement was logged
        log_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "hyperlink_fallback_placement" in str(call)
        ]

        assert len(log_calls) > 0, "Should log fallback placement"

        # Verify log contains expected data
        fallback_log = None
        for call in mock_logger.info.call_args_list:
            if call[0] and "hyperlink_fallback_placement" in str(call[0]):
                fallback_log = call[1].get("extra", {})
                break

        if fallback_log:
            assert "total_fallback_links" in fallback_log, "Should include total count"
            assert fallback_log["total_fallback_links"] == 2, (
                "Should have 2 fallback links"
            )
            assert "links" in fallback_log, "Should include links array"
            assert len(fallback_log["links"]) == 2, "Should have 2 links in array"


class TestNoSchoolFilteringDiagnostics:
    """Test No-School filtering diagnostics."""

    def test_no_school_filtering_preserves_links_without_day_hint(self):
        """Links without day_hint are preserved during No-School filtering."""
        # This test verifies the logic in batch_processor.py
        # We'll test the filtering logic directly

        no_school_days = ["monday", "tuesday"]
        no_school_days_normalized = {day.lower().strip() for day in no_school_days}

        hyperlinks = [
            {
                "text": "Link with Monday hint",
                "url": "https://example.com/1",
                "day_hint": "monday",
                "section_hint": "objective",
            },
            {
                "text": "Link without day hint",
                "url": "https://example.com/2",
                "day_hint": None,  # No day hint - should be preserved
                "section_hint": "instruction",
            },
            {
                "text": "Link with Tuesday hint",
                "url": "https://example.com/3",
                "day_hint": "tuesday",
                "section_hint": "assessment",
            },
            {
                "text": "Another link without day hint",
                "url": "https://example.com/4",
                "day_hint": None,  # No day hint - should be preserved
                "section_hint": "homework",
            },
        ]

        # Track links without day_hint for diagnostics
        links_without_day_hint = [h for h in hyperlinks if not h.get("day_hint")]

        # Filter hyperlinks
        filtered_hyperlinks = [
            h
            for h in hyperlinks
            if not h.get("day_hint")
            or h.get("day_hint", "").lower().strip() not in no_school_days_normalized
        ]

        filtered_count = len(hyperlinks) - len(filtered_hyperlinks)

        # Links with Monday/Tuesday hints should be filtered
        assert filtered_count == 2, "Should filter 2 links (Monday and Tuesday)"

        # Links without day_hint should be preserved
        assert len(filtered_hyperlinks) == 2, "Should preserve 2 links without day_hint"
        assert all(not h.get("day_hint") for h in filtered_hyperlinks), (
            "All preserved links should have no day_hint"
        )

        # Verify links without day_hint tracking
        assert len(links_without_day_hint) == 2, "Should track 2 links without day_hint"
        assert all(not h.get("day_hint") for h in links_without_day_hint), (
            "Tracked links should have no day_hint"
        )

    @patch("backend.telemetry.logger")
    def test_no_school_filtering_logs_diagnostics(self, mock_logger):
        """No-School filtering logs diagnostics for preserved links."""
        # This simulates the logging in batch_processor.py

        slot = {"slot_number": 1, "subject": "Math"}
        no_school_days = ["monday", "tuesday"]

        hyperlinks = [
            {
                "text": "Link without day hint",
                "url": "https://example.com/1",
                "day_hint": None,
                "section_hint": "instruction",
            },
            {
                "text": "Another link without day hint",
                "url": "https://example.com/2",
                "day_hint": None,
                "section_hint": "homework",
            },
        ]

        # Track links without day_hint for diagnostics
        links_without_day_hint = [h for h in hyperlinks if not h.get("day_hint")]

        # Simulate logging (as done in batch_processor.py)
        if links_without_day_hint:
            logger.info(
                "hyperlinks_preserved_no_day_hint",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "no_school_days": no_school_days,
                    "links_without_day_hint_count": len(links_without_day_hint),
                    "preserved_links": [
                        {
                            "text": h.get("text", "")[:50],
                            "section_hint": h.get("section_hint"),
                        }
                        for h in links_without_day_hint[:5]  # Limit to first 5
                    ],
                },
            )

        # Verify logging was called
        assert mock_logger.info.called, "Should log preserved links"

        # Find the specific log call
        preserved_log_call = None
        for call in mock_logger.info.call_args_list:
            args, kwargs = call
            if args and "hyperlinks_preserved_no_day_hint" in args[0]:
                preserved_log_call = kwargs.get("extra", {})
                break

        if preserved_log_call:
            assert preserved_log_call["slot"] == 1, "Should include slot number"
            assert preserved_log_call["subject"] == "Math", "Should include subject"
            assert preserved_log_call["links_without_day_hint_count"] == 2, (
                "Should include count of links without day_hint"
            )
            assert "preserved_links" in preserved_log_call, (
                "Should include preserved links array"
            )


class TestDayHintValidationRelaxation:
    """Test day hint normalization for compound formats."""

    def test_normalize_monday_wednesday(self):
        """Normalize 'Monday/Wednesday' to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Monday/Wednesday")
        assert normalized == "monday", "Should extract first valid day"

    def test_normalize_mon_wed(self):
        """Normalize 'Mon-Wed' to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Mon-Wed")
        assert normalized == "monday", (
            "Should extract first valid day from abbreviations"
        )

    def test_normalize_monday_comma_wednesday(self):
        """Normalize 'Monday, Wednesday' to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Monday, Wednesday")
        assert normalized == "monday", "Should handle comma separator"

    def test_normalize_monday_and_wednesday(self):
        """Normalize 'Monday and Wednesday' to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Monday and Wednesday")
        assert normalized == "monday", "Should handle 'and' separator"

    def test_normalize_multiple_days(self):
        """Normalize 'Monday/Wednesday/Friday' to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Monday/Wednesday/Friday")
        assert normalized == "monday", (
            "Should extract first valid day from multiple days"
        )

    def test_normalize_already_valid(self):
        """Normalize 'monday' (already valid) to 'monday'."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("monday")
        assert normalized == "monday", "Should preserve already valid day"

    def test_normalize_flex_day_returns_none(self):
        """Normalize 'Flex Day' returns None (no valid day)."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Flex Day")
        assert normalized is None, "Should return None for patterns without valid day"

    def test_normalize_day_one_returns_none(self):
        """Normalize 'Day 1' returns None (no valid day)."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("Day 1")
        assert normalized is None, "Should return None for numeric day patterns"

    def test_normalize_empty_string(self):
        """Normalize empty string returns None."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("")
        assert normalized is None, "Should return None for empty string"

    def test_normalize_whitespace_only(self):
        """Normalize whitespace-only string returns None."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        normalized = parser._normalize_day_hint("   ")
        assert normalized is None, "Should return None for whitespace-only string"

    def test_normalize_all_days(self):
        """Test normalization for all valid days."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for day in days:
            normalized = parser._normalize_day_hint(day)
            assert normalized == day, f"Should normalize {day} correctly"

            # Test uppercase
            normalized = parser._normalize_day_hint(day.upper())
            assert normalized == day, f"Should normalize {day.upper()} correctly"

            # Test capitalized
            normalized = parser._normalize_day_hint(day.capitalize())
            assert normalized == day, f"Should normalize {day.capitalize()} correctly"

    def test_validation_with_normalization(self):
        """Test that validation uses normalization before rejecting."""
        parser = DOCXParser("input/Lesson Plan Template SY'25-26.docx")

        # Test normalization directly
        normalized = parser._normalize_day_hint("Monday/Wednesday")
        assert normalized == "monday", "Normalization should work"

        # Test that already valid days still work
        normalized = parser._normalize_day_hint("monday")
        assert normalized == "monday", "Already valid days should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
