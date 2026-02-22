"""
Table and cell filling for DOCX rendering.

Re-exports fill, format, and placement functions for use by the renderer.
"""

from .fill import (
    fill_cell,
    fill_day,
    fill_metadata,
    fill_multi_slot_day,
    fill_single_slot_day,
)
from .format import (
    filter_valid_sentence_frames,
    filter_valid_vocabulary_pairs,
    format_anticipatory_set,
    format_assessment,
    format_homework,
    format_misconceptions,
    format_objective,
    format_tailored_instruction,
)
from .placement import (
    abbreviate_content,
    calculate_match_confidence,
    extract_unique_subjects,
    extract_unique_teachers,
    try_structure_based_placement,
)

__all__ = [
    "abbreviate_content",
    "calculate_match_confidence",
    "extract_unique_subjects",
    "extract_unique_teachers",
    "fill_cell",
    "fill_day",
    "fill_metadata",
    "fill_multi_slot_day",
    "fill_single_slot_day",
    "filter_valid_sentence_frames",
    "filter_valid_vocabulary_pairs",
    "format_anticipatory_set",
    "format_assessment",
    "format_homework",
    "format_misconceptions",
    "format_objective",
    "format_tailored_instruction",
    "try_structure_based_placement",
]
