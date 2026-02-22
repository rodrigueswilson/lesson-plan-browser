"""
Placement and extraction helpers for table/cell filling.

Provides: extract_unique_teachers, extract_unique_subjects, abbreviate_content,
try_structure_based_placement, calculate_match_confidence.
"""

from typing import Dict, List, Tuple

from .. import logger
from backend.utils.metadata_utils import get_teacher_name

from ..style import FUZZY_MATCH_THRESHOLD


def extract_unique_teachers(renderer, json_data: Dict) -> List[str]:
    """
    Extract unique teacher names from all slots in a multi-slot structure.

    Args:
        renderer: DOCXRenderer instance (for attribute access; not used here)
        json_data: Full lesson plan JSON with days/slots structure

    Returns:
        Sorted list of unique teacher names
    """
    teachers = set()
    metadata = json_data.get("metadata", {})
    if "days" in json_data:
        for day_data in json_data["days"].values():
            if day_data and "slots" in day_data:
                for slot in day_data["slots"]:
                    slot_teacher = get_teacher_name(metadata, slot=slot)
                    if slot_teacher and slot_teacher != "Unknown":
                        teachers.add(slot_teacher)
    return sorted(teachers)


def extract_unique_subjects(renderer, json_data: Dict) -> List[str]:
    """
    Extract unique subjects from all slots in a multi-slot structure.

    Args:
        renderer: DOCXRenderer instance (unused)
        json_data: Full lesson plan JSON with days/slots structure

    Returns:
        Sorted list of unique subjects
    """
    subjects = set()
    if "days" in json_data:
        for day_data in json_data["days"].values():
            if day_data and "slots" in day_data:
                for slot in day_data["slots"]:
                    if slot.get("subject"):
                        subjects.add(slot["subject"])
    return sorted(subjects)


def abbreviate_content(
    renderer, content: str, num_slots: int, max_length: int = None
) -> str:
    """
    Abbreviate content based on number of slots to ensure it fits in template cells.

    Args:
        renderer: DOCXRenderer instance (unused)
        content: Original content text
        num_slots: Number of slots being displayed
        max_length: Optional max length override

    Returns:
        Abbreviated content with ellipsis if truncated
    """
    if not content:
        return content

    if max_length is None:
        if num_slots <= 2:
            max_length = 500
        elif num_slots == 3:
            max_length = 300
        elif num_slots == 4:
            max_length = 200
        else:
            max_length = 150

    if len(content) > max_length:
        truncated = content[:max_length]
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")
        boundary = max(last_period, last_newline)
        if boundary > max_length * 0.7:
            return truncated[: boundary + 1] + "..."
        else:
            last_space = truncated.rfind(" ")
            if last_space > 0:
                return truncated[:last_space] + "..."
            return truncated + "..."

    return content


def try_structure_based_placement(
    renderer, image: Dict, day_name: str, section_name: str, col_idx: int
) -> bool:
    """
    Try to place image using structure-based matching (row label + cell index).

    Args:
        renderer: DOCXRenderer instance (unused)
        image: Image dictionary with row_label and cell_index
        day_name: Current day being rendered
        section_name: Current section being rendered
        col_idx: Current column index

    Returns:
        True if structure matches (should place here), False otherwise
    """
    if not image.get("row_label") or image.get("cell_index") is None:
        return False

    section_matches = {
        "unit_lesson": ["unit", "lesson"],
        "objective": ["objective", "goal"],
        "anticipatory_set": ["anticipatory", "warm", "hook"],
        "instruction": ["instruction", "activity", "lesson", "tailored"],
        "misconceptions": ["misconception", "error"],
        "assessment": ["assessment", "check", "evaluate"],
        "homework": ["homework", "assignment"],
    }

    section_match = False
    image_section = image.get("section_hint", "")

    if section_name and image_section:
        if section_name == image_section:
            section_match = True
        elif section_name in section_matches:
            keywords = section_matches[section_name]
            if any(kw in image_section for kw in keywords):
                section_match = True

    day_match = image.get("cell_index") == col_idx
    return section_match and day_match


def calculate_match_confidence(
    renderer,
    cell_text: str,
    media: Dict,
    day_name: str = None,
    section_name: str = None,
) -> Tuple[float, str]:
    """
    Calculate match confidence with multiple strategies.

    Matching strategies (in order):
    1. Exact text match
    2. Semantic similarity (if available)
    3. Fuzzy context match
    4. Hint-based match

    Args:
        renderer: DOCXRenderer instance (unused except for type)
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
        if "text" in media and media["text"] in cell_text:
            return (1.0, "exact_text")
        return (0.0, "no_match")

    day_hint_normalized = None
    if media.get("day_hint"):
        day_hint_normalized = media["day_hint"].lower().strip()

    day_name_normalized = None
    if day_name:
        day_name_normalized = day_name.lower().strip()

    if day_hint_normalized and day_name_normalized:
        if day_hint_normalized != day_name_normalized:
            return (0.0, "day_mismatch")

    if "text" in media and media["text"] in cell_text:
        return (1.0, "exact_text")

    context = media.get("context_snippet", "")
    context_score = 0.0
    hint_matches = 0

    if day_name_normalized and day_hint_normalized == day_name_normalized:
        hint_matches += 1

    if section_name:
        hint = (media.get("section_hint") or "").lower()
        section_mappings = {
            "unit_lesson": ["unit", "lesson", "module"],
            "objective": ["objective", "goal", "swbat"],
            "anticipatory_set": ["anticipatory", "warm up", "hook", "do now", "entry"],
            "tailored_instruction": [
                "instruction",
                "activity",
                "procedure",
                "lesson",
                "tailored",
                "differentiation",
            ],
            "misconceptions": ["misconception", "misconceptions", "error", "pitfall"],
            "assessment": ["assessment", "check", "evaluate", "exit ticket"],
            "homework": ["homework", "assignment", "practice"],
        }
        if hint == section_name:
            hint_matches += 1
        elif section_name in section_mappings:
            if hint in section_mappings[section_name]:
                hint_matches += 1
            elif any(
                kw in hint for kw in section_mappings[section_name] if len(kw) > 3
            ):
                hint_matches += 1

    if context:
        context_score = fuzz.partial_ratio(context, cell_text) / 100.0

        if hint_matches == 2:
            if context_score >= 0.40:
                boosted_score = min(1.0, context_score + 0.15)
                return (
                    boosted_score,
                    f"context_bilingual_with_{hint_matches}_hints",
                )
        elif hint_matches == 1:
            if context_score >= 0.45:
                boosted_score = min(1.0, context_score + 0.10)
                return (boosted_score, f"context_with_{hint_matches}_hint")

        if context_score >= FUZZY_MATCH_THRESHOLD:
            if hint_matches > 0:
                boosted_score = min(1.0, context_score + (hint_matches * 0.05))
                return (boosted_score, f"context_with_{hint_matches}_hints")
            return (context_score, "fuzzy_context")

    if hint_matches == 2:
        return (0.5, "hints_only")

    return (0.0, "no_match")
