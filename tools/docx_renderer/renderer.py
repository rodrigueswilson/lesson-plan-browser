"""
DOCX Renderer - Convert validated JSON to DOCX using district template.

This renderer:
1. Loads the district template (input/Lesson Plan Template SY'25-26.docx)
2. Fills in metadata (teacher name, grade, subject, week, homeroom)
3. Fills in daily plans for Monday-Friday
4. Preserves all original formatting
"""

from io import BytesIO
from typing import Any, Dict, List

from docx import Document

from . import logger
from tools.table_structure import TableStructureDetector

from . import fallback_media as _fallback_media_module
from . import hyperlink_placement as _hyperlink_module
from . import inject_inline as _inject_inline_module
from . import style as _style_module
from . import table_cell
from . import render_pipeline as _render_pipeline_module
from . import template_structure as _template_structure_module

sanitize_xml_text = _style_module.sanitize_xml_text
is_signature_table = _style_module.is_signature_table


class DOCXRenderer:
    """Render validated JSON lesson plans to DOCX format."""

    # Table indices in the template document
    METADATA_TABLE_IDX = 0  # First table contains metadata (Name, Grade, etc.)
    DAILY_PLANS_TABLE_IDX = 1  # Second table contains daily lesson plans

    # Row indices in the daily plans table (typical layout; dynamic via get_indices when structure is detected)
    UNIT_LESSON_ROW = 1  # Unit/Lesson row (first data row after headers)
    OBJECTIVE_ROW = 2  # Objective row
    ANTICIPATORY_SET_ROW = 3  # Anticipatory set row
    INSTRUCTION_ROW = 4  # Tailored instruction row
    ASSESSMENT_ROW = 6  # Assessment row

    def __init__(self, template_path: str):
        """Initialize renderer with template path.

        Args:
            template_path: Path to the DOCX template file
        """
        self.template_path = template_path
        self.is_originals = False # Initialized to False, set by renderer logic
        self.logger = logger.bind(component="docx_renderer")
        self.structure_detector = TableStructureDetector()
        
        # Cache template in memory to avoid repeated disk I/O when reused
        self.template_buffer = None
        try:
            with open(template_path, "rb") as f:
                self.template_buffer = BytesIO(f.read())
        except Exception as e:
            self.logger.error(f"Failed to cache template buffer: {e}")

        # Initialize structure metadata
        self.structure_metadata = None
        _template_structure_module.initialize_structure(self)

        # Reset per-render state
        self._reset_state()

    def _reset_state(self):
        """Reset internal state before each render call."""
        self.placement_stats = {
            "coordinate": 0,
            "label_day": 0,
            "fuzzy": 0,
            "fallback": 0,
        }
        self.current_file = None
        self.current_teacher = None
        self._current_metadata = {}
        self.is_originals = False

    def render(
        self,
        json_data: Dict,
        output_path: Any,  # Can be str, Path, or BytesIO
        plan_id: str = None,
        skip_fallback_sections: bool = False,
    ) -> Any:
        """
        Render JSON data to DOCX with semantic anchoring for media.

        Args:
            json_data: Validated lesson plan JSON (supports both single-slot and multi-slot)
            output_path: Path to save DOCX file or BytesIO stream
            plan_id: Optional plan ID for performance tracking
            skip_fallback_sections: If True, don't append "Referenced Links" or "Attached Images" sections
                                   (used when rendering slots for later merging)

        Returns:
            If skip_fallback_sections=True: Tuple (success: bool, pending_hyperlinks: List, pending_images: List)
            Otherwise: True if successful, False otherwise
        """
        return _render_pipeline_module.run_render_pipeline(
            self, json_data, output_path, plan_id, skip_fallback_sections
        )

    def _abbreviate_content(
        self, content: str, num_slots: int, max_length: int = None
    ) -> str:
        return table_cell.abbreviate_content(self, content, num_slots, max_length)

    def _fill_day(
        self,
        doc,
        day_name: str,
        day_data: Dict,
        pending_hyperlinks: List[Dict] = None,
        pending_images: List[Dict] = None,
        slot_number: int = None,
        subject: str = None,
    ):
        table_cell.fill_day(
            self, doc, day_name, day_data,
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            slot_number=slot_number,
            subject=subject,
        )

    def _fill_cell(
        self,
        table,
        row_idx: int,
        col_idx: int,
        text: str,
        day_name: str = None,
        section_name: str = None,
        pending_hyperlinks: List[Dict] = None,
        pending_images: List[Dict] = None,
        current_slot_number: int = None,
        current_subject: str = None,
        append_mode: bool = False,
    ):
        table_cell.fill_cell(
            self, table, row_idx, col_idx, text,
            day_name=day_name,
            section_name=section_name,
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=current_slot_number,
            current_subject=current_subject,
            append_mode=append_mode,
        )

    def _calculate_match_confidence(
        self,
        cell_text: str,
        media: Dict,
        day_name: str = None,
        section_name: str = None,
    ) -> tuple:
        return table_cell.calculate_match_confidence(
            self, cell_text, media, day_name, section_name
        )

    def _inject_hyperlink_inline(self, cell, hyperlink: Dict, row_idx: int = None):
        """Inject hyperlink into cell on its own line."""
        _inject_inline_module.inject_hyperlink_inline(self, cell, hyperlink, row_idx=row_idx)

    def _inject_image_inline(self, cell, image: Dict, max_width: float):
        """Inject image into cell with width constraints."""
        _inject_inline_module.inject_image_inline(self, cell, image, max_width)

    def _append_unmatched_media(
        self, doc: Document, hyperlinks: List[Dict], images: List[Dict]
    ):
        """Append unmatched media to end with context for traceability."""
        _fallback_media_module.append_unmatched_media(
            self, doc, hyperlinks, images
        )

    def _insert_images(self, doc: Document, images: List[Dict]):
        """Insert images at the end of the document (legacy v1.0)."""
        _fallback_media_module.insert_images(self, doc, images)

    def _restore_hyperlinks(self, doc: Document, hyperlinks: List[Dict]):
        """Restore hyperlinks by adding them at the end of the document."""
        _hyperlink_module.restore_hyperlinks(self, doc, hyperlinks)

    def _add_hyperlink(self, paragraph, text: str, url: str, bold: bool = False, insert_at: int = None):
        """Add a hyperlink to a paragraph."""
        _hyperlink_module.add_hyperlink(self, paragraph, text, url, bold=bold, insert_at=insert_at)
