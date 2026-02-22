"""
DOCX Parser package: extract content from primary teacher lesson plan DOCX files.

Public API: DOCXParser, parse_docx, validate_slot_structure.
"""

from .parser import DOCXParser, parse_docx
from .structure import validate_slot_structure

__all__ = ["DOCXParser", "parse_docx", "validate_slot_structure"]
