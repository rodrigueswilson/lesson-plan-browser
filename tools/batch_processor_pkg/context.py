"""
Slot processing context for batch processor.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SlotProcessingContext:
    """Context for processing a single slot across phases.

    This dataclass tracks the state of a slot through the two-phase processing:
    - Phase 1: Sequential file operations (extract content)
    - Phase 2: Parallel LLM processing (transform content)
    """

    slot: Dict[str, Any]
    slot_index: int
    total_slots: int
    primary_file: Optional[str] = None
    extracted_content: Optional[str] = None
    available_days: Optional[List[str]] = None
    no_school_days: Optional[List[str]] = None
    lesson_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cache_hit: bool = False

    # Parallel processing metrics (for analytics)
    is_parallel: bool = False
    parallel_slot_count: Optional[int] = None
    sequential_time_ms: Optional[float] = None
    rate_limit_errors: int = 0
    concurrency_level: Optional[int] = None
    tpm_usage: Optional[int] = None
    rpm_usage: Optional[int] = None
    link_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
