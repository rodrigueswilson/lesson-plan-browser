"""
Batch processor facade: re-exports public API from the package.

Import from here for compatibility: from tools.batch_processor import BatchProcessor, process_batch, SlotProcessingContext

Tests that patch get_db, get_file_manager, get_tracker on this module will affect the orchestrator
because the orchestrator imports these from here.
"""

from backend.database import get_db
from backend.file_manager import get_file_manager
from backend.performance_tracker import get_tracker

from tools.batch_processor_pkg.context import SlotProcessingContext
from tools.batch_processor_pkg.orchestrator import (
    MOCK_LLM_CALL,
    BatchProcessor,
    process_batch,
)

__all__ = [
    "BatchProcessor",
    "SlotProcessingContext",
    "MOCK_LLM_CALL",
    "process_batch",
    "get_db",
    "get_file_manager",
    "get_tracker",
]
