"""
Batch processor implementation package.

Used by tools/batch_processor.py (facade). Public API remains
BatchProcessor, process_batch, SlotProcessingContext from tools.batch_processor.
"""

from tools.batch_processor_pkg.context import SlotProcessingContext

__all__ = ["SlotProcessingContext"]
