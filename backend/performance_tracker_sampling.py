"""
Sampling and critical-operation logic for performance tracking.
"""

import random
from typing import FrozenSet

CRITICAL_OPERATIONS: FrozenSet[str] = frozenset([
    "batch_process",
    "plan_generation",
    "llm_call",
    "llm_api_call",
])


def should_track_operation(
    enabled: bool,
    operation_type: str,
    debug_mode: bool,
    sampling_rate: float,
) -> bool:
    """
    Return True if this operation should be tracked.

    Critical operations are always tracked. Others are tracked according to
    sampling_rate unless debug_mode is True.
    """
    if not enabled:
        return False
    if operation_type in CRITICAL_OPERATIONS:
        return True
    if debug_mode:
        return True
    return random.random() <= sampling_rate
