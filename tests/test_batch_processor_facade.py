"""
Minimal regression test for the batch processor facade and package layout.
Ensures the public API and import path remain valid after refactors.
"""
import pytest
from unittest.mock import MagicMock

from tools.batch_processor import (
    BatchProcessor,
    process_batch,
    SlotProcessingContext,
    get_db,
    get_file_manager,
    get_tracker,
)


def test_facade_imports():
    """Public API is importable from tools.batch_processor."""
    assert BatchProcessor is not None
    assert process_batch is not None
    assert SlotProcessingContext is not None
    assert get_db is not None
    assert get_file_manager is not None
    assert get_tracker is not None


def test_batch_processor_instantiation():
    """BatchProcessor can be instantiated with a mock LLM service."""
    mock_llm = MagicMock()
    processor = BatchProcessor(mock_llm)
    assert processor is not None
    assert processor.llm_service is mock_llm


def test_slot_processing_context_import():
    """SlotProcessingContext can be used for type/construction if needed."""
    ctx = SlotProcessingContext(slot={"slot_number": 1}, slot_index=0, total_slots=1)
    assert ctx.slot == {"slot_number": 1}
    assert ctx.slot_index == 0
    assert ctx.total_slots == 1
