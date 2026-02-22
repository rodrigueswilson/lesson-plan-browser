"""
Fill logic for DOCX table/cell rendering.

Provides: fill_metadata, fill_day, fill_single_slot_day, fill_multi_slot_day, fill_cell.
Re-exports from fill_metadata, fill_day, and fill_cell modules.
"""

from .fill_cell import fill_cell
from .fill_day import fill_day, fill_multi_slot_day, fill_single_slot_day
from .fill_metadata import fill_metadata

__all__ = [
    "fill_cell",
    "fill_day",
    "fill_metadata",
    "fill_multi_slot_day",
    "fill_single_slot_day",
]
