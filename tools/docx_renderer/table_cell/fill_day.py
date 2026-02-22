"""
Fill day and slot data for DOCX table rendering (single-slot and multi-slot).
"""

from typing import Any, Dict, List, Optional

from .. import logger
from backend.services.sorting_utils import sort_slots
from backend.utils.metadata_utils import get_teacher_name

from . import format as format_module
from . import placement as placement_module
from .fill_cell import fill_cell


def fill_day(
    renderer,
    doc,
    day_name: str,
    day_data: Dict,
    pending_hyperlinks: List[Dict] = None,
    pending_images: List[Dict] = None,
    slot_number: int = None,
    subject: str = None,
) -> None:
    """
    Fill a single day's data with media injection.

    Args:
        renderer: DOCXRenderer instance
        doc: Document object
        day_name: Day name (monday, tuesday, etc.)
        day_data: Day's lesson plan data (can be single-slot or multi-slot)
        pending_hyperlinks: List of hyperlinks awaiting placement
        pending_images: List of images awaiting placement
        slot_number: Slot number for filtering (if rendering single slot)
        subject: Subject name for filtering (if rendering single slot)
    """
    table = doc.tables[renderer.DAILY_PLANS_TABLE_IDX]
    col_idx = renderer._get_col_index(day_name)
    if col_idx == -1:
        return

    hyperlinks_before = len(pending_hyperlinks) if pending_hyperlinks else 0

    if "slots" in day_data and isinstance(day_data["slots"], list):
        metadata = getattr(renderer, "_current_metadata", {})
        fill_multi_slot_day(
            renderer,
            table,
            col_idx,
            day_data["slots"],
            metadata=metadata,
            day_name=day_name,
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
        )
    else:
        fill_single_slot_day(
            renderer,
            table,
            col_idx,
            day_data,
            day_name=day_name,
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            slot_number=slot_number,
            subject=subject,
        )

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


def fill_single_slot_day(
    renderer,
    table,
    col_idx: int,
    day_data: Dict,
    day_name: str = None,
    pending_hyperlinks: List[Dict] = None,
    pending_images: List[Dict] = None,
    slot_number: int = None,
    subject: str = None,
) -> None:
    """
    Fill a single slot's data for one day with media injection.
    """
    unit_lesson = day_data.get("unit_lesson", "")
    if unit_lesson and "no school" in unit_lesson.lower():
        fill_cell(
            renderer,
            table,
            renderer.UNIT_LESSON_ROW,
            col_idx,
            unit_lesson,
            day_name=day_name,
            section_name="unit_lesson",
            pending_hyperlinks=pending_hyperlinks,
            pending_images=pending_images,
            current_slot_number=slot_number,
            current_subject=subject,
        )
        for row_label in [
            "objective",
            "anticipatory",
            "instruction",
            "misconception",
            "assessment",
            "homework",
        ]:
            row_idx = renderer._get_row_index(row_label)
            if row_idx != -1:
                table.rows[row_idx].cells[col_idx].text = ""
        return

    fill_cell(
        renderer,
        table,
        renderer._get_row_index("unit"),
        col_idx,
        unit_lesson,
        day_name=day_name,
        section_name="unit_lesson",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    objective_text = format_module.format_objective(renderer, day_data.get("objective", {}))
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("objective"),
        col_idx,
        objective_text,
        day_name=day_name,
        section_name="objective",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    anticipatory_text = format_module.format_anticipatory_set(
        renderer, day_data.get("anticipatory_set", {})
    )
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("anticipatory"),
        col_idx,
        anticipatory_text,
        day_name=day_name,
        section_name="anticipatory_set",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    instruction_text = format_module.format_tailored_instruction(
        renderer,
        day_data.get("tailored_instruction", {}),
        day_data.get("vocabulary_cognates"),
        day_data.get("sentence_frames"),
    )
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("instruction"),
        col_idx,
        instruction_text,
        day_name=day_name,
        section_name="instruction",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    misconceptions_text = format_module.format_misconceptions(
        renderer, day_data.get("misconceptions", {})
    )
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("misconception"),
        col_idx,
        misconceptions_text,
        day_name=day_name,
        section_name="misconceptions",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    assessment_text = format_module.format_assessment(
        renderer, day_data.get("assessment", {})
    )
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("assessment"),
        col_idx,
        assessment_text,
        day_name=day_name,
        section_name="assessment",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )

    homework_text = format_module.format_homework(
        renderer, day_data.get("homework", "")
    )
    fill_cell(
        renderer,
        table,
        renderer._get_row_index("homework"),
        col_idx,
        homework_text,
        day_name=day_name,
        section_name="homework",
        pending_hyperlinks=pending_hyperlinks,
        pending_images=pending_images,
        current_slot_number=slot_number,
        current_subject=subject,
    )


