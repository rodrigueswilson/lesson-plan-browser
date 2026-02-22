"""
Batch processor for handling multiple class slots and generating combined lesson plans.
Processes all user's class slots and combines them into a single DOCX output.
"""

import asyncio
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from docx import Document

from backend.config import settings
from backend.llm_service import LLMService
from backend.progress import progress_tracker
from tools.batch_processor import get_db, get_file_manager, get_tracker
from backend.schema import OriginalLessonPlan
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.telemetry import logger
from backend.utils.date_formatter import format_week_dates
from tools.batch_processor_pkg.context import SlotProcessingContext
from tools.batch_processor_pkg.helpers import (
    build_teacher_name,
    calculate_week_number,
    get_week_num,
    no_school_day_stub,
)
from tools.batch_processor_pkg.hyperlink_scrubber import (
    restore_hyperlinks,
    scrub_hyperlinks,
)
from tools.batch_processor_pkg.slot_schema import (
    convert_single_slot_to_slots_format,
    map_day_content_to_schema,
    sanitize_slot as slot_schema_sanitize_slot,
    sanitize_value as slot_schema_sanitize_value,
)
from tools.batch_processor_pkg import combine as combine_module
from tools.batch_processor_pkg import slot_flow as slot_flow_module
from tools.batch_processor_pkg import week_flow as week_flow_module
from tools.batch_processor_pkg import combined_original as combined_original_module
from tools.batch_processor_pkg import extraction as extraction_module
from tools.batch_processor_pkg import signatures as signatures_module
from tools.batch_processor_pkg.extraction import resolve_primary_file as extraction_resolve_primary_file
from tools.batch_processor_pkg import transform as transform_module
from tools.batch_processor_pkg import persistence as persistence_module
from tools.docx_parser import DOCXParser

# DEBUG FLAG: Set to True to skip actual LLM calls and return mock data
# This helps isolate where the ModelPrivateAttr error is occurring
MOCK_LLM_CALL = False  # Changed to False to enable real LLM calls


