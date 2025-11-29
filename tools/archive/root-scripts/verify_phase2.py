import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.docx_renderer import DOCXRenderer
from tools.table_structure import TableStructureDetector, StructureMetadata

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.renderer = DOCXRenderer("dummy_template.docx")
        # Mock structure detector to return a known structure
        self.renderer.structure_metadata = StructureMetadata(
            structure_type="standard_8x6",
            num_rows=8,
            num_cols=6,
            row_offset=0,
            has_day_row=False,
            row_label_map={
                "unit": 1,
                "objective": 2,
                "anticipatory": 3,
                "instruction": 4,
                "misconception": 5,
                "assessment": 6,
                "homework": 7
            },
            col_header_map={
                "monday": 1,
                "tuesday": 2,
                "wednesday": 3,
                "thursday": 4,
                "friday": 5
            }
        )

    def test_dynamic_row_lookup(self):
        """Verify that row indices are resolved dynamically."""
        self.assertEqual(self.renderer._get_row_index("unit"), 1)
        self.assertEqual(self.renderer._get_row_index("objective"), 2)
        self.assertEqual(self.renderer._get_row_index("unknown"), -1)

    def test_dynamic_col_lookup(self):
        """Verify that column indices are resolved dynamically."""
        self.assertEqual(self.renderer._get_col_index("monday"), 1)
        self.assertEqual(self.renderer._get_col_index("friday"), 5)
        self.assertEqual(self.renderer._get_col_index("saturday"), -1)

    @patch("tools.docx_renderer.MarkdownToDocx")
    def test_fallback_media_placement(self, mock_md):
        """Verify that unmatched media with section hints are appended."""
        # Mock table/cell structure
        mock_table = MagicMock()
        mock_cell = MagicMock()
        mock_table.rows[1].cells[1] = mock_cell
        mock_cell.paragraphs = []
        mock_cell.add_paragraph.return_value = MagicMock()

        # Pending media with hint
        pending_hyperlinks = [
            {
                "text": "Link 1",
                "url": "http://example.com",
                "section_hint": "unit_lesson",
                "_source_slot": 1
            }
        ]
        pending_images = []

        # Call _fill_cell
        self.renderer._fill_cell(
            mock_table,
            1, # row_idx
            1, # col_idx
            "Some text",
            day_name="monday",
            section_name="unit_lesson",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=1
        )

        # Verify link was removed from pending (meaning it was placed)
        self.assertEqual(len(pending_hyperlinks), 0)
        # Verify add_formatted_text was called (fallback logic)
        # Note: exact call args depend on implementation details, but we check it was called
        self.assertTrue(mock_md.add_formatted_text.called)

if __name__ == "__main__":
    unittest.main()
