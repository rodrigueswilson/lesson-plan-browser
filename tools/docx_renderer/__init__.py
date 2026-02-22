"""
DOCX Renderer package: template-based DOCX generation from validated JSON.

Public API: DOCXRenderer, FUZZY_MATCH_THRESHOLD. Logger is exposed for tests.
"""

from backend.telemetry import logger
from .renderer import DOCXRenderer
from .style import FUZZY_MATCH_THRESHOLD

__all__ = ["DOCXRenderer", "FUZZY_MATCH_THRESHOLD", "logger"]
