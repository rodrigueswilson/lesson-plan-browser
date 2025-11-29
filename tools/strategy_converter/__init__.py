"""
Strategy Converter Package
Bidirectional JSON↔Markdown conversion for bilingual teaching strategies.
"""

__version__ = '1.0.0'
__author__ = 'Bilingual Weekly Plan Builder Team'

from .json_to_md import JsonToMarkdownConverter
from .md_to_json import MarkdownToJsonConverter
from .schema_validator import SchemaValidator

__all__ = [
    'JsonToMarkdownConverter',
    'MarkdownToJsonConverter',
    'SchemaValidator'
]
