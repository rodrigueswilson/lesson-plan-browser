"""
Parallel LLM execution for batch processor slots.
"""

import asyncio
from typing import Any, List, Optional

from backend.config import settings
from backend.telemetry import logger

from tools.batch_processor_pkg.context import SlotProcessingContext


async def process_slots_parallel_llm(
    processor: Any,
    contexts: List[SlotProcessingContext],
    week_of: str,
    provider: str,
    plan_id: Optional[str] = None,
) -> List[SlotProcessingContext]:
    """
    Process all slots' LLM calls in parallel with concurrency limit.

    Args:
        processor: BatchProcessor instance (must have _transform_slot_with_llm)
        contexts: List of SlotProcessingContext with extracted_content
        week_of: Week date range
        provider: LLM provider name
        plan_id: Plan ID for progress tracking

    Returns:
        List of updated SlotProcessingContext with lesson_json
    """
    limit = settings.MAX_CONCURRENT_LLM_REQUESTS
    semaphore = asyncio.Semaphore(limit)

    async def limited_transform(ctx: SlotProcessingContext) -> SlotProcessingContext:
        async with semaphore:
            return await processor._transform_slot_with_llm(
                ctx, week_of, provider, plan_id
            )

    tasks = [limited_transform(ctx) for ctx in contexts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            contexts[i].error = str(result)
            logger.error(
                "parallel_llm_slot_failed",
                extra={
                    "slot_index": contexts[i].slot_index,
                    "slot_number": contexts[i].slot.get("slot_number"),
                    "error": str(result),
                },
            )
        else:
            contexts[i] = result

    return contexts