class BatchProcessor:
    """Batch processor for multi-slot lesson plan generation."""

    def __init__(self, llm_service: LLMService):
        """Initialize batch processor.

        Args:
            llm_service: LLM service instance for transformations
        """
        self.llm_service = llm_service
        self.db = get_db()
        self.tracker = get_tracker()
        self.get_file_manager = get_file_manager
        self.get_db = get_db
        self._file_locks = {}  # Cache of asyncio.Lock per file path

    def _build_teacher_name(self, user: Dict[str, Any], slot: Dict[str, Any]) -> str:
        """Build teacher name as "Primary First Last / Bilingual First Last"."""
        return build_teacher_name(user, slot)

    def _no_school_day_stub(self) -> Dict[str, Any]:
        """Return the minimal day structure for a No School day (shared by sequential and parallel paths)."""
        return no_school_day_stub()

    def _scrub_hyperlinks(self, context: SlotProcessingContext):
        """Pre-processing: Replace links with [[LINK_n]] placeholders, tracking which day they belong to."""
        scrub_hyperlinks(context)

    def _restore_hyperlinks(
        self, data: Any, link_map: Dict[str, Dict[str, Any]]
    ) -> Tuple[Any, set]:
        """Post-processing: Recursively swap placeholders back for original links with day-matching validation."""
        return restore_hyperlinks(data, link_map)

    async def process_user_week(
        self,
        user_id: str,
        week_of: str,
        provider: str = "openai",
        week_folder_path: Optional[str] = None,
        slot_ids: Optional[list] = None,
        plan_id: Optional[str] = None,
        partial: bool = False,
        missing_only: bool = False,
        force_slots: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Process all class slots for a user's week. Delegates to week_flow.run_process_user_week."""
        return await week_flow_module.run_process_user_week(
            self,
            user_id,
            week_of,
            provider,
            week_folder_path=week_folder_path,
            slot_ids=slot_ids,
            plan_id=plan_id,
            partial=partial,
            missing_only=missing_only,
            force_slots=force_slots,
        )

    def _sanitize_value(self, value: Any) -> Any:
        """Recursively sanitize a value to remove ModelPrivateAttr objects."""
        return slot_schema_sanitize_value(value)

    async def _open_docx_with_retry(
        self,
        file_path: str,
        plan_id: Optional[str] = None,
        slot_number: Optional[int] = None,
        subject: Optional[str] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> DOCXParser:
        """Open DOCX file with retry logic. Delegates to extraction module."""
        return await extraction_module.open_docx_with_retry(
            self, file_path, plan_id, slot_number, subject, max_retries, initial_delay
        )

    def _sanitize_slot(self, slot: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure slot dictionary contains no ModelPrivateAttr objects."""
        return slot_schema_sanitize_slot(slot)

    def _convert_single_slot_to_slots_format(
        self, lesson_json: Dict[str, Any], slot_number: int, subject: str
    ) -> Dict[str, Any]:
        """Convert single-slot lesson_json to slots format."""
        return convert_single_slot_to_slots_format(lesson_json, slot_number, subject)

    def _map_day_content_to_schema(
        self,
        day_content: Dict[str, str],
        slot_info: Dict[str, Any],
        day_hyperlinks: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Map raw extracted string content to OriginalDayPlanSingleSlot schema."""
        return map_day_content_to_schema(day_content, slot_info, day_hyperlinks)

    async def _persist_original_lesson_plan(
        self,
        slot: Dict[str, Any],
        week_of: str,
        primary_file: str,
        teacher_name: str,
        content: Dict[str, Any],
        hyperlinks: List[Dict[str, Any]],
        available_days: Optional[List[str]],
        plan_id: Optional[str] = None,
    ) -> Optional[str]:
        """Helper to persist original lesson plan data to the database. Delegates to persistence module."""
        return await persistence_module.persist_original_lesson_plan(
            self.db,
            getattr(self, "_current_user_id", ""),
            slot,
            week_of,
            primary_file,
            teacher_name,
            content,
            hyperlinks,
            available_days,
            plan_id,
        )

    async def _extract_slot_content(
        self,
        context: SlotProcessingContext,
        week_of: str,
        week_folder_path: Optional[str] = None,
        user_base_path: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> SlotProcessingContext:
        """Phase 1: Extract content from DOCX file. Delegates to extraction module."""
        return await extraction_module.extract_slot_content(
            self, context, week_of, week_folder_path, user_base_path, plan_id
        )

    async def _transform_slot_with_llm(
        self,
        context: SlotProcessingContext,
        week_of: str,
        provider: str,
        plan_id: Optional[str] = None,
    ) -> SlotProcessingContext:
        """Phase 2: Transform content with LLM (can run in parallel). Delegates to transform module."""
        return await transform_module.transform_slot_with_llm(
            self, context, week_of, provider, plan_id
        )

    async def _process_slots_parallel_llm(
        self,
        contexts: List[SlotProcessingContext],
        week_of: str,
        provider: str,
        plan_id: Optional[str] = None,
    ) -> List[SlotProcessingContext]:
        """Process all slots' LLM calls in parallel with concurrency limit.

        Args:
            contexts: List of SlotProcessingContext with extracted_content
            week_of: Week date range
            provider: LLM provider name
            plan_id: Plan ID for progress tracking

        Returns:
            List of updated SlotProcessingContext with lesson_json
        """
        # Get concurrency limit from settings
        limit = settings.MAX_CONCURRENT_LLM_REQUESTS
        semaphore = asyncio.Semaphore(limit)

        async def limited_transform(
            ctx: SlotProcessingContext,
        ) -> SlotProcessingContext:
            """Execute transformation within semaphore to limit concurrency."""
            async with semaphore:
                return await self._transform_slot_with_llm(
                    ctx, week_of, provider, plan_id
                )

        # Create tasks for limited parallel execution
        tasks = [limited_transform(ctx) for ctx in contexts]

        # Execute in parallel with error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
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

    async def _process_slot(
        self,
        slot: Dict[str, Any],
        week_of: str,
        provider: str,
        week_folder_path: Optional[str] = None,
        user_base_path: Optional[str] = None,
        plan_id: Optional[str] = None,
        slot_index: int = 1,
        total_slots: int = 1,
        processing_weight: float = 0.8,
        existing_lesson_json: Optional[Dict[str, Any]] = None,
        force_ai: bool = False,
    ) -> Dict[str, Any]:
        """Process a single class slot. Delegates to slot_flow.process_one_slot."""
        return await slot_flow_module.process_one_slot(
            self,
            slot,
            week_of,
            provider,
            week_folder_path=week_folder_path,
            user_base_path=user_base_path,
            plan_id=plan_id,
            slot_index=slot_index,
            total_slots=total_slots,
            processing_weight=processing_weight,
            existing_lesson_json=existing_lesson_json,
            force_ai=force_ai,
        )

    def _resolve_primary_file(
        self,
        slot: Dict[str, Any],
        week_of: str,
        week_folder_path: Optional[str] = None,
        user_base_path: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve primary teacher file using hybrid approach (see extraction.resolve_primary_file)."""
        return extraction_resolve_primary_file(
            slot, week_of, week_folder_path, user_base_path
        )

    def _combine_lessons(
        self,
        user: Dict[str, Any],
        lessons: List[Dict[str, Any]],
        week_of: str,
        generated_at: datetime,
        plan_id: Optional[str] = None,
    ) -> str:
        """
        Combine multiple lessons into a single DOCX using JSON merging.
        Delegates to combine module.
        """
        return combine_module.combine_lessons(
            self,
            user,
            lessons,
            week_of,
            generated_at,
            plan_id,
            get_file_manager_fn=get_file_manager,
        )

    def _merge_docx_files(
        self,
        file_paths: List[str],
        output_path: str,
        master_template_path: Optional[str] = None,
    ) -> None:
        """
        Merge multiple DOCX files into one using docxcompose.
        Delegates to combine module.
        """
        combine_module.merge_docx_files(
            file_paths, output_path, master_template_path
        )

    def _get_week_num(self, week_of: str) -> int:
        """Extract week number from week_of string (MM/DD-MM/DD or MM-DD-MM-DD)."""
        return get_week_num(week_of)

    def _remove_signature_boxes(self, doc: Document) -> None:
        """Remove signature boxes/tables from document. Delegates to signatures module."""
        signatures_module.remove_signature_boxes(doc)

    def _modify_existing_signature_table(
        self,
        doc: Document,
        date: datetime,
        signature_image_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> None:
        """Modify existing signature table in document. Delegates to signatures module."""
        signatures_module.modify_existing_signature_table(
            doc, date, signature_image_path, user_name
        )

    def _add_signature_image_to_table(self, table, signature_image_path: str) -> None:
        """Add signature image to the signature table. Delegates to signatures module."""
        signatures_module.add_signature_image_to_table(table, signature_image_path)

    def _add_user_name_to_table(self, table, user_name: str) -> None:
        """Add user name to the signature table. Delegates to signatures module."""
        signatures_module.add_user_name_to_table(table, user_name)

    def _add_signature_box(
        self,
        doc: Document,
        date: datetime,
        template_path: str,
        signature_image_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> None:
        """Add signature box from template to the end of document. Delegates to signatures module."""
        signatures_module.add_signature_box(
            doc, date, template_path, signature_image_path, user_name
        )

    def _calculate_week_number(self, week_of: str) -> int:
        """Calculate week number from date range (MM/DD-MM/DD). Returns 1-52."""
        return calculate_week_number(week_of)

    async def _extract_slots_parallel_db(
        self,
        slots: List[Dict[str, Any]],
        week_of: str,
        week_folder_path: Optional[str],
        user_base_path: Optional[str],
        plan_id: Optional[str],
        progress_tracker: Any,
    ) -> List[SlotProcessingContext]:
        """Parallel extraction using DB cache and file grouping. Delegates to extraction module."""
        return await extraction_module.extract_slots_parallel_db(
            self, slots, week_of, week_folder_path, user_base_path, plan_id, progress_tracker
        )

    async def _process_file_group(
        self,
        file_path: Optional[str],
        group: List[Tuple[int, Dict[str, Any]]],
        week_of: str,
        week_folder_path: Optional[str],
        user_base_path: Optional[str],
        plan_id: Optional[str],
        semaphore: asyncio.Semaphore,
    ) -> List[SlotProcessingContext]:
        """Process a group of slots that share the same source file. Delegates to combined_original module."""
        return await combined_original_module.process_file_group(
            self,
            file_path,
            group,
            week_of,
            week_folder_path,
            user_base_path,
            plan_id,
            semaphore,
        )

    def _convert_originals_to_json(
        self, plans: List[OriginalLessonPlan]
    ) -> Dict[str, Any]:
        """
        Convert a list of OriginalLessonPlan objects to a multi-slot lesson JSON.
        Delegates to combine module.
        """
        return combine_module.convert_originals_to_json(plans)

    def _reconstruct_slots_from_json(
        self, lesson_json: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Reconstruct individual slot lesson plans from a multi-slot lesson JSON.
        Delegates to combine module.
        """
        return combine_module.reconstruct_slots_from_json(lesson_json)

    async def _generate_combined_original_docx(
        self,
        user_id: str,
        week_of: str,
        plan_id: str,
        week_folder_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generates a combined DOCX of all original plans for the week. Delegates to combined_original module.
        """
        return await combined_original_module.generate_combined_original_docx(
            self,
            user_id,
            week_of,
            plan_id,
            week_folder_path,
            get_file_manager_fn=get_file_manager,
        )


async def process_batch(
    user_id: str, week_of: str, provider: str = "openai"
) -> Dict[str, Any]:
    """Convenience function to process a batch.

    Args:
        user_id: User ID
        week_of: Week date range
        provider: LLM provider

    Returns:
        Processing results
    """
    from backend.llm_service import get_llm_service

    llm_service = get_llm_service()
    processor = BatchProcessor(llm_service)

    return await processor.process_user_week(user_id, week_of, provider)