def _format_slot_field(
    renderer, field_name: str, slot_content: Any
) -> Optional[str]:
    """Format a slot field using the appropriate format function."""
    if field_name == "unit_lesson":
        return slot_content if isinstance(slot_content, str) else None
    if field_name == "objective":
        return format_module.format_objective(renderer, slot_content)
    if field_name == "anticipatory_set":
        return format_module.format_anticipatory_set(renderer, slot_content)
    if field_name == "tailored_instruction":
        return format_module.format_tailored_instruction(
            renderer,
            slot_content,
            slot_content.get("vocabulary_cognates") if isinstance(slot_content, dict) else None,
            slot_content.get("sentence_frames") if isinstance(slot_content, dict) else None,
        )
    if field_name == "misconceptions":
        return format_module.format_misconceptions(renderer, slot_content)
    if field_name == "assessment":
        return format_module.format_assessment(renderer, slot_content)
    if field_name == "homework":
        return format_module.format_homework(renderer, slot_content)
    return None


def fill_multi_slot_day(
    renderer,
    table,
    col_idx: int,
    slots: List[Dict],
    metadata: Dict = None,
    day_name: str = None,
    pending_hyperlinks: List[Dict] = None,
    pending_images: List[Dict] = None,
) -> None:
    """
    Fill multiple slots' data for one day, with per-slot hyperlink placement.
    """
    if not slots:
        return

    sorted_slots = sort_slots(slots)
    num_slots = len(sorted_slots)

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

    rows_config = [
        ("unit_lesson", renderer._get_row_index("unit"), "[No unit/lesson specified]", 100),
        ("objective", renderer._get_row_index("objective"), "[No objective specified]", None),
        ("anticipatory_set", renderer._get_row_index("anticipatory"), None, None),
        ("tailored_instruction", renderer._get_row_index("instruction"), None, None),
        ("misconceptions", renderer._get_row_index("misconception"), None, None),
        ("assessment", renderer._get_row_index("assessment"), None, None),
        ("homework", renderer._get_row_index("homework"), None, 100),
    ]

    if metadata is None:
        metadata = {}

    for (field_name, row_idx, placeholder_text, max_length) in rows_config:
        written_any = False

        for i, slot in enumerate(sorted_slots):
            slot_num = slot.get("slot_number", "?")
            subject = slot.get("subject", "Unknown")
            teacher = get_teacher_name(metadata, slot=slot)
            has_content = slots_have_content[i]

            is_no_school = "no school" in (slot.get("unit_lesson") or "").lower()
            if is_no_school and field_name != "unit_lesson":
                continue

            slot_header = f"**Slot {slot_num}: {subject}**"
            if teacher:
                slot_header += f" ({teacher})"

            slot_content = slot.get(field_name)
            if slot_content:
                slot_text = _format_slot_field(renderer, field_name, slot_content)
                if slot_text is None and field_name == "unit_lesson":
                    slot_text = slot_content
                if slot_text:
                    slot_text = placement_module.abbreviate_content(
                        renderer, slot_text, num_slots, max_length=max_length
                    )
                    slot_text = f"{slot_header}\n{slot_text}"
                else:
                    slot_text = None
            elif has_content and placeholder_text:
                slot_text = f"{slot_header}\n{placeholder_text}"
            else:
                slot_text = None

            if not slot_text:
                continue

            has_next_slot_with_content = False
            for j in range(i + 1, len(sorted_slots)):
                next_slot = sorted_slots[j]
                next_slot_content = next_slot.get(field_name)
                next_has_content = slots_have_content[j]
                if next_slot_content:
                    next_text = _format_slot_field(renderer, field_name, next_slot_content)
                    if next_text is None and field_name == "unit_lesson":
                        next_text = next_slot_content
                    if next_text:
                        has_next_slot_with_content = True
                        break
                elif next_has_content and placeholder_text:
                    has_next_slot_with_content = True
                    break

            if has_next_slot_with_content:
                slot_text += "\n\n---"

            fill_cell(
                renderer,
                table,
                row_idx,
                col_idx,
                slot_text,
                day_name=day_name,
                section_name=field_name,
                pending_hyperlinks=pending_hyperlinks,
                pending_images=pending_images,
                current_slot_number=slot_num,
                current_subject=subject,
                append_mode=written_any,
            )
            written_any = True
