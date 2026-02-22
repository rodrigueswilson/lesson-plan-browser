"""
Fill metadata table (Table 0) for DOCX rendering.
"""

from typing import Dict

from .. import logger
from .. import style as _style_module
from backend.utils.metadata_utils import get_homeroom, get_subject, get_teacher_name

sanitize_xml_text = _style_module.sanitize_xml_text


def fill_metadata(renderer, doc, json_data: Dict) -> None:
    """
    Fill metadata table (Table 0).

    Template structure:
    | Name: | Grade: | Homeroom: | Subject: | Week of: | Room: |

    For multi-slot lessons, extracts slot-specific metadata from the first slot
    found across all days, using standardized metadata utilities.

    Args:
        renderer: DOCXRenderer instance
        doc: Document object
        json_data: Full lesson plan JSON (supports both single-slot and multi-slot)
    """
    metadata = json_data.get("metadata", {})

    representative_slot = None
    if "days" in json_data and isinstance(json_data["days"], dict):
        all_slots = []
        for day_name, day_data in json_data["days"].items():
            if day_data and "slots" in day_data and isinstance(day_data["slots"], list):
                all_slots.extend(day_data["slots"])
        if all_slots:
            sorted_slots = sorted(all_slots, key=lambda x: x.get("slot_number", 0))
            representative_slot = sorted_slots[0]

    table = doc.tables[renderer.METADATA_TABLE_IDX]
    row = table.rows[0]

    teacher_name = get_teacher_name(metadata, slot=representative_slot)
    cell = row.cells[0]
    cell.text = ""
    para = cell.paragraphs[0]
    run1 = para.add_run(sanitize_xml_text("Name: "))
    renderer._force_font_arial10(run1, is_bold=True)
    run2 = para.add_run(
        sanitize_xml_text(
            teacher_name if teacher_name and teacher_name != "Unknown" else "Unknown"
        )
    )
    renderer._force_font_arial10(run2, is_bold=False)

    grade = None
    if representative_slot:
        grade = representative_slot.get("grade")
    if not grade or grade == "N/A":
        grade = metadata.get("grade")
    if grade and grade != "Unknown" and grade != "N/A":
        cell = row.cells[1]
        cell.text = ""
        para = cell.paragraphs[0]
        run1 = para.add_run(sanitize_xml_text("Grade: "))
        renderer._force_font_arial10(run1, is_bold=True)
        run2 = para.add_run(sanitize_xml_text(grade))
        renderer._force_font_arial10(run2, is_bold=False)

    homeroom = get_homeroom(metadata, slot=representative_slot)
    if homeroom and homeroom != "Unknown":
        cell = row.cells[2]
        cell.text = ""
        para = cell.paragraphs[0]
        run1 = para.add_run(sanitize_xml_text("Homeroom: "))
        renderer._force_font_arial10(run1, is_bold=True)
        run2 = para.add_run(sanitize_xml_text(homeroom))
        renderer._force_font_arial10(run2, is_bold=False)

    subject = get_subject(metadata, slot=representative_slot)
    if subject and subject != "Unknown":
        cell = row.cells[3]
        cell.text = ""
        para = cell.paragraphs[0]
        run1 = para.add_run(sanitize_xml_text("Subject: "))
        renderer._force_font_arial10(run1, is_bold=True)
        run2 = para.add_run(sanitize_xml_text(subject))
        renderer._force_font_arial10(run2, is_bold=False)

    week_of = metadata.get("week_of", "Unknown")
    if week_of and week_of != "Unknown":
        cell = row.cells[4]
        cell.text = ""
        para = cell.paragraphs[0]
        run1 = para.add_run(sanitize_xml_text("Week of: "))
        renderer._force_font_arial10(run1, is_bold=True)
        run2 = para.add_run(sanitize_xml_text(week_of))
        renderer._force_font_arial10(run2, is_bold=False)

    if len(row.cells) > 5:
        room = None
        if representative_slot:
            room = representative_slot.get("room")
        if (
            not room
            or room == "N/A"
            or (isinstance(room, str) and not room.strip())
        ):
            room = metadata.get("room", "")
        if room and room.strip() and room != "N/A" and room != "Unknown":
            cell = row.cells[5]
            cell.text = ""
            para = cell.paragraphs[0]
            run1 = para.add_run(sanitize_xml_text("Room: "))
            renderer._force_font_arial10(run1, is_bold=True)
            run2 = para.add_run(sanitize_xml_text(room))
            renderer._force_font_arial10(run2, is_bold=False)
