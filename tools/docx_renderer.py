"""
DOCX Renderer - Convert validated JSON to DOCX using district template.

This renderer:
1. Loads the district template (input/Lesson Plan Template SY'25-26.docx)
2. Fills in metadata (teacher name, grade, subject, week, homeroom)
3. Fills in daily plans for Monday-Friday
4. Preserves all original formatting
"""

import base64
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from backend.performance_tracker import get_tracker
from backend.telemetry import logger
from tools.table_structure import StructureMetadata, TableStructureDetector

# Feature flag for fuzzy matching threshold
# ADJUSTED: Lowered to 0.50 to handle bilingual/rephrased content better
# Combined with hint-based boosting for more accurate placement
FUZZY_MATCH_THRESHOLD = 0.50  # Lowered from 0.65 for bilingual support

# Handle imports for both CLI and module usage
try:
    from tools.markdown_to_docx import MarkdownToDocx
except ImportError:
    from markdown_to_docx import MarkdownToDocx


class DOCXRenderer:
    """Render validated JSON lesson plans to DOCX format."""
    
    # Table indices in the template document
    METADATA_TABLE_IDX = 0  # First table contains metadata (Name, Grade, etc.)
    DAILY_PLANS_TABLE_IDX = 1  # Second table contains daily lesson plans
    
    # Row indices in the daily plans table
    UNIT_LESSON_ROW = 1  # Unit/Lesson row (first data row after headers)

    def __init__(self, template_path: str):
        """Initialize renderer with template path.

        Args:
            template_path: Path to the DOCX template file
        """
        self.template_path = template_path
        self.logger = logger.bind(component="docx_renderer")
        self.structure_detector = TableStructureDetector()
        self.placement_stats = {
            "coordinate": 0,
            "label_day": 0,
            "fuzzy": 0,
            "fallback": 0,
        }
        
        # Initialize structure metadata
        self.structure_metadata = None
        self._initialize_structure()

    def _initialize_structure(self):
        """Initialize table structure metadata from template."""
        try:
            doc = Document(self.template_path)
            if len(doc.tables) > 1:
                # Assume daily plans table is at index 1 (standard)
                # If not, we might need more sophisticated detection logic
                table = doc.tables[1] 
                self.structure_metadata = self.structure_detector.detect_structure(table)
                
                self.logger.info(
                    "template_structure_detected",
                    extra={
                        "type": self.structure_metadata.structure_type,
                        "rows": self.structure_metadata.num_rows,
                        "cols": self.structure_metadata.num_cols,
                        "has_day_row": self.structure_metadata.has_day_row
                    }
                )
            else:
                self.logger.warning("Template has fewer than 2 tables, cannot detect structure")
        except Exception as e:
            self.logger.error(f"Failed to initialize structure: {e}")

    def _get_row_index(self, label: str) -> int:
        """Get row index for a given label using structure metadata."""
        if self.structure_metadata:
            idx = self.structure_metadata.get_row_index(label)
            if idx is not None:
                # Apply offset if needed (e.g. for day row)
                return idx + self.structure_metadata.row_offset
        return -1

    def _get_col_index(self, day: str) -> int:
        """Get column index for a given day using structure metadata."""
        if self.structure_metadata:
            idx = self.structure_metadata.get_col_index(day)
            return idx if idx is not None else -1
        return -1

    def render(self, json_data: Dict, output_path: str, plan_id: str = None) -> bool:
        """
        Render JSON data to DOCX with semantic anchoring for media.

        Args:
            json_data: Validated lesson plan JSON (supports both single-slot and multi-slot)
            output_path: Path to save DOCX file
            plan_id: Optional plan ID for performance tracking

        Returns:
            True if successful, False otherwise
        """
        tracker = get_tracker()

        # Set context for logging
        self.current_file = Path(output_path).name
        self.current_teacher = json_data.get("metadata", {}).get(
            "teacher_name", "unknown"
        )

        try:
            # Track template loading
            if plan_id:
                with tracker.track_operation(plan_id, "render_load_template"):
                    doc = Document(self.template_path)
            else:
                doc = Document(self.template_path)

            # Track metadata filling
            if plan_id:
                with tracker.track_operation(plan_id, "render_fill_metadata"):
                    self._fill_metadata(doc, json_data["metadata"])
            else:
                self._fill_metadata(doc, json_data["metadata"])

            # Prepare media for semantic anchoring
            schema_version = json_data.get("_media_schema_version", "1.0")
            # v1.1 and v2.0 both use semantic anchoring (v2.0 adds coordinates)
            pending_hyperlinks = (
                json_data.get("_hyperlinks", []).copy()
                if schema_version in ["1.1", "2.0"]
                else []
            )
            pending_images = (
                json_data.get("_images", []).copy()
                if schema_version in ["1.1", "2.0"]
                else []
            )

            # v2.0: Use hybrid coordinate-based placement for hyperlinks
            # CRITICAL: Only for single-slot documents. Multi-slot changes the table structure
            # (combines multiple slots' content in each cell), so coordinates don't map correctly.
            is_multi_slot = any(
                "slots" in day_data for day_data in json_data.get("days", {}).values()
            )

            if schema_version == "2.0" and pending_hyperlinks and not is_multi_slot:
                table = doc.tables[self.DAILY_PLANS_TABLE_IDX]
                structure = self.structure_detector.detect_structure(table)

                logger.info(
                    "hyperlink_placement_v2",
                    extra={
                        "total_links": len(pending_hyperlinks),
                        "structure_type": structure.structure_type,
                        "multi_slot": is_multi_slot,
                    },
                )

                # Process each hyperlink with hybrid strategy
                for hyperlink in pending_hyperlinks[:]:
                    strategy = self._place_hyperlink_hybrid(hyperlink, table, structure)
                    self.placement_stats[strategy] += 1

                    # If placed, remove from pending list
                    if strategy != "fallback":
                        pending_hyperlinks.remove(hyperlink)

                # Log placement statistics
                logger.info("hyperlink_placement_stats", extra=self.placement_stats)

            # Extract slot metadata for filtering (if present)
            # In multi-slot batch processing, each lesson JSON has slot metadata
            slot_number = json_data.get("metadata", {}).get("slot_number")
            subject = json_data.get("metadata", {}).get("subject")

            # DEBUG: Log slot metadata extraction
            logger.info(
                "renderer_slot_metadata_extracted",
                extra={
                    "slot_number": slot_number,
                    "subject": subject,
                    "has_hyperlinks": len(json_data.get("_hyperlinks", [])),
                    "teacher": json_data.get("metadata", {}).get(
                        "teacher_name", "unknown"
                    ),
                },
            )

            # DIAGNOSTIC: Log renderer metadata extraction
            from tools.diagnostic_logger import get_diagnostic_logger

            diag = get_diagnostic_logger()
            diag.log_renderer_extracted_metadata(
                slot_number,
                subject,
                len(json_data.get("_hyperlinks", [])),
                json_data.get("metadata", {}).get("teacher_name", "unknown"),
            )

            # Track daily plans filling            # Fill daily plans
            if plan_id:
                with tracker.track_operation(plan_id, "render_fill_days"):
                    table = doc.tables[self.DAILY_PLANS_TABLE_IDX]
                    for day_name, day_data in json_data["days"].items():
                        col_idx = self._get_col_index(day_name)
                        if col_idx == -1:
                            continue

                        # Check if this day has multiple slots
                        if "slots" in day_data:
                            self._fill_multi_slot_day(
                                table,
                                col_idx,
                                day_data["slots"],
                                day_name=day_name,
                                pending_hyperlinks=pending_hyperlinks,
                                pending_images=pending_images,
                            )
                        else:
                            self._fill_single_slot_day(
                                table,
                                col_idx,
                                day_data,
                                day_name=day_name,
                                pending_hyperlinks=pending_hyperlinks,
                                pending_images=pending_images,
                                slot_number=slot_number,
                                subject=subject,
                            )       # Append unmatched media to fallback sections
            if pending_hyperlinks or pending_images:
                self._append_unmatched_media(doc, pending_hyperlinks, pending_images)
                logger.info(
                    "unmatched_media_appended",
                    extra={
                        "hyperlinks": len(pending_hyperlinks),
                        "images": len(pending_images),
                    },
                )

            # Legacy behavior for schema v1.0
            if schema_version == "1.0":
                if "_images" in json_data and json_data["_images"]:
                    if plan_id:
                        with tracker.track_operation(plan_id, "render_insert_images"):
                            self._insert_images(doc, json_data["_images"])
                            logger.info(
                                "images_inserted",
                                extra={"count": len(json_data["_images"])},
                            )
                    else:
                        self._insert_images(doc, json_data["_images"])
                        logger.info(
                            "images_inserted",
                            extra={"count": len(json_data["_images"])},
                        )

                if "_hyperlinks" in json_data and json_data["_hyperlinks"]:
                    if plan_id:
                        with tracker.track_operation(
                            plan_id, "render_restore_hyperlinks"
                        ):
                            self._restore_hyperlinks(doc, json_data["_hyperlinks"])
                            logger.info(
                                "hyperlinks_restored",
                                extra={"count": len(json_data["_hyperlinks"])},
                            )
                    else:
                        self._restore_hyperlinks(doc, json_data["_hyperlinks"])
                        logger.info(
                            "hyperlinks_restored",
                            extra={"count": len(json_data["_hyperlinks"])},
                        )

            # Track table normalization
            # Calculate table width dynamically from template page setup
            section = doc.sections[0]
            available_width_emus = section.page_width - section.left_margin - section.right_margin
            available_width_inches = available_width_emus / 914400
            
            if plan_id:
                with tracker.track_operation(plan_id, "render_normalize_tables"):
                    from tools.docx_utils import normalize_all_tables

                    table_count = normalize_all_tables(doc, total_width_inches=available_width_inches)
                    logger.info("tables_normalized", extra={"count": table_count, "width_inches": available_width_inches})
            else:
                from tools.docx_utils import normalize_all_tables

                table_count = normalize_all_tables(doc, total_width_inches=available_width_inches)
                logger.info("tables_normalized", extra={"count": table_count, "width_inches": available_width_inches})

            # Track file saving
            if plan_id:
                with tracker.track_operation(plan_id, "render_save_docx"):
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    doc.save(output_path)
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                doc.save(output_path)

            logger.info("docx_render_success", extra={"output_path": str(output_path)})
            return True

        except Exception as e:
            logger.exception(
                "docx_render_error",
                extra={
                    "output_path": output_path if "output_path" in locals() else None,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            # Re-raise the exception instead of returning False
            # This allows callers to see the actual error
            raise RuntimeError(
                f"Renderer failed to create DOCX file '{output_path}': {str(e)}"
            ) from e

    def _fill_metadata(self, doc: Document, metadata: Dict):
        """
        Fill metadata table (Table 0).

        Template structure:
        | Name: | Grade: | Homeroom: | Subject: | Week of: |

        Args:
            doc: Document object
            metadata: Metadata dictionary
        """
        table = doc.tables[self.METADATA_TABLE_IDX]
        row = table.rows[0]

        def _format_metadata_cell(cell, label: str, value: str):
            """Format a metadata cell with bold label and Arial 10pt font."""
            # Clear existing content
            cell.text = ""
            # Get or create paragraph
            para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            
            # Add label run (bold, Arial 10pt)
            label_run = para.add_run(f"{label}: ")
            label_run.bold = True
            label_run.font.name = "Arial"
            label_run.font.size = Pt(10)
            
            # Add value run (not bold, Arial 10pt)
            value_run = para.add_run(value)
            value_run.font.name = "Arial"
            value_run.font.size = Pt(10)

        # Name (cell 0)
        if "teacher_name" in metadata and metadata["teacher_name"]:
            cell = row.cells[0]
            _format_metadata_cell(cell, "Name", metadata["teacher_name"])

        # Grade (cell 1)
        if "grade" in metadata:
            cell = row.cells[1]
            _format_metadata_cell(cell, "Grade", metadata["grade"])

        # Homeroom (cell 2)
        if "homeroom" in metadata and metadata["homeroom"]:
            cell = row.cells[2]
            _format_metadata_cell(cell, "Homeroom", metadata["homeroom"])

        # Subject (cell 3)
        if "subject" in metadata:
            cell = row.cells[3]
            _format_metadata_cell(cell, "Subject", metadata["subject"])

        # Week of (cell 4)
        if "week_of" in metadata:
            cell = row.cells[4]
            _format_metadata_cell(cell, "Week of", metadata["week_of"])

    def _extract_unique_teachers(self, json_data: Dict) -> List[str]:
        """
        Extract unique teacher names from all slots in a multi-slot structure.

        Args:
            json_data: Full lesson plan JSON with days/slots structure

        Returns:
            Sorted list of unique teacher names
        """
        teachers = set()
        if "days" in json_data:
            for day_data in json_data["days"].values():
                if "slots" in day_data:
                    for slot in day_data["slots"]:
                        if slot.get("teacher_name"):
                            teachers.add(slot["teacher_name"])
        return sorted(teachers)

    def _extract_unique_subjects(self, json_data: Dict) -> List[str]:
        """
        Extract unique subjects from all slots in a multi-slot structure.

        Args:
            json_data: Full lesson plan JSON with days/slots structure

        Returns:
            Sorted list of unique subjects
        """
        subjects = set()
        if "days" in json_data:
            for day_data in json_data["days"].values():
                if "slots" in day_data:
                    for slot in day_data["slots"]:
                        if slot.get("subject"):
                            subjects.add(slot["subject"])
        return sorted(subjects)

    def _abbreviate_content(
        self, content: str, num_slots: int, max_length: int = None
    ) -> str:
        """
        Abbreviate content based on number of slots to ensure it fits in template cells.

        Args:
            content: Original content text
            num_slots: Number of slots being displayed
            max_length: Optional max length override

        Returns:
            Abbreviated content with ellipsis if truncated
        """
        if not content:
            return content

        # Calculate max length based on number of slots
        if max_length is None:
            if num_slots <= 2:
                max_length = 500  # Full content
            elif num_slots == 3:
                max_length = 300  # Moderate truncation
            elif num_slots == 4:
                max_length = 200  # More truncation
            else:  # 5+ slots
                max_length = 150  # Aggressive truncation

        # Truncate if needed
        if len(content) > max_length:
            # Try to truncate at sentence boundary
            truncated = content[:max_length]
            last_period = truncated.rfind(".")
            last_newline = truncated.rfind("\n")

            # Use sentence boundary if found in last 30% of text
            boundary = max(last_period, last_newline)
            if boundary > max_length * 0.7:
                return truncated[: boundary + 1] + "..."
            else:
                # Just truncate at word boundary
                last_space = truncated.rfind(" ")
                if last_space > 0:
                    return truncated[:last_space] + "..."
                return truncated + "..."

        return content

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
        """
        Fill a single day's data with media injection.

        Args:
            doc: Document object
            day_name: Day name (monday, tuesday, etc.)
            day_data: Day's lesson plan data (can be single-slot or multi-slot)
            pending_hyperlinks: List of hyperlinks awaiting placement
            pending_images: List of images awaiting placement
            slot_number: Slot number for filtering (if rendering single slot)
            subject: Subject name for filtering (if rendering single slot)
        """
        table = doc.tables[self.DAILY_PLANS_TABLE_IDX]
        col_idx = self.DAY_TO_COL[day_name.lower()]

        # Track hyperlinks before placement for observability
        hyperlinks_before = len(pending_hyperlinks) if pending_hyperlinks else 0

        # Check if this is multi-slot structure (has 'slots' array)
        if "slots" in day_data and isinstance(day_data["slots"], list):
            # Multi-slot: combine all slots for this day
            self._fill_multi_slot_day(
                table,
                col_idx,
                day_data["slots"],
                day_name=day_name,
                pending_hyperlinks=pending_hyperlinks,
                pending_images=pending_images,
            )
        else:
            # Single-slot: use existing logic with slot filtering
            self._fill_single_slot_day(
                table,
                col_idx,
                day_data,
                day_name=day_name,
                pending_hyperlinks=pending_hyperlinks,
                pending_images=pending_images,
                slot_number=slot_number,
                subject=subject,
            )

        # Log placement outcomes for observability
        hyperlinks_after = len(pending_hyperlinks) if pending_hyperlinks else 0
        placed_count = hyperlinks_before - hyperlinks_after

        if hyperlinks_before > 0:
            logger.info(
                "hyperlink_placement_outcome",
                extra={
                    "day": day_name,
                    "slot": slot_number,
                    "subject": subject,
                    "total_links": hyperlinks_before,
                    "placed_count": placed_count,
                    "remaining_count": hyperlinks_after,
                    "placement_rate": placed_count / hyperlinks_before
                    if hyperlinks_before > 0
                    else 0.0,
                },
            )

    def _fill_single_slot_day(
        self,
        table,
        col_idx: int,
        day_data: Dict,
        day_name: str = None,
        pending_hyperlinks: List[Dict] = None,
        pending_images: List[Dict] = None,
        slot_number: int = None,
        subject: str = None,
    ):
        """
        Fill a single slot's data for one day with media injection.

        Args:
            table: Table object
            col_idx: Column index for the day
            day_data: Day's lesson plan data
            day_name: Day name for media matching
            pending_hyperlinks: List of hyperlinks awaiting placement
            pending_images: List of images awaiting placement
            slot_number: Slot number for filtering hyperlinks/images
            subject: Subject name for filtering hyperlinks/images
        """
        # Check if this is a "No School" day
        unit_lesson = day_data.get("unit_lesson", "")
        if unit_lesson and "no school" in unit_lesson.lower():
            # For "No School" days, only fill the unit/lesson cell and clear others
            self._fill_cell(
                table,
                self.UNIT_LESSON_ROW,
                col_idx,
                unit_lesson,
                day_name=day_name,
                section_name="unit_lesson",
                pending_hyperlinks=pending_hyperlinks,
                pending_images=pending_images,
                current_slot_number=slot_number,
                current_subject=subject,
            )
            # Clear all other cells for this day
            for row_label in [
                "objective",
                "anticipatory",
                "instruction",
                "misconception",
                "assessment",
                "homework",
            ]:
                row_idx = self._get_row_index(row_label)
                if row_idx != -1:
                    table.rows[row_idx].cells[col_idx].text = ""
            return

        # Unit/Lesson (Row 1)
        self._fill_cell(
            table,
            self._get_row_index("unit"),
            col_idx,
            unit_lesson,
            day_name=day_name,
            section_name="unit_lesson",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Objective (Row 2)
        objective_text = self._format_objective(day_data.get("objective", {}))
        self._fill_cell(
            table,
            self._get_row_index("objective"),
            col_idx,
            objective_text,
            day_name=day_name,
            section_name="objective",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Anticipatory Set (Row 3)
        anticipatory_text = self._format_anticipatory_set(
            day_data.get("anticipatory_set", {})
        )
        self._fill_cell(
            table,
            self._get_row_index("anticipatory"),
            col_idx,
            anticipatory_text,
            day_name=day_name,
            section_name="anticipatory_set",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Tailored Instruction (Row 4)
        instruction_text = self._format_tailored_instruction(
            day_data.get("tailored_instruction", {}),
            day_data.get("vocabulary_cognates"),
            day_data.get("sentence_frames"),
        )
        self._fill_cell(
            table,
            self._get_row_index("instruction"),
            col_idx,
            instruction_text,
            day_name=day_name,
            section_name="instruction",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Misconceptions (Row 5)
        misconceptions_text = self._format_misconceptions(
            day_data.get("misconceptions", {})
        )
        self._fill_cell(
            table,
            self._get_row_index("misconception"),
            col_idx,
            misconceptions_text,
            day_name=day_name,
            section_name="misconceptions",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Assessment (Row 6)
        assessment_text = self._format_assessment(day_data.get("assessment", {}))
        self._fill_cell(
            table,
            self._get_row_index("assessment"),
            col_idx,
            assessment_text,
            day_name=day_name,
            section_name="assessment",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

        # Homework (Row 7)
        homework_text = self._format_homework(day_data.get("homework", ""))
        self._fill_cell(
            table,
            self._get_row_index("homework"),
            col_idx,
            homework_text,
            day_name=day_name,
            section_name="homework",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )

    def _fill_multi_slot_day(
        self,
        table,
        col_idx: int,
        slots: List[Dict],
        day_name: str = None,
        pending_hyperlinks: List[Dict] = None,
        pending_images: List[Dict] = None,
    ):
        """
        Fill multiple slots' data for one day, with per-slot hyperlink placement.

        Strategy:
        - For each row (Unit/Lesson, Objective, etc.):
          - Clear cell once (first _fill_cell call will do this)
          - For each slot:
            - Build slot text with header
            - Call _fill_cell with append_mode=True (after first)
            - Pass shared pending_hyperlinks/pending_images lists
            - Let _fill_cell filter by current_slot_number
            - Matched items removed from shared lists automatically

        Args:
            table: Table object
            col_idx: Column index for the day
            slots: List of slot data dicts
            day_name: Day name for media matching
            pending_hyperlinks: List of hyperlinks awaiting placement
            pending_images: List of images awaiting placement
        """
        if not slots:
            return

        # Sort slots by slot_number to ensure consistent ordering
        sorted_slots = sorted(slots, key=lambda x: x.get("slot_number", 0))
        num_slots = len(sorted_slots)

        # Check if any slot has content (for placeholder logic)
        slots_have_content = []
        for slot in sorted_slots:
            has_content = any(
                [
                    slot.get("unit_lesson"),
                    slot.get("objective"),
                    slot.get("anticipatory_set"),
                    slot.get("tailored_instruction"),
                    slot.get("misconceptions"),
                    slot.get("assessment"),
                    slot.get("homework"),
                ]
            )
            slots_have_content.append(has_content)

        # Define rows to fill with correct field names and format functions
        # Use dynamic row indices from structure detector
        rows_config = [
            # (field_name, row_idx, format_func, placeholder_text, max_length)
            (
                "unit_lesson",
                self._get_row_index("unit"),
                None,
                "[No unit/lesson specified]",
                100,
            ),
            (
                "objective",
                self._get_row_index("objective"),
                self._format_objective,
                "[No objective specified]",
                None,
            ),
            (
                "anticipatory_set",
                self._get_row_index("anticipatory"),
                self._format_anticipatory_set,
                None,
                None,
            ),
            (
                "tailored_instruction",
                self._get_row_index("instruction"),
                self._format_tailored_instruction,
                None,
                None,
            ),
            (
                "misconceptions",
                self._get_row_index("misconception"),
                self._format_misconceptions,
                None,
                None,
            ),
            (
                "assessment", 
                self._get_row_index("assessment"), 
                self._format_assessment, 
                None, 
                None
            ),
            (
                "homework", 
                self._get_row_index("homework"), 
                self._format_homework, 
                None, 
                100
            ),
        ]

        # Fill each row
        for (
            field_name,
            row_idx,
            format_func,
            placeholder_text,
            max_length,
        ) in rows_config:
            # NOTE: We don't manually clear the cell here. The first _fill_cell call
            # (with append_mode=False) will clear it automatically.

            # Track whether we've written any content to this row yet
            written_any = False

            # Fill each slot
            for i, slot in enumerate(sorted_slots):
                slot_num = slot.get("slot_number", "?")
                subject = slot.get("subject", "Unknown")
                teacher = slot.get("teacher_name", "")
                has_content = slots_have_content[i]

                # Check for "No School" status
                # If this slot has "No School" in unit_lesson, we only show it in the unit_lesson row
                # and skip all other rows for this slot.
                is_no_school = "no school" in (slot.get("unit_lesson") or "").lower()
                if is_no_school and field_name != "unit_lesson":
                    continue

                # Build slot header
                slot_header = f"**Slot {slot_num}: {subject}**"
                if teacher:
                    slot_header += f" ({teacher})"

                # Get slot content
                slot_content = slot.get(field_name)

                # Build slot text
                if slot_content:
                    # Format if format function provided
                    if format_func:
                        slot_text = format_func(slot_content)
                    else:
                        # Raw string (e.g., unit_lesson)
                        slot_text = slot_content

                    # Abbreviate for multi-slot
                    if slot_text:
                        slot_text = self._abbreviate_content(
                            slot_text, num_slots, max_length=max_length
                        )
                        slot_text = f"{slot_header}\n{slot_text}"
                    else:
                        slot_text = None
                elif has_content and placeholder_text:
                    # Add placeholder if other fields exist but not this one
                    slot_text = f"{slot_header}\n{placeholder_text}"
                else:
                    # No content and no placeholder needed
                    slot_text = None

                # Skip if no content
                if not slot_text:
                    continue

                # Add separator only if there's another slot with content after this one
                # Look ahead to see if any remaining slots will produce content
                has_next_slot_with_content = False
                for j in range(i + 1, len(sorted_slots)):
                    next_slot = sorted_slots[j]
                    next_slot_content = next_slot.get(field_name)
                    next_has_content = slots_have_content[j]

                    # Check if next slot will produce text (content or placeholder)
                    if next_slot_content:
                        # Has actual content
                        if format_func:
                            next_text = format_func(next_slot_content)
                        else:
                            next_text = next_slot_content
                        if next_text:
                            has_next_slot_with_content = True
                            break
                    elif next_has_content and placeholder_text:
                        # Will show placeholder
                        has_next_slot_with_content = True
                        break

                # Only add separator if there's content coming after
                if has_next_slot_with_content:
                    slot_text += "\n\n---"

                # Fill cell with this slot's content
                # IMPORTANT: Pass shared pending_hyperlinks and pending_images lists
                # _fill_cell will filter by current_slot_number and remove matched items
                self._fill_cell(
                    table,
                    row_idx,
                    col_idx,
                    slot_text,
                    day_name=day_name,
                    section_name=field_name,
                    pending_hyperlinks=pending_hyperlinks,  # Shared list
                    pending_images=pending_images,  # Shared list
                    current_slot_number=slot_num,
                    current_subject=subject,
                    append_mode=written_any,  # Append only if we've already written to this row
                )

                # Mark that we've written content to this row
                written_any = True

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
        """
        Fill a cell with formatted text and inject matched media inline.

        Args:
            table: Table object
            row_idx: Row index
            col_idx: Column index
            text: Text to fill (may contain markdown)
            day_name: Day name for media matching
            section_name: Section name for media matching
            pending_hyperlinks: List of hyperlinks awaiting placement
            pending_images: List of images awaiting placement
            current_slot_number: Slot number for filtering hyperlinks/images
            current_subject: Subject name for filtering hyperlinks/images
            append_mode: If True, append to cell without clearing existing content
        """
        from backend.config import settings

        cell = table.rows[row_idx].cells[col_idx]

        # Check if cell already has hyperlinks (from coordinate placement)
        existing_hyperlinks = cell._element.xpath(".//w:hyperlink")
        has_coordinate_hyperlinks = len(existing_hyperlinks) > 0

        # Clear existing content ONLY if:
        # 1. No coordinate-placed hyperlinks exist, AND
        # 2. Not in append mode
        if not has_coordinate_hyperlinks and not append_mode:
            # CRITICAL: Manually remove all paragraphs instead of cell.text = ""
            # cell.text = "" leaves an empty paragraph with default formatting (Arial 11)
            # which causes blank lines. Manual removal is cleaner.
            paras_to_remove = list(cell.paragraphs)
            for para in paras_to_remove:
                p = para._element
                p.getparent().remove(p)
            # Word requires at least one paragraph - add a fresh one with proper formatting
            new_para = cell.add_paragraph()
            new_para.paragraph_format.space_after = Pt(0)
            new_para.paragraph_format.space_before = Pt(0)
            new_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

        # Collect matching hyperlinks FIRST (before adding text)
        matching_hyperlinks = []
        if pending_hyperlinks and text:
            # DEBUG: Log filtering context
            logger.info(
                "hyperlink_filtering_context",
                extra={
                    "current_slot_number": current_slot_number,
                    "current_subject": current_subject,
                    "pending_hyperlinks_count": len(pending_hyperlinks),
                    "cell": f"{day_name}_{section_name}"
                    if day_name and section_name
                    else "unknown",
                },
            )

            # DIAGNOSTIC: Log filtering context
            from tools.diagnostic_logger import get_diagnostic_logger

            diag = get_diagnostic_logger()
            diag.log_filtering_context(
                current_slot_number,
                current_subject,
                len(pending_hyperlinks),
                f"{day_name}_{section_name}"
                if day_name and section_name
                else "unknown",
            )

            # Collect all matching hyperlinks first
            for hyperlink in pending_hyperlinks[:]:
                # CRITICAL: Filter hyperlinks by slot to prevent cross-contamination
                # Only consider hyperlinks from the current slot being rendered
                if current_slot_number is not None:
                    link_slot = hyperlink.get("_source_slot")

                    # STRICT: In multi-slot mode, REQUIRE slot metadata
                    if link_slot is None:
                        # Missing metadata - skip to prevent cross-contamination
                        logger.warning(
                            "hyperlink_missing_slot_metadata",
                            extra={
                                "text": hyperlink["text"][:50],
                                "url": hyperlink["url"],
                                "current_slot": current_slot_number,
                            },
                        )
                        continue

                    if link_slot != current_slot_number:
                        # Skip hyperlinks from other slots
                        logger.debug(
                            "hyperlink_filtered_by_slot",
                            extra={
                                "text": hyperlink["text"][:50],
                                "link_slot": link_slot,
                                "current_slot": current_slot_number,
                            },
                        )

                        # DIAGNOSTIC: Log filtered hyperlink
                        diag.log_hyperlink_filtered(
                            hyperlink["text"],
                            link_slot,
                            current_slot_number,
                            "slot_mismatch",
                        )
                        continue

                # Additional filter by subject for extra safety
                if current_subject is not None:
                    link_subject = hyperlink.get("_source_subject")

                    # STRICT: In multi-slot mode, REQUIRE subject metadata
                    if link_subject is None:
                        # Missing metadata - skip to prevent cross-contamination
                        logger.warning(
                            "hyperlink_missing_subject_metadata",
                            extra={
                                "text": hyperlink["text"][:50],
                                "url": hyperlink["url"],
                                "current_subject": current_subject,
                            },
                        )
                        continue

                    if link_subject != current_subject:
                        # Skip hyperlinks from other subjects
                        logger.debug(
                            "hyperlink_filtered_by_subject",
                            extra={
                                "text": hyperlink["text"][:50],
                                "link_subject": link_subject,
                                "current_subject": current_subject,
                            },
                        )
                        continue

                confidence, match_type = self._calculate_match_confidence(
                    text, hyperlink, day_name, section_name
                )

                if confidence >= settings.MEDIA_MATCH_CONFIDENCE_THRESHOLD:
                    matching_hyperlinks.append((hyperlink, confidence, match_type))

        # CRITICAL: Format ALL paragraphs in cell consistently (including coordinate hyperlinks)
        # This ensures coordinate-placed hyperlinks don't have default spacing/styles
        if cell.paragraphs:
            for para in cell.paragraphs:
                # Only format if paragraph has content (don't format empty placeholder)
                if para.text.strip() or para.runs:
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    # Ensure font formatting is consistent
                    if row_idx > 0 and col_idx > 0:
                        for run in para.runs:
                            if not run.font.name or run.font.name == "Arial":
                                run.font.name = "Times New Roman"
                            if not run.font.size or run.font.size != Pt(8):
                                run.font.size = Pt(8)

        # Check if "Link:" or "Links:" header already exists (prevents duplicate headers in append mode)
        has_links_header = False
        if cell.paragraphs:
            # Check first few paragraphs for existing "Link:" or "Links:" header
            for para in cell.paragraphs[:3]:
                para_text = para.text.strip()
                if para_text.startswith("Link:") or para_text.startswith("Links:"):
                    has_links_header = True
                    break

        # Calculate total hyperlink count (coordinate + fuzzy)
        coordinate_link_count = len(existing_hyperlinks) if existing_hyperlinks else 0
        fuzzy_link_count = len(matching_hyperlinks) if matching_hyperlinks else 0
        total_link_count = coordinate_link_count + fuzzy_link_count

        # Log cases where both coordinate and fuzzy links exist in the same cell
        if matching_hyperlinks and has_coordinate_hyperlinks:
            logger.info(
                "hyperlink_mixed_placement_detected",
                extra={
                    "coordinate_links_count": coordinate_link_count,
                    "fuzzy_links_count": fuzzy_link_count,
                    "total_links_count": total_link_count,
                    "cell": f"{day_name}_{section_name}",
                    "row_idx": row_idx,
                    "col_idx": col_idx,
                    "slot": current_slot_number,
                    "subject": current_subject,
                },
            )

        # Add "Link:" or "Links:" header at TOP if we have any hyperlinks and no header exists
        links_header_just_added = False
        if total_link_count > 0 and not has_links_header:
            # Determine header text: "Link:" (singular) for 1 link, "Links:" (plural) for multiple
            header_text = "Link:" if total_link_count == 1 else "Links:"

            # Insert header paragraph at the TOP of the cell (before any existing content)
            if cell.paragraphs:
                # Insert before the first paragraph
                links_header_para = cell.paragraphs[0].insert_paragraph_before()
            else:
                # Cell is empty, add as first paragraph
                links_header_para = cell.add_paragraph()

            links_header_run = links_header_para.add_run(header_text)
            links_header_run.bold = True

            # Remove spacing to avoid blank line between header and links
            links_header_para.paragraph_format.space_after = Pt(0)
            links_header_para.paragraph_format.space_before = Pt(0)
            # Set line spacing to SINGLE (equivalent to Word's 1.0)
            # SINGLE automatically uses font size for line spacing
            links_header_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

            # CRITICAL: Remove any empty paragraphs that might cause blank lines
            # After inserting header, check if there are empty paragraphs after it
            header_idx = None
            for idx, para in enumerate(cell.paragraphs):
                if para.text.strip().startswith(("Link:", "Links:")):
                    header_idx = idx
                    break

            if header_idx is not None:
                # Remove empty paragraphs immediately after header
                paras_to_remove = []
                for idx in range(header_idx + 1, len(cell.paragraphs)):
                    para = cell.paragraphs[idx]
                    if not para.text.strip() and not para.runs:
                        paras_to_remove.append(para)

                # Remove empty paragraphs (in reverse order to maintain indices)
                for para in reversed(paras_to_remove):
                    p = para._element
                    p.getparent().remove(p)

                # CRITICAL: Re-format header paragraph to ensure exact spacing
                header_para = cell.paragraphs[header_idx]
                header_para.paragraph_format.space_after = Pt(0)
                header_para.paragraph_format.space_before = Pt(0)
                header_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

            # Apply font formatting
            if row_idx > 0 and col_idx > 0:
                links_header_run.font.name = "Times New Roman"
                links_header_run.font.size = Pt(8)

            links_header_just_added = True

        # If we have matching fuzzy hyperlinks, inject them immediately after header
        if matching_hyperlinks and not has_coordinate_hyperlinks:
            # Inject all matching hyperlinks right after the header (or at top if no header)
            for idx, (hyperlink, confidence, match_type) in enumerate(
                matching_hyperlinks
            ):
                # If we just added a header, insert first hyperlink paragraph right after header with zero spacing
                if links_header_just_added and idx == 0:
                    # Find the header paragraph
                    header_para_idx = None
                    for para_idx, para in enumerate(cell.paragraphs):
                        if para.text.strip().startswith(("Link:", "Links:")):
                            header_para_idx = para_idx
                            break

                    if header_para_idx is not None:
                        # Add hyperlink directly to header paragraph with line break (same paragraph = no spacing)
                        header_para = cell.paragraphs[header_para_idx]

                        # CRITICAL: Set exact line spacing and zero spacing on header paragraph
                        header_para.paragraph_format.space_after = Pt(0)
                        header_para.paragraph_format.space_before = Pt(0)
                        header_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

                        # Add line break (creates new line within same paragraph - no spacing)
                        # Note: We add break AFTER setting formatting to ensure it inherits the formatting
                        break_run = header_para.add_run()
                        break_run.font.name = "Times New Roman"
                        break_run.font.size = Pt(8)
                        break_run.add_break()

                        # Add hyperlink to the same paragraph (no new paragraph = no spacing)
                        self._add_hyperlink(
                            header_para, hyperlink["text"], hyperlink["url"]
                        )
                        # Apply font formatting to the hyperlink runs
                        if row_idx > 0 and col_idx > 0:
                            for run in header_para.runs:
                                if run.text and hyperlink["text"] in run.text:
                                    run.font.name = "Times New Roman"
                                    run.font.size = Pt(8)
                        # CRITICAL: Unit/Lesson row hyperlinks must be BOLD
                        if row_idx == self.UNIT_LESSON_ROW:
                            for run in header_para.runs:
                                if run.text and hyperlink["text"] in run.text:
                                    run.font.bold = True
                    else:
                        # Fallback: use standard method
                        self._inject_hyperlink_inline(cell, hyperlink, row_idx=row_idx)
                else:
                    # Subsequent hyperlinks or header already exists - use standard method
                    self._inject_hyperlink_inline(cell, hyperlink, row_idx=row_idx)

                pending_hyperlinks.remove(hyperlink)

                logger.info(
                    "hyperlink_placed_inline",
                    extra={
                        "text": hyperlink["text"][:50],
                        "url": hyperlink["url"][:50],
                        "cell": f"{day_name}_{section_name}",
                        "confidence": confidence,
                        "match_type": match_type,
                        "slot": current_slot_number,
                        "subject": current_subject,
                    },
                )

                # DIAGNOSTIC: Log placed hyperlink
                diag.log_hyperlink_placed(
                    hyperlink["text"],
                    current_slot_number,
                    current_subject,
                    f"{day_name}_{section_name}",
                    confidence,
                )

        # If we have fuzzy links but header already exists (append mode), inject links without header
        elif matching_hyperlinks and has_links_header:
            # Inject links without adding another header
            for hyperlink, confidence, match_type in matching_hyperlinks:
                self._inject_hyperlink_inline(cell, hyperlink, row_idx=row_idx)
                pending_hyperlinks.remove(hyperlink)

                logger.info(
                    "hyperlink_placed_inline",
                    extra={
                        "text": hyperlink["text"][:50],
                        "url": hyperlink["url"][:50],
                        "cell": f"{day_name}_{section_name}",
                        "confidence": confidence,
                        "match_type": match_type,
                        "slot": current_slot_number,
                        "subject": current_subject,
                        "note": "appended_without_header",
                    },
                )

                # DIAGNOSTIC: Log placed hyperlink
                diag.log_hyperlink_placed(
                    hyperlink["text"],
                    current_slot_number,
                    current_subject,
                    f"{day_name}_{section_name}",
                    confidence,
                )

        # If we have fuzzy links but coordinate links exist, inject them (header already added above)
        elif matching_hyperlinks and has_coordinate_hyperlinks:
            # Inject fuzzy links (header was already added above for total count)
            for hyperlink, confidence, match_type in matching_hyperlinks:
                self._inject_hyperlink_inline(cell, hyperlink, row_idx=row_idx)
                pending_hyperlinks.remove(hyperlink)

                logger.info(
                    "hyperlink_placed_inline",
                    extra={
                        "text": hyperlink["text"][:50],
                        "url": hyperlink["url"][:50],
                        "cell": f"{day_name}_{section_name}",
                        "confidence": confidence,
                        "match_type": match_type,
                        "slot": current_slot_number,
                        "subject": current_subject,
                        "note": "mixed_with_coordinate_links",
                    },
                )

                # DIAGNOSTIC: Log placed hyperlink
                diag.log_hyperlink_placed(
                    hyperlink["text"],
                    current_slot_number,
                    current_subject,
                    f"{day_name}_{section_name}",
                    confidence,
                )

        # Now add the text content
        if not has_coordinate_hyperlinks and not append_mode:
            # Add formatted text
            if text:
                MarkdownToDocx.add_multiline_text(cell, text)
                # Apply font formatting (Times New Roman 8pt) to content cells
                # Skip row 1 (days) and column 0 (section labels)
                if row_idx > 0 and col_idx > 0:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.font.name = "Times New Roman"
                            run.font.size = Pt(8)
                            # CRITICAL: Unit/Lesson row must always be BOLD
                            if row_idx == self._get_row_index("unit"):
                                run.font.bold = True
        else:
            # Cell has coordinate-placed hyperlinks OR append mode - append text without clearing
            # Add text with markdown formatting to preserve existing hyperlinks
            if text:
                # Add formatted text line by line, preserving Markdown
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if line.strip():
                        if i == 0:
                            # First line - use MarkdownToDocx for proper formatting
                            new_para = cell.add_paragraph()
                            MarkdownToDocx.add_formatted_text(new_para, line)
                        else:
                            # Subsequent lines
                            MarkdownToDocx.add_paragraph(cell, line)

                # Apply font formatting to newly added paragraphs only
                if row_idx > 0 and col_idx > 0:
                    # Format only the paragraphs we just added
                    num_new_paras = len(lines)
                    for para in cell.paragraphs[-num_new_paras:]:
                        for run in para.runs:
                            run.font.name = "Times New Roman"
                            run.font.size = Pt(8)
                            # CRITICAL: Unit/Lesson row must always be BOLD
                            if row_idx == self._get_row_index("unit"):
                                run.font.bold = True

        # CRITICAL: Final formatting pass - ensure ALL paragraphs have consistent formatting
        # This catches any paragraphs that might have been missed or created with defaults
        if cell.paragraphs:
            for para in cell.paragraphs:
                # Format all paragraphs (including empty placeholders to prevent spacing issues)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                # Ensure font formatting is consistent for content paragraphs
                if para.text.strip() or para.runs:
                    if row_idx > 0 and col_idx > 0:
                        for run in para.runs:
                            # Only update if font is missing or default Arial
                            if not run.font.name or run.font.name == "Arial":
                                run.font.name = "Times New Roman"
                            if not run.font.size or run.font.size != Pt(8):
                                run.font.size = Pt(8)

        # FALLBACK: Append media that belongs to this section but wasn't placed inline
        # This ensures "orphan" media stays with its relevant section
        if section_name and (pending_hyperlinks or pending_images):
            # Check for hyperlinks with matching section hint
            for hyperlink in pending_hyperlinks[:]:
                # Check if this hyperlink belongs to this slot/subject
                if current_slot_number is not None:
                    link_slot = hyperlink.get("_source_slot")
                    if link_slot is not None and link_slot != current_slot_number:
                        continue
                
                # Check section hint
                hint = hyperlink.get("section_hint", "").lower()
                # Simple mapping for common section names
                is_section_match = False
                if hint == section_name:
                    is_section_match = True
                elif section_name == "unit_lesson" and hint in ["unit", "lesson"]:
                    is_section_match = True
                elif section_name == "anticipatory_set" and hint in ["anticipatory", "warm up", "hook"]:
                    is_section_match = True
                elif section_name == "tailored_instruction" and hint in ["instruction", "activity"]:
                    is_section_match = True
                
                if is_section_match:
                    # Append as a new paragraph
                    p = cell.add_paragraph()
                    MarkdownToDocx.add_formatted_text(p, f"Referenced: [{hyperlink['text']}]({hyperlink['url']})")
                    # Format the new paragraph
                    p.paragraph_format.space_after = Pt(0)
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(8)
                    
                    pending_hyperlinks.remove(hyperlink)
                    logger.info("hyperlink_placed_fallback", extra={"text": hyperlink["text"], "section": section_name})

            # Check for images with matching section hint
            for image in pending_images[:]:
                # Check slot/subject (similar to hyperlinks)
                if current_slot_number is not None:
                    img_slot = image.get("_source_slot")
                    if img_slot is not None and img_slot != current_slot_number:
                        continue

                hint = image.get("section_hint", "").lower()
                is_section_match = False
                if hint == section_name:
                    is_section_match = True
                elif section_name == "unit_lesson" and hint in ["unit", "lesson"]:
                    is_section_match = True
                elif section_name == "anticipatory_set" and hint in ["anticipatory", "warm up", "hook"]:
                    is_section_match = True
                elif section_name == "tailored_instruction" and hint in ["instruction", "activity"]:
                    is_section_match = True

                if is_section_match:
                    self._inject_image_inline(cell, image, max_width=1.3) # approx column width
                    pending_images.remove(image)
                    logger.info("image_placed_fallback", extra={"filename": image["filename"], "section": section_name})

        # CRITICAL: Remove placeholder paragraph if no content was actually added
        # This prevents empty cells from showing a placeholder when content is missing
        # Check if cell has any real content (text, hyperlinks, or images)
        has_content = False
        if cell.paragraphs:
            for para in cell.paragraphs:
                # Check if paragraph has content (not just whitespace)
                if para.text.strip() or para.runs:
                    # Check if runs contain actual content (not just formatting)
                    for run in para.runs:
                        if run.text and run.text.strip():
                            has_content = True
                            break
                    if has_content:
                        break
                    # Check for hyperlinks (they might be in XML, not runs)
                    if para._element.xpath(".//w:hyperlink"):
                        has_content = True
                        break

        # If no content was added and we have placeholder paragraphs, remove them
        if not has_content and not has_coordinate_hyperlinks and not append_mode:
            # Check if cell only has empty placeholder paragraphs
            empty_paras = []
            for para in cell.paragraphs:
                if not para.text.strip() and not para.runs:
                    empty_paras.append(para)

            # Remove all empty paragraphs (they're just placeholders)
            for para in empty_paras:
                p = para._element
                p.getparent().remove(p)

        # Match and inject images (existing logic continues)
        if pending_images:
            # Estimate column width (5 columns = ~1.3 inches each)
            estimated_col_width = 6.5 / 5

            if estimated_col_width >= settings.IMAGE_INLINE_MIN_COLUMN_WIDTH_INCHES:
                for image in pending_images[:]:
                    # CRITICAL: Filter images by slot to prevent cross-contamination
                    # Only consider images from the current slot being rendered
                    if current_slot_number is not None:
                        image_slot = image.get("_source_slot")

                        # STRICT: In multi-slot mode, REQUIRE slot metadata
                        if image_slot is None:
                            # Missing metadata - skip to prevent cross-contamination
                            logger.warning(
                                "image_missing_slot_metadata",
                                extra={
                                    "filename": image.get("filename", "unknown"),
                                    "current_slot": current_slot_number,
                                },
                            )
                            continue

                        if image_slot != current_slot_number:
                            # Skip images from other slots
                            logger.debug(
                                "image_filtered_by_slot",
                                extra={
                                    "filename": image["filename"],
                                    "image_slot": image_slot,
                                    "current_slot": current_slot_number,
                                },
                            )
                            continue

                    # Additional filter by subject for extra safety
                    if current_subject is not None:
                        image_subject = image.get("_source_subject")

                        # STRICT: In multi-slot mode, REQUIRE subject metadata
                        if image_subject is None:
                            # Missing metadata - skip to prevent cross-contamination
                            logger.warning(
                                "image_missing_subject_metadata",
                                extra={
                                    "filename": image.get("filename", "unknown"),
                                    "current_subject": current_subject,
                                },
                            )
                            continue

                        if image_subject != current_subject:
                            # Skip images from other subjects
                            logger.debug(
                                "image_filtered_by_subject",
                                extra={
                                    "filename": image["filename"],
                                    "image_subject": image_subject,
                                    "current_subject": current_subject,
                                },
                            )
                            continue

                    # Try structure-based placement first (exact location)
                    if self._try_structure_based_placement(
                        image, day_name, section_name, col_idx
                    ):
                        self._inject_image_inline(
                            cell, image, max_width=estimated_col_width
                        )
                        pending_images.remove(image)

                        logger.info(
                            "image_placed_inline",
                            extra={
                                "filename": image["filename"],
                                "cell": f"{day_name}_{section_name}",
                                "confidence": 1.0,
                                "match_type": "structure_based",
                                "slot": current_slot_number,
                                "subject": current_subject,
                            },
                        )
                    # Fall back to context-based matching
                    elif text:
                        confidence, match_type = self._calculate_match_confidence(
                            text, image, day_name, section_name
                        )

                        if confidence >= settings.MEDIA_MATCH_CONFIDENCE_THRESHOLD:
                            self._inject_image_inline(
                                cell, image, max_width=estimated_col_width
                            )
                            pending_images.remove(image)

                            logger.info(
                                "image_placed_inline",
                                extra={
                                    "filename": image["filename"],
                                    "cell": f"{day_name}_{section_name}",
                                    "confidence": confidence,
                                    "match_type": match_type,
                                    "slot": current_slot_number,
                                    "subject": current_subject,
                                },
                            )
                        else:
                            logger.debug(
                                "image_match_rejected",
                                extra={
                                    "filename": image["filename"],
                                    "cell": f"{day_name}_{section_name}",
                                    "confidence": confidence,
                                },
                            )

    def _format_objective(self, objective: Dict) -> str:
        """Format objective section."""
        if not objective:
            return ""

        parts = []

        if "content_objective" in objective:
            parts.append(f"**Content:** {objective['content_objective']}")

        if "student_goal" in objective:
            parts.append(f"**Student Goal:** {objective['student_goal']}")

        if "wida_objective" in objective:
            parts.append(f"**WIDA/Bilingual:** {objective['wida_objective']}")

        return "\n\n".join(parts)

    def _format_anticipatory_set(self, anticipatory: Dict) -> str:
        """Format anticipatory set section."""
        if not anticipatory:
            return ""

        parts = []

        if "original_content" in anticipatory:
            parts.append(anticipatory["original_content"])

        if "bilingual_bridge" in anticipatory:
            parts.append(f"\n**Bilingual Bridge:** {anticipatory['bilingual_bridge']}")

        return "\n".join(parts)

    def _format_tailored_instruction(
        self,
        instruction: Dict,
        vocabulary_cognates: Optional[List[Dict]] = None,
        sentence_frames: Optional[List[Dict]] = None,
    ) -> str:
        """Format tailored instruction section.

        Args:
            instruction: Tailored instruction dict for the day/slot.
            vocabulary_cognates: Optional list of vocabulary cognate pairs for
                this day. When provided and when a cognate_awareness strategy
                is present in ell_support, this will be rendered as a structured
                "Vocabulary / Cognate Awareness" block after the explanation.
        """
        if not instruction:
            return ""

        parts: List[str] = []

        # Original content
        if "original_content" in instruction:
            parts.append(instruction["original_content"])

        # Co-teaching model
        if "co_teaching_model" in instruction:
            co_teaching = instruction["co_teaching_model"]
            parts.append(
                f"\n**Co-Teaching Model:** {co_teaching.get('model_name', '')}"
            )

            if "phase_plan" in co_teaching:
                parts.append("\n**Phase Plan:**")
                for phase in co_teaching["phase_plan"]:
                    phase_name = phase.get("phase_name", "")
                    minutes = phase.get("minutes", "")
                    parts.append(f"- **{phase_name}** ({minutes} min)")

                    if "bilingual_teacher_role" in phase:
                        parts.append(
                            f"  - Bilingual: {phase['bilingual_teacher_role']}"
                        )
                    if "primary_teacher_role" in phase:
                        parts.append(f"  - Primary: {phase['primary_teacher_role']}")

        # ELL Support
        ell_support = instruction.get("ell_support") or []
        if ell_support:
            parts.append("\n**ELL Support:**")
            has_cognate_awareness = False

            for strategy in ell_support:
                strategy_name = strategy.get("strategy_name", "")
                implementation = strategy.get("implementation", "")
                levels = strategy.get("proficiency_levels", "")
                strategy_id = strategy.get("strategy_id", "")

                parts.append(f"- **{strategy_name}** ({levels}): {implementation}")

                if strategy_id == "cognate_awareness":
                    has_cognate_awareness = True

            # If we have a cognate awareness strategy and structured
            # vocabulary_cognates data, append a formatted vocabulary block.
            if has_cognate_awareness and vocabulary_cognates:
                # Ensure we only render pairs with both english and portuguese
                valid_pairs = [
                    pair
                    for pair in vocabulary_cognates
                    if isinstance(pair, dict)
                    and str(pair.get("english", "")).strip()
                    and str(pair.get("portuguese", "")).strip()
                ]

                if valid_pairs:
                    parts.append("\n**Vocabulary / Cognate Awareness:**")
                    for pair in valid_pairs:
                        english = str(pair.get("english", "")).strip()
                        portuguese = str(pair.get("portuguese", "")).strip()
                        parts.append(f"- **{english}** → *{portuguese}*")

            # Sentence Frames grouped by proficiency level (if provided)
            if sentence_frames:
                # Filter to well-formed frames
                valid_frames = [
                    frame
                    for frame in sentence_frames
                    if isinstance(frame, dict)
                    and str(frame.get("english", "")).strip()
                    and str(frame.get("portuguese", "")).strip()
                    and str(frame.get("proficiency_level", "")).strip()
                ]

                if valid_frames:
                    parts.append("\n**Sentence Frames / Stems / Questions:**")

                    level_order = [
                        ("levels_1_2", "Levels 1-2"),
                        ("levels_3_4", "Levels 3-4"),
                        ("levels_5_6", "Levels 5-6"),
                    ]

                    for level_key, level_label in level_order:
                        frames_for_level = [
                            f
                            for f in valid_frames
                            if f.get("proficiency_level") == level_key
                        ]

                        if not frames_for_level:
                            continue

                        parts.append(f"\n- **{level_label}:**")

                        for frame in frames_for_level:
                            english = str(frame.get("english", "")).strip()
                            portuguese = str(frame.get("portuguese", "")).strip()
                            language_function = str(
                                frame.get("language_function", "")
                            ).strip()

                            parts.append(f"  - PT: *{portuguese}*")

                            if language_function:
                                parts.append(
                                    f"    EN: **{english}** (function: {language_function})"
                                )
                            else:
                                parts.append(f"    EN: **{english}**")

        # Materials
        if "materials" in instruction and instruction["materials"]:
            parts.append("\n**Materials:** " + ", ".join(instruction["materials"]))

        return "\n".join(parts)

    def _format_misconceptions(self, misconceptions: Dict) -> str:
        """Format misconceptions section."""
        if not misconceptions:
            return ""

        parts = []

        if "original_content" in misconceptions:
            parts.append(misconceptions["original_content"])

        if "linguistic_note" in misconceptions:
            ling = misconceptions["linguistic_note"]
            if "note" in ling:
                parts.append(f"\n**Linguistic Note:** {ling['note']}")
            if "prevention_tip" in ling:
                parts.append(f"**Prevention:** {ling['prevention_tip']}")

        return "\n".join(parts)

    def _format_assessment(self, assessment: Dict) -> str:
        """Format assessment section."""
        if not assessment:
            return ""

        parts = []

        if "primary_assessment" in assessment:
            parts.append(f"**Assessment:** {assessment['primary_assessment']}")

        if "bilingual_overlay" in assessment:
            overlay = assessment["bilingual_overlay"]

            if "instrument" in overlay:
                parts.append(f"\n**Instrument:** {overlay['instrument']}")

            if "supports_by_level" in overlay:
                parts.append("\n**Supports by Level:**")
                supports = overlay["supports_by_level"]
                if "levels_1_2" in supports:
                    parts.append(f"- **Levels 1-2:** {supports['levels_1_2']}")
                if "levels_3_4" in supports:
                    parts.append(f"- **Levels 3-4:** {supports['levels_3_4']}")
                if "levels_5_6" in supports:
                    parts.append(f"- **Levels 5-6:** {supports['levels_5_6']}")

        return "\n".join(parts)

    def _try_structure_based_placement(
        self, image: Dict, day_name: str, section_name: str, col_idx: int
    ) -> bool:
        """
        Try to place image using structure-based matching (row label + cell index).

        Args:
            image: Image dictionary with row_label and cell_index
            day_name: Current day being rendered
            section_name: Current section being rendered
            col_idx: Current column index

        Returns:
            True if structure matches (should place here), False otherwise
        """
        # Check if image has structure information
        if not image.get("row_label") or image.get("cell_index") is None:
            return False

        # Map section names to match variations
        section_matches = {
            "unit_lesson": ["unit", "lesson"],
            "objective": ["objective", "goal"],
            "anticipatory_set": ["anticipatory", "warm", "hook"],
            "instruction": ["instruction", "activity", "lesson", "tailored"],
            "misconceptions": ["misconception", "error"],
            "assessment": ["assessment", "check", "evaluate"],
            "homework": ["homework", "assignment"],
        }

        # Check if section matches
        section_match = False
        image_section = image.get("section_hint", "")

        if section_name and image_section:
            # Direct match
            if section_name == image_section:
                section_match = True
            # Check variations
            elif section_name in section_matches:
                keywords = section_matches[section_name]
                if any(kw in image_section for kw in keywords):
                    section_match = True

        # Check if day/column matches
        day_match = image.get("cell_index") == col_idx

        # Both must match for structure-based placement
        return section_match and day_match

    def _calculate_match_confidence(
        self,
        cell_text: str,
        media: Dict,
        day_name: str = None,
        section_name: str = None,
    ) -> tuple:
        """
        Calculate match confidence with multiple strategies.

        Matching strategies (in order):
        1. Exact text match
        2. Semantic similarity (if available)
        3. Fuzzy context match
        4. Hint-based match

        Args:
            cell_text: Text content of the cell
            media: Media dictionary (hyperlink or image)
            day_name: Day name for hint matching
            section_name: Section name for hint matching

        Returns:
            (confidence_score, match_type) tuple
        """
        try:
            from rapidfuzz import fuzz
        except ImportError:
            logger.warning(
                "rapidfuzz_not_installed", extra={"fallback": "exact_match_only"}
            )
            # Fallback to exact matching only
            if "text" in media and media["text"] in cell_text:
                return (1.0, "exact_text")
            return (0.0, "no_match")

        # Strategy 1: Exact text match (hyperlinks only)
        if "text" in media and media["text"] in cell_text:
            return (1.0, "exact_text")

        # Strategy 2: Context fuzzy match with hint-based boosting
        context = media.get("context_snippet", "")
        context_score = 0.0
        hint_matches = 0

        # Normalize day hints for case-insensitive comparison
        day_hint_normalized = None
        if media.get("day_hint"):
            day_hint_normalized = media["day_hint"].lower().strip()

        day_name_normalized = None
        if day_name:
            day_name_normalized = day_name.lower().strip()

        # Count hint matches (case-insensitive)
        if day_name_normalized and day_hint_normalized == day_name_normalized:
            hint_matches += 1
        if section_name and media.get("section_hint") == section_name:
            hint_matches += 1

        if context:
            context_score = fuzz.partial_ratio(context, cell_text) / 100.0

            # NEW: Lower threshold if hints match (bilingual content support)
            if hint_matches == 2:
                # Both hints match - accept lower text similarity
                if context_score >= 0.40:  # Lower bar with strong hints
                    boosted_score = min(1.0, context_score + 0.15)
                    return (
                        boosted_score,
                        f"context_bilingual_with_{hint_matches}_hints",
                    )
            elif hint_matches == 1:
                # One hint matches - slightly lower threshold
                if context_score >= 0.45:
                    boosted_score = min(1.0, context_score + 0.10)
                    return (boosted_score, f"context_with_{hint_matches}_hint")

            # Standard threshold (no hint boost)
            if context_score >= FUZZY_MATCH_THRESHOLD:
                if hint_matches > 0:
                    boosted_score = min(1.0, context_score + (hint_matches * 0.05))
                    return (boosted_score, f"context_with_{hint_matches}_hints")
                return (context_score, "fuzzy_context")

        # Strategy 3: Section + day hint match only (weak signal)
        if hint_matches == 2:
            # Both hints match but no context - moderate confidence
            return (0.5, "hints_only")

        return (0.0, "no_match")

    def _inject_hyperlink_inline(self, cell, hyperlink: Dict, row_idx: int = None):
        """Inject hyperlink into cell on its own line.

        Args:
            cell: Cell object
            hyperlink: Hyperlink dictionary with text and url
            row_idx: Row index (for applying bold to unit/lesson row)
        """
        # CRITICAL: Each hyperlink must start on its own line
        # Create a new paragraph for the hyperlink
        para = cell.add_paragraph()

        # Remove spacing to avoid blank lines
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

        # Add the hyperlink to the new paragraph
        self._add_hyperlink(para, hyperlink["text"], hyperlink["url"])

        # CRITICAL: Unit/Lesson row hyperlinks must be BOLD
        if row_idx == self.UNIT_LESSON_ROW:
            for run in para.runs:
                run.font.bold = True

    def _place_hyperlink_hybrid(
        self, link: Dict, table, structure: StructureMetadata
    ) -> str:
        """
        Place hyperlink using hybrid strategy (v2.0) with detailed diagnostics.

        Strategies (in order):
        1. Coordinate-based (if standard structure)
        2. Label + Day matching (adaptive)
        3. Fuzzy text matching (fallback)
        4. Referenced Links section (last resort)

        Args:
            link: Hyperlink dictionary with v2.0 schema
            table: Output table object
            structure: Detected structure metadata

        Returns:
            Strategy used: 'coordinate', 'label_day', 'fuzzy', or 'fallback'
        """

        # Create diagnostic record
        diagnostic = {
            "link_text": link.get("text", "")[:50],
            "url": link.get("url", "")[:50],
            "input_coords": f"table={link.get('table_idx')}, row={link.get('row_idx')}, cell={link.get('cell_idx')}",
            "row_label": link.get("row_label", ""),
            "col_header": link.get("col_header", ""),
            "day_hint": link.get("day_hint", ""),
            "section_hint": link.get("section_hint", ""),
            "structure_type": structure.structure_type,
            "strategy_attempted": [],
        }

        # Skip non-table links
        if link.get("table_idx") is None:
            diagnostic["strategy_attempted"].append("skipped_non_table")
            diagnostic["result"] = "fallback"
            logger.info("hyperlink_placement_diagnostic", extra=diagnostic)
            return "fallback"

        # Strategy 1: Coordinate-based (if standard structure)
        if structure.structure_type == "standard_8x6":
            diagnostic["strategy_attempted"].append("coordinate")
            if self._try_coordinate_placement(link, table, structure):
                diagnostic["result"] = "success_coordinate"
                logger.info("hyperlink_placement_diagnostic", extra=diagnostic)
                return "coordinate"
            diagnostic["coordinate_failure"] = "mismatch_or_bounds"

        # Strategy 2: Label + Day matching
        diagnostic["strategy_attempted"].append("label_day")
        diagnostic["label_lookup"] = structure.get_row_index(link.get("row_label", ""))
        diagnostic["day_lookup"] = structure.get_col_index(link.get("day_hint", ""))

        if self._try_label_day_placement(link, table, structure):
            diagnostic["result"] = "success_label_day"
            logger.info("hyperlink_placement_diagnostic", extra=diagnostic)
            return "label_day"
        diagnostic["label_day_failure"] = (
            f"row={diagnostic['label_lookup']}, col={diagnostic['day_lookup']}"
        )

        # Strategy 3: Fuzzy matching
        diagnostic["strategy_attempted"].append("fuzzy")
        if self._try_fuzzy_placement(link, table, threshold=FUZZY_MATCH_THRESHOLD):
            diagnostic["result"] = "success_fuzzy"
            logger.info("hyperlink_placement_diagnostic", extra=diagnostic)
            return "fuzzy"
        diagnostic["fuzzy_failure"] = "no_match_above_threshold"

        # Strategy 4: Fallback (will be added to Referenced Links)
        diagnostic["result"] = "fallback"
        logger.warning("hyperlink_placement_fallback", extra=diagnostic)
        return "fallback"

    def _try_coordinate_placement(
        self, link: Dict, table, structure: StructureMetadata
    ) -> bool:
        """Try to place link at exact coordinates."""

        row_idx = link.get("row_idx")
        cell_idx = link.get("cell_idx")

        if row_idx is None or cell_idx is None:
            return False

        # Apply row offset if needed
        target_row = row_idx + structure.row_offset

        # Guard against invalid coordinates
        try:
            if target_row >= len(table.rows):
                logger.warning(
                    f"Row {target_row} out of bounds (table has {len(table.rows)} rows)"
                )
                return False

            row = table.rows[target_row]

            if cell_idx >= len(row.cells):
                logger.warning(
                    f"Cell {cell_idx} out of bounds (row has {len(row.cells)} cells)"
                )
                return False

            cell = row.cells[cell_idx]

            # Place hyperlink
            self._inject_hyperlink_inline(cell, link)

            logger.debug(
                f"Placed '{link['text']}' at coordinates ({target_row}, {cell_idx})"
            )
            return True

        except (IndexError, AttributeError) as e:
            logger.warning(f"Coordinate placement failed for '{link['text']}': {e}")
            return False

    def _try_label_day_placement(
        self, link: Dict, table, structure: StructureMetadata
    ) -> bool:
        """Try to place link using row label + day matching."""

        row_label = link.get("row_label", "").strip().lower().rstrip(":")
        day_hint = link.get("day_hint", "").strip().lower()

        if not row_label or not day_hint:
            return False

        # Find target row
        target_row = structure.get_row_index(row_label)

        # Find target column
        target_col = structure.get_col_index(day_hint)

        if target_row is None or target_col is None:
            logger.debug(
                f"Could not find row/col for '{link['text']}': row={row_label}, day={day_hint}"
            )
            return False

        # Guard against invalid coordinates
        try:
            if target_row >= len(table.rows) or target_col >= len(
                table.rows[target_row].cells
            ):
                logger.warning(
                    f"Label/day placement out of bounds: ({target_row}, {target_col})"
                )
                return False

            cell = table.rows[target_row].cells[target_col]
            self._inject_hyperlink_inline(cell, link)

            logger.debug(
                f"Placed '{link['text']}' via label/day at ({target_row}, {target_col})"
            )
            return True

        except (IndexError, AttributeError) as e:
            logger.warning(f"Label/day placement failed for '{link['text']}': {e}")
            return False

    def _try_fuzzy_placement(self, link: Dict, table, threshold=0.65) -> bool:
        """Try to place link using fuzzy text matching with detailed scoring."""

        best_match = {
            "confidence": 0.0,
            "location": None,
            "cell_text_preview": "",
            "match_type": "none",
        }

        # Iterate through all cells in table
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                # Use existing _calculate_match_confidence method
                # Extract day/section from table structure
                day_name = None
                section_name = None

                # Get day from column header
                if table.rows and cell_idx < len(table.rows[0].cells):
                    col_header = table.rows[0].cells[cell_idx].text.strip().lower()
                    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    for day in days:
                        if day in col_header:
                            day_name = day
                            break

                # Get section from row label
                if row.cells:
                    row_label = row.cells[0].text.strip().lower()
                    if "objective" in row_label:
                        section_name = "objective"
                    elif "instruction" in row_label or "tailored" in row_label:
                        section_name = "instruction"
                    elif "assessment" in row_label:
                        section_name = "assessment"
                    elif "homework" in row_label:
                        section_name = "homework"

                confidence, match_type = self._calculate_match_confidence(
                    cell.text, link, day_name=day_name, section_name=section_name
                )

                # Track best match even if below threshold
                if confidence > best_match["confidence"]:
                    best_match["confidence"] = confidence
                    best_match["location"] = f"({row_idx}, {cell_idx})"
                    best_match["cell_text_preview"] = cell.text[:80]
                    best_match["match_type"] = match_type

                if confidence >= threshold:
                    self._inject_hyperlink_inline(cell, link)
                    logger.debug(
                        f"Placed '{link['text']}' via fuzzy matching "
                        f"at ({row_idx}, {cell_idx}), confidence={confidence:.2f}, "
                        f"match_type={match_type}"
                    )
                    return True

        # Log best match even if it failed
        logger.debug(
            "fuzzy_match_best_attempt",
            extra={
                "link_text": link.get("text", "")[:50],
                "best_confidence": best_match["confidence"],
                "best_location": best_match["location"],
                "threshold": threshold,
                "cell_preview": best_match["cell_text_preview"],
                "match_type": best_match["match_type"],
            },
        )

        return False

    def _inject_image_inline(self, cell, image: Dict, max_width: float):
        """Inject image into cell with width constraints.

        Args:
            cell: Cell object
            image: Image dictionary with base64 data
            max_width: Maximum width in inches
        """
        try:
            image_data = base64.b64decode(image["data"])
            image_stream = BytesIO(image_data)

            # Add to new paragraph
            para = cell.add_paragraph()
            run = para.add_run()
            run.add_picture(
                image_stream, width=Inches(max_width * 0.9)
            )  # 90% of column width

            # Optional: tiny caption
            caption = cell.add_paragraph()
            caption_run = caption.add_run(f"[{image.get('filename', 'image')}]")
            caption_run.font.size = Pt(7)
            caption_run.italic = True

        except Exception as e:
            logger.warning(
                "inline_image_failed",
                extra={"filename": image.get("filename"), "error": str(e)},
            )

    def _append_unmatched_media(
        self, doc: Document, hyperlinks: List[Dict], images: List[Dict]
    ):
        """Append unmatched media to end with context for traceability.

        Args:
            doc: Document object
            hyperlinks: List of unmatched hyperlinks
            images: List of unmatched images
        """
        if hyperlinks:
            doc.add_page_break()
            heading = doc.add_paragraph("Referenced Links")
            heading.runs[0].bold = True
            heading.runs[0].font.size = Pt(12)

            for link in hyperlinks:
                para = doc.add_paragraph()
                try:
                    para.style = "List Bullet"
                except KeyError:
                    para.add_run("• ")

                self._add_hyperlink(para, link["text"], link["url"])

                # Add context hint
                if link.get("context_snippet"):
                    context_para = doc.add_paragraph()
                    context_run = context_para.add_run(
                        f'  Context: "{link["context_snippet"][:80]}..."'
                    )
                    context_run.font.size = Pt(9)
                    context_run.italic = True

        if images:
            if not hyperlinks:
                doc.add_page_break()

            heading = doc.add_paragraph("Attached Images")
            heading.runs[0].bold = True
            heading.runs[0].font.size = Pt(12)

            for i, image in enumerate(images, 1):
                try:
                    image_data = base64.b64decode(image["data"])
                    image_stream = BytesIO(image_data)

                    para = doc.add_paragraph()
                    run = para.add_run()
                    run.add_picture(image_stream, width=Inches(4.0))

                    caption = doc.add_paragraph()
                    caption_run = caption.add_run(
                        f"Image {i}: {image.get('filename', 'Untitled')}"
                    )
                    caption_run.italic = True
                    caption_run.font.size = Pt(10)

                    # Add context hint
                    if image.get("context_snippet"):
                        context_para = doc.add_paragraph()
                        context_run = context_para.add_run(
                            f'Context: "{image["context_snippet"][:80]}..."'
                        )
                        context_run.font.size = Pt(9)
                        context_run.italic = True

                except Exception as e:
                    logger.warning(
                        "fallback_image_failed",
                        extra={"filename": image.get("filename"), "error": str(e)},
                    )

    def _insert_images(self, doc: Document, images: List[Dict]):
        """Insert images at the end of the document.

        Args:
            doc: Document object
            images: List of image dictionaries with base64-encoded data
        """
        if not images:
            return

        try:
            # Add a page break before images section
            doc.add_page_break()

            # Add section header
            heading = doc.add_paragraph()
            heading_run = heading.add_run("Attached Images")
            heading_run.bold = True
            heading_run.font.size = Pt(14)

            # Insert each image
            for i, image in enumerate(images, 1):
                try:
                    # Decode base64 image data
                    image_data = base64.b64decode(image["data"])
                    image_stream = BytesIO(image_data)

                    # Add image with caption
                    paragraph = doc.add_paragraph()
                    run = paragraph.add_run()

                    # Insert image with reasonable width (4 inches)
                    run.add_picture(image_stream, width=Inches(4.0))

                    # Add caption
                    caption = doc.add_paragraph()
                    caption_run = caption.add_run(
                        f"Image {i}: {image.get('filename', 'Untitled')}"
                    )
                    caption_run.italic = True
                    caption_run.font.size = Pt(10)

                except Exception as e:
                    logger.warning(
                        "image_insertion_failed",
                        extra={
                            "image_index": i,
                            "filename": image.get("filename", "unknown"),
                            "error": str(e),
                        },
                    )
        except Exception as e:
            logger.warning("images_insertion_error", extra={"error": str(e)})

    def _restore_hyperlinks(self, doc: Document, hyperlinks: List[Dict]):
        """Restore hyperlinks by adding them at the end of the document.

        Args:
            doc: Document object
            hyperlinks: List of hyperlink dictionaries with text and url
        """
        if not hyperlinks:
            return

        # Log fallback placement for observability
        logger.info(
            "hyperlink_fallback_placement",
            extra={
                "total_fallback_links": len(hyperlinks),
                "links": [
                    {
                        "text": link.get("text", "")[:50],
                        "url": link.get("url", "")[:50],
                        "day_hint": link.get("day_hint"),
                        "section_hint": link.get("section_hint"),
                        "slot": link.get("_source_slot"),
                        "subject": link.get("_source_subject"),
                    }
                    for link in hyperlinks
                ],
            },
        )

        try:
            # Add section header
            heading = doc.add_paragraph()
            heading_run = heading.add_run("Referenced Links")
            heading_run.bold = True
            heading_run.font.size = Pt(12)

            # Add each hyperlink
            for link in hyperlinks:
                try:
                    paragraph = doc.add_paragraph()
                    # Try to use List Bullet style if available, otherwise use default
                    try:
                        paragraph.style = "List Bullet"
                    except KeyError:
                        # Style doesn't exist, add bullet manually
                        paragraph.style = "Normal"
                        paragraph.paragraph_format.left_indent = Inches(0.25)
                        paragraph.paragraph_format.first_line_indent = Inches(-0.25)
                        paragraph.add_run("• ")  # Add bullet manually

                    # Add hyperlink text and URL
                    self._add_hyperlink(paragraph, link["text"], link["url"])

                except Exception as e:
                    logger.warning(
                        "hyperlink_restoration_failed",
                        extra={
                            "text": link.get("text", "unknown"),
                            "url": link.get("url", "unknown"),
                            "error": str(e),
                        },
                    )
        except Exception as e:
            logger.warning("hyperlinks_restoration_error", extra={"error": str(e)})

    def _add_hyperlink(self, paragraph, text: str, url: str):
        """Add a hyperlink to a paragraph.

        Args:
            paragraph: Paragraph object
            text: Display text for the hyperlink
            url: URL to link to
        """
        # Get the paragraph's part
        part = paragraph.part

        # Create relationship to the URL
        r_id = part.relate_to(
            url,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )

        # Create the hyperlink element
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)

        # Create a new run for the hyperlink text
        new_run = OxmlElement("w:r")

        # Set run properties (blue, underlined, Times New Roman 8pt)
        rPr = OxmlElement("w:rPr")

        # Add font (Times New Roman)
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(qn("w:ascii"), "Times New Roman")
        rFonts.set(qn("w:hAnsi"), "Times New Roman")
        rPr.append(rFonts)

        # Add font size (8pt = 16 half-points)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "16")
        rPr.append(sz)

        # Add color (blue)
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0000FF")
        rPr.append(color)

        # Add underline
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

        new_run.append(rPr)

        # Add the text
        text_elem = OxmlElement("w:t")
        text_elem.text = text
        new_run.append(text_elem)

        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)

    def _format_homework(self, homework: Dict) -> str:
        """Format homework section."""
        if not homework:
            return ""

        parts = []

        if "original_content" in homework and homework["original_content"]:
            parts.append(homework["original_content"])

        if "family_connection" in homework:
            parts.append(f"\n**Family Connection:** {homework['family_connection']}")

        return "\n".join(parts)


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: python docx_renderer.py <input.json> <output.docx> [template.docx]"
        )
        print("\nExample:")
        print(
            "  python docx_renderer.py tests/fixtures/valid_lesson_minimal.json output/lesson.docx"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    template_path = (
        sys.argv[3] if len(sys.argv) > 3 else "input/Lesson Plan Template SY'25-26.docx"
    )

    # Load JSON
    with open(input_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Render
    renderer = DOCXRenderer(template_path)
    success = renderer.render(json_data, output_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
