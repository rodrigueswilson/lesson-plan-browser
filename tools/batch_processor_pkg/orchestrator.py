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
        """Process all class slots for a user's week.

        Args:
            user_id: User ID
            week_of: Week date range (MM/DD-MM/DD)
            provider: LLM provider to use
            week_folder_path: Optional path to week folder (overrides auto-detection)
            slot_ids: Optional list of specific slot IDs to process
            plan_id: Optional plan ID for progress tracking (if already created)
            partial: Whether to merge with an existing plan for the week
            missing_only: Whether to automatically identify and process only missing slots

        Returns:
            Dict with processing results
        """
        originals_docx = None
        try:
            logger.info(
                "process_user_week_START",
                extra={"user_id": user_id, "week_of": week_of},
            )
            print(
                f"\n{'=' * 60}\nPROCESS_USER_WEEK STARTED\nUser: {user_id}\nWeek: {week_of}\n{'=' * 60}\n"
            )
            start_time = datetime.now()
        except Exception as e:
            print(f"\n{'=' * 60}\nERROR IN PROCESS_USER_WEEK INIT: {e}\n{'=' * 60}\n")
            raise

        # Get user-specific database instance to ensure we're using the correct project
        db = get_db(user_id=user_id)
        print(f"DEBUG: Using database instance for user_id: {user_id}")

        # Get user and slots (wrapped in asyncio.to_thread to avoid blocking event loop)
        print("DEBUG: About to call db.get_user()")
        user_raw = await asyncio.to_thread(db.get_user, user_id)
        if not user_raw:
            return {"success": False, "error": f"User not found: {user_id}"}

        # Convert User object to dictionary
        if hasattr(user_raw, "model_dump"):
            user = user_raw.model_dump()
        elif hasattr(user_raw, "dict"):
            user = user_raw.dict()
        else:
            user = dict(user_raw)
        print(f"DEBUG: Got user: {user.get('name')}")

        print("DEBUG: About to call db.get_user_slots()")
        slots_raw = await asyncio.to_thread(db.get_user_slots, user_id)
        print(f"DEBUG: Got {len(slots_raw)} slots")
        if not slots_raw:
            return {
                "success": False,
                "error": f"No class slots configured for user: {user['name']}",
            }

        # Convert ClassSlot objects to dictionaries so we can enrich them
        slots = []
        for slot_obj in slots_raw:
            slot_dict = None

            # Try model_dump first (Pydantic v2 / SQLModel)
            if hasattr(slot_obj, "model_dump"):
                try:
                    slot_dict = slot_obj.model_dump(mode="python")
                except Exception:
                    try:
                        slot_dict = slot_obj.model_dump()
                    except Exception:
                        slot_dict = None

            # Try dict() method (Pydantic v1)
            if slot_dict is None and hasattr(slot_obj, "dict"):
                try:
                    slot_dict = slot_obj.dict()
                except Exception:
                    slot_dict = None

            # Already a dict - ensure all values are properly extracted
            if slot_dict is None and isinstance(slot_obj, dict):
                slot_dict = {}
                for key, value in slot_obj.items():
                    # Skip ModelPrivateAttr and similar objects
                    if hasattr(value, "__class__") and "ModelPrivateAttr" in str(
                        type(value)
                    ):
                        try:
                            # Try to get the actual value
                            slot_dict[key] = getattr(slot_obj, key, None)
                        except Exception:
                            slot_dict[key] = None
                    else:
                        slot_dict[key] = value

            # Fallback: Extract as dictionary from object attributes
            if slot_dict is None:
                slot_dict = {
                    "id": str(getattr(slot_obj, "id", ""))
                    if hasattr(slot_obj, "id")
                    else "",
                    "user_id": str(getattr(slot_obj, "user_id", ""))
                    if hasattr(slot_obj, "user_id")
                    else "",
                    "slot_number": int(getattr(slot_obj, "slot_number", 0))
                    if hasattr(slot_obj, "slot_number")
                    else 0,
                    "subject": str(getattr(slot_obj, "subject", ""))
                    if hasattr(slot_obj, "subject")
                    else "",
                    "grade": str(getattr(slot_obj, "grade", ""))
                    if hasattr(slot_obj, "grade")
                    else "",
                    "homeroom": str(getattr(slot_obj, "homeroom", ""))
                    if hasattr(slot_obj, "homeroom")
                    else None,
                    "plan_group_label": str(getattr(slot_obj, "plan_group_label", ""))
                    if hasattr(slot_obj, "plan_group_label")
                    else None,
                    "proficiency_levels": str(
                        getattr(slot_obj, "proficiency_levels", "")
                    )
                    if hasattr(slot_obj, "proficiency_levels")
                    else None,
                    "primary_teacher_file": str(
                        getattr(slot_obj, "primary_teacher_file", "")
                    )
                    if hasattr(slot_obj, "primary_teacher_file")
                    else None,
                    "primary_teacher_name": str(
                        getattr(slot_obj, "primary_teacher_name", "")
                    )
                    if hasattr(slot_obj, "primary_teacher_name")
                    else None,
                    "primary_teacher_first_name": str(
                        getattr(slot_obj, "primary_teacher_first_name", "")
                    )
                    if hasattr(slot_obj, "primary_teacher_first_name")
                    else None,
                    "primary_teacher_last_name": str(
                        getattr(slot_obj, "primary_teacher_last_name", "")
                    )
                    if hasattr(slot_obj, "primary_teacher_last_name")
                    else None,
                    "primary_teacher_file_pattern": str(
                        getattr(slot_obj, "primary_teacher_file_pattern", "")
                    )
                    if hasattr(slot_obj, "primary_teacher_file_pattern")
                    else None,
                    "display_order": int(getattr(slot_obj, "display_order", 0))
                    if hasattr(slot_obj, "display_order")
                    else 0,
                }

            # Ensure all values are safe (no ModelPrivateAttr objects)
            for key in list(slot_dict.keys()):
                value = slot_dict[key]
                if hasattr(value, "__class__") and "ModelPrivateAttr" in str(
                    type(value)
                ):
                    slot_dict[key] = None
                elif not isinstance(
                    value, (str, int, float, bool, type(None), list, dict)
                ):
                    # Convert other non-serializable types to None
                    try:
                        slot_dict[key] = str(value)
                    except Exception:
                        slot_dict[key] = None

            slots.append(slot_dict)

        # Enrich slots with schedule entry data (start_time, end_time)
        print("DEBUG: Enriching slots with schedule data")
        schedule_entries = await asyncio.to_thread(db.get_user_schedule, user_id)
        # Convert schedule entries to dictionaries to avoid ModelPrivateAttr issues
        schedule_entries_dict = []
        for entry in schedule_entries:
            if hasattr(entry, "model_dump"):
                entry_dict = entry.model_dump()
            elif hasattr(entry, "dict"):
                entry_dict = entry.dict()
            else:
                entry_dict = {
                    "slot_number": getattr(entry, "slot_number", None),
                    "is_active": getattr(entry, "is_active", True),
                    "start_time": getattr(entry, "start_time", None),
                    "end_time": getattr(entry, "end_time", None),
                }
            schedule_entries_dict.append(entry_dict)

        def normalize_subj(s):
            if not s:
                return ""
            # Lowercase and keep only alphanumeric characters for comparison
            return re.sub(r"[^a-z0-9]", "", s.lower())

        for slot in slots:
            slot_subj_norm = normalize_subj(slot.get("subject", ""))
            slot_num = slot.get("slot_number")

            # Find matching schedule entry using a multi-stage strategy
            # Stage 1: Match by both subject and slot number (tightest)
            matching_entries = [
                e
                for e in schedule_entries_dict
                if normalize_subj(e.get("subject", "")) == slot_subj_norm
                and e.get("slot_number") == slot_num
                and e.get("is_active", True)
            ]

            # Stage 2: Match by subject only (useful if slot numbers shifted)
            if not matching_entries:
                matching_entries = [
                    e
                    for e in schedule_entries_dict
                    if normalize_subj(e.get("subject", "")) == slot_subj_norm
                    and e.get("is_active", True)
                ]

            # Stage 3: Match by slot number only (legacy fallback)
            if not matching_entries:
                matching_entries = [
                    e
                    for e in schedule_entries_dict
                    if e.get("slot_number") == slot_num
                    and e.get("is_active", True)
                ]

            if matching_entries:
                # Store all day-specific times for accurate chronological ordering in PDFs
                day_times = {}
                for e in matching_entries:
                    day = e.get("day_of_week", "").lower()
                    if day:
                        day_times[day] = {
                            "start_time": e.get("start_time"),
                            "end_time": e.get("end_time"),
                        }
                slot["day_times"] = day_times

                # Keep the "most common" time as the default/fallback
                from collections import Counter

                times = [
                    (e.get("start_time"), e.get("end_time")) for e in matching_entries
                ]
                most_common_time = Counter(times).most_common(1)[0][0]
                slot["start_time"] = most_common_time[0]
                slot["end_time"] = most_common_time[1]
                print(
                    f"DEBUG: Enriched slot {slot.get('slot_number')} ({slot.get('subject')}) with day_times for {list(day_times.keys())}"
                )
            else:
                print(
                    f"DEBUG: No schedule entry found for slot {slot.get('slot_number')} ({slot.get('subject')})"
                )

        # Filter slots if specific slot_ids provided
        # Convert slot_ids to a set of strings for efficient lookup
        if slot_ids:
            print(f"DEBUG: Filtering slots with provided slot_ids: {slot_ids}")
            print(f"DEBUG: Total slots before filtering: {len(slots)}")
            print(f"DEBUG: Slot IDs in database: {[slot.get('id') for slot in slots]}")

            slot_ids_set = set()
            for sid in slot_ids:
                if isinstance(sid, str):
                    slot_ids_set.add(sid)
                elif hasattr(sid, "id"):
                    slot_ids_set.add(str(sid.id))
                else:
                    slot_ids_set.add(str(sid))

            print(f"DEBUG: slot_ids_set after conversion: {slot_ids_set}")

            slots = [slot for slot in slots if slot.get("id") in slot_ids_set]
            print(f"DEBUG: Total slots after filtering: {len(slots)}")
            print(f"DEBUG: Filtered slot IDs: {[slot.get('id') for slot in slots]}")

            if not slots:
                error_msg = f"No matching slots found for provided slot_ids. Requested: {slot_ids_set}, Available: {[slot.get('id') for slot in slots_raw if hasattr(slot, 'id') or isinstance(slot, dict)]}"
                print(f"ERROR: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                }

        # Always check for existing plan for this week (Optimization cache)
        existing_lesson_json = None
        print("DEBUG: Checking for existing plan for week process optimization")
        # Try to get existing plan for this week
        existing_plans = await asyncio.to_thread(db.get_user_plans, user_id, limit=5)
        # Find the first one with the same week_of
        existing_plan = next(
            (p for p in existing_plans if p.week_of == week_of), None
        )

        if existing_plan:
            print(f"DEBUG: Found existing plan {existing_plan.id} for week {week_of}")
            # Use current plan_id if not provided
            if not plan_id:
                plan_id = existing_plan.id

            # Load existing lesson_json
            existing_lesson_json = existing_plan.lesson_json
            if isinstance(existing_lesson_json, str):
                import json

                try:
                    existing_lesson_json = json.loads(existing_lesson_json)
                except Exception:
                    existing_lesson_json = None

            if existing_lesson_json:
                # Enrich from steps if needed (api.py logic)
                from backend.utils.lesson_json_enricher import (
                    enrich_lesson_json_from_steps,
                )

                existing_lesson_json = enrich_lesson_json_from_steps(
                    existing_lesson_json, existing_plan.id, db
                )
                print(
                    f"DEBUG: Loaded and enriched existing lesson_json for plan {existing_plan.id}"
                )
                logger.info(
                    "skip_logic_plan_found",
                    extra={
                        "plan_id": existing_plan.id,
                        "status": "valid_json_loaded",
                        "week_of": week_of
                    }
                )

                if missing_only:
                    print("DEBUG: Identifying missing slots...")
                    # Extract existing slot IDs or slot numbers from existing_lesson_json
                    existing_slots_data = []
                    for day in existing_lesson_json.get("days", {}).values():
                        existing_slots_data.extend(day.get("slots", []))

                    existing_slot_numbers = {
                        s.get("slot_number")
                        for s in existing_slots_data
                        if s.get("slot_number") is not None
                    }
                    print(f"DEBUG: Existing slot numbers: {existing_slot_numbers}")

                    # Filter current slots to only those NOT in existing_slots_data
                    # We use slot_number as the primary identifier for "missing"
                    original_count = len(slots)
                    slots = [
                        s
                        for s in slots
                        if s.get("slot_number") not in existing_slot_numbers
                    ]
                    print(
                        f"DEBUG: Filtered from {original_count} to {len(slots)} missing slots"
                    )
            else:
                logger.info(
                    "skip_logic_plan_invalid",
                    extra={
                        "plan_id": existing_plan.id,
                        "status": "json_empty_or_invalid",
                        "week_of": week_of
                    }
                )
        else:
            print(
                f"DEBUG: No existing plan found for week {week_of}, proceeding with generation"
            )
            logger.info(
                "skip_logic_no_plan",
                extra={
                    "status": "plan_not_found_in_db",
                    "week_of": week_of
                }
            )
            # If no existing plan, we can't do "partial" merge at the end
            partial = False
            missing_only = False

        # Store user's metadata for file resolution and rendering
        self._current_user_id = user_id
        # Prefer base_path_override, but fall back to base_path if available in the user object
        self._user_base_path = user.get("base_path_override") or user.get("base_path")
        self._user_first_name = user.get("first_name", "")
        self._user_last_name = user.get("last_name", "")
        self._user_name = user.get("name", "")
        logger.info(
            "batch_user_base_path",
            extra={
                "user_id": user_id,
                "user_name": user["name"],
                "base_path": self._user_base_path or "default",
            },
        )

        # Determine if this is a consolidated plan
        is_consolidated = len(slots) > 1

        # Create or use existing weekly plan record
        if not plan_id:
            plan_id = await asyncio.to_thread(
                db.create_weekly_plan,
                user_id,
                week_of,
                output_file="",  # Will be updated after generation
                week_folder_path=week_folder_path,
                consolidated=is_consolidated,
                total_slots=len(slots),
            )
            await asyncio.to_thread(db.update_weekly_plan, plan_id, status="processing")

        # Store plan_id for tracking
        self._current_plan_id = plan_id

        # Start tracking total batch duration
        batch_op_id = ""
        try:
            batch_op_id = self.tracker.start_operation(
                plan_id,
                "batch_process",
                metadata={"total_slots": len(slots), "consolidated": is_consolidated},
            )
        except Exception as e:
            print(f"WARNING: Failed to start batch tracking: {e}")

        processing_weight = settings.PROGRESS_PROCESSING_WEIGHT
        rendering_weight = settings.PROGRESS_RENDERING_WEIGHT

        # Ensure weights sum to 1 for progress tracking
        if abs((processing_weight + rendering_weight) - 1.0) > 1e-6:
            total = processing_weight + rendering_weight
            processing_weight = processing_weight / total
            rendering_weight = rendering_weight / total

        # Process each slot
        lessons = []
        errors = []

        print(f"DEBUG: About to start processing {len(slots)} slots")
        # Update progress: starting
        progress_tracker.update(
            plan_id, "processing", 0, f"Starting to process {len(slots)} slots..."
        )
        print("DEBUG: Progress tracker updated - starting")

        # Check if parallel processing is enabled
        use_parallel = settings.PARALLEL_LLM_PROCESSING and len(slots) > 1

        if use_parallel:
            # Two-phase processing: Extract sequentially, transform in parallel
            print(f"DEBUG: Using parallel processing for {len(slots)} slots")

            # Phase 1: Parallel Extraction with DB Caching and Grouping
            contexts = await self._extract_slots_parallel_db(
                slots,
                week_of,
                week_folder_path,
                self._user_base_path,
                plan_id,
                progress_tracker,
            )

            # AUTO-GENERATE ORIGINALS AUDIT DOCX (Parallel Path)
            try:
                logger.info("batch_auto_generating_originals_docx_parallel")
                originals_docx = await self._generate_combined_original_docx(
                    user_id, week_of, plan_id, week_folder_path
                )
            except Exception as e:
                logger.error(
                    "batch_auto_originals_generation_failed_parallel",
                    extra={"error": str(e)},
                )

            # Re-collect errors from contexts
            for ctx in contexts:
                if ctx.error:
                    errors.append(
                        f"Failed slot {ctx.slot_index}/{ctx.total_slots}: {ctx.error}"
                    )

            # NEW: Optimize Phase 2 - Avoid LLM calls for unchanged slots if we already have transformed versions
            if existing_lesson_json:
                print(
                    "DEBUG: Checking for slots to skip LLM transformation (already in DB and unchanged source)..."
                )
                existing_slot_plans = self._reconstruct_slots_from_json(
                    existing_lesson_json
                )

                for ctx in contexts:
                    if ctx.cache_hit and not ctx.error:
                        slot_num = ctx.slot.get("slot_number")
                        if slot_num in existing_slot_plans and slot_num not in (
                            force_slots or []
                        ):
                            print(
                                f"[DEBUG] REUSING TRANSFORMED PLAN for slot {slot_num} ({ctx.slot['subject']}) - Source file unchanged."
                            )
                            # CRITICAL: Create a deep copy to prevent shared state in parallel processing
                            # If multiple slots share the same lesson_json reference, mutations in one
                            # parallel task could affect others, causing all slots to show the same teacher
                            import copy
                            ctx.lesson_json = copy.deepcopy(existing_slot_plans[slot_num][
                                "lesson_json"
                            ])
                        elif slot_num in existing_slot_plans and slot_num in (
                            force_slots or []
                        ):
                            print(
                                f"[DEBUG] FORCING AI transformation for slot {slot_num} ({ctx.slot['subject']}) as requested."
                            )

            # Phase 2: Transform with LLM in parallel
            print(
                f"DEBUG: Starting Phase 2: Parallel LLM transformation for {len(contexts)} slots"
            )
            transform_count = len(
                [c for c in contexts if not c.error and not c.lesson_json]
            )
            progress_tracker.update(
                plan_id,
                "processing",
                20,
                f"Transforming {transform_count} slots with AI in parallel...",
            )

            contexts = await self._process_slots_parallel_llm(
                contexts,
                week_of,
                provider,
                plan_id,
            )

            # Collect results
            for context in contexts:
                if context.error:
                    errors.append(
                        f"Failed slot {context.slot_index}/{context.total_slots}: {context.error}"
                    )
                elif context.lesson_json:
                    # LOGGING: Verify hyperlinks are present before collecting
                    hyperlinks_in_json = context.lesson_json.get("_hyperlinks", [])
                    print(
                        f"[DEBUG] Collecting parallel result: Slot {context.slot.get('slot_number')}, "
                        f"Subject {context.slot.get('subject')}, "
                        f"Hyperlinks in lesson_json: {len(hyperlinks_in_json)}"
                    )
                    logger.info(
                        "parallel_result_collection",
                        extra={
                            "slot": context.slot.get("slot_number"),
                            "subject": context.slot.get("subject"),
                            "has_lesson_json": context.lesson_json is not None,
                            "hyperlinks_count": len(hyperlinks_in_json),
                            "has_hyperlinks_key": "_hyperlinks" in context.lesson_json,
                        },
                    )
                    # Include original slot data for primary teacher fields
                    # context.slot is already a dict with primary teacher fields from database
                    slot_data = context.slot.copy() if isinstance(context.slot, dict) else {
                        "slot_number": getattr(context.slot, "slot_number", context.slot_index),
                        "subject": getattr(context.slot, "subject", "Unknown"),
                        "primary_teacher_name": getattr(context.slot, "primary_teacher_name", None),
                        "primary_teacher_first_name": getattr(context.slot, "primary_teacher_first_name", None),
                        "primary_teacher_last_name": getattr(context.slot, "primary_teacher_last_name", None),
                    }
                    # Debug: Verify primary teacher fields are present
                    if isinstance(slot_data, dict):
                        print(f"[DEBUG] BATCH_PROCESSOR: Slot {slot_data.get('slot_number')} slot_data has primary_teacher_name: {slot_data.get('primary_teacher_name')}")
                    lessons.append(
                        {
                            "slot_number": slot_data.get("slot_number") if isinstance(slot_data, dict) else getattr(context.slot, "slot_number", context.slot_index),
                            "subject": slot_data.get("subject") if isinstance(slot_data, dict) else getattr(context.slot, "subject", "Unknown"),
                            "lesson_json": context.lesson_json,
                            "slot_data": slot_data,  # Include original slot data for teacher fields
                        }
                    )
                    # Track parallel processing metrics
                    if plan_id and context.is_parallel:
                        # Store metrics in performance tracker result
                        # This will be picked up by end_operation
                        pass  # Metrics are already in context

        else:
            # Sequential processing (fallback or single slot)
            print(
                "DEBUG: Using sequential processing (parallel disabled or single slot)"
            )

            for i, slot in enumerate(slots, 1):
                # Ensure slot is a dictionary with safe access
                slot_num = (
                    slot.get("slot_number")
                    if isinstance(slot, dict)
                    else getattr(slot, "slot_number", i)
                )
                slot_subject = (
                    slot.get("subject")
                    if isinstance(slot, dict)
                    else getattr(slot, "subject", "Unknown")
                )

                print(
                    f"\nDEBUG: === Starting slot {i}/{len(slots)} (slot_number={slot_num}): {slot_subject} ==="
                )
                try:
                    # CRITICAL: Sanitize slot immediately before ANY access
                    # This handles Pydantic/SQLModel PrivateAttr issues at the source
                    try:
                        slot = self._sanitize_slot(slot)
                    except Exception as sanitize_err:
                        print(f"ERROR: _sanitize_slot failed: {sanitize_err}")
                        # Fallback to dict conversion
                        if hasattr(slot, "model_dump"):
                            slot = slot.model_dump()
                        elif hasattr(slot, "dict"):
                            slot = slot.dict()
                        else:
                            slot = dict(slot)

                    # Ensure slot is fully a dictionary for safe access
                    if not isinstance(slot, dict):
                        if hasattr(slot, "model_dump"):
                            slot = slot.model_dump()
                        elif hasattr(slot, "dict"):
                            slot = slot.dict()
                        else:
                            # Convert to dict manually
                            slot = {
                                "id": getattr(slot, "id", None),
                                "slot_number": getattr(slot, "slot_number", i),
                                "subject": getattr(slot, "subject", "Unknown"),
                                "grade": getattr(slot, "grade", None),
                                "homeroom": getattr(slot, "homeroom", None),
                                "primary_teacher_name": getattr(
                                    slot, "primary_teacher_name", None
                                ),
                                "primary_teacher_first_name": getattr(
                                    slot, "primary_teacher_first_name", None
                                ),
                                "primary_teacher_last_name": getattr(
                                    slot, "primary_teacher_last_name", None
                                ),
                                "primary_teacher_file": getattr(
                                    slot, "primary_teacher_file", None
                                ),
                                "primary_teacher_file_pattern": getattr(
                                    slot, "primary_teacher_file_pattern", None
                                ),
                            }

                    # RE-SANITIZE just in case conversion re-introduced issues
                    slot = self._sanitize_slot(slot)

                    # Update slot in list to use dictionary version
                    slots[i - 1] = slot

                    # Update progress: processing slot
                    progress_pct = int((i - 1) / len(slots) * processing_weight * 100)
                    print(
                        f"DEBUG: Updating progress tracker for slot {i} (slot_number={slot.get('slot_number')})"
                    )
                    progress_tracker.update(
                        plan_id,
                        "processing",
                        progress_pct,
                        f"Processing slot {i}/{len(slots)}: {slot.get('subject', 'Unknown')} ({slot.get('primary_teacher_name', 'No teacher')})",
                    )
                    print(f"DEBUG: Progress tracker updated for slot {i}")

                    logger.info(
                        "batch_slot_processing",
                        extra={
                            "plan_id": plan_id,
                            "slot_index": i,
                            "total_slots": len(slots),
                            "subject": slot.get("subject", "Unknown"),
                            "teacher": slot.get("primary_teacher_name"),
                        },
                    )
                    print(
                        f"DEBUG: About to call _process_slot for slot {i} (slot_number={slot.get('slot_number')}, subject={slot.get('subject')})"
                    )
                    lesson_json = await self._process_slot(
                        slot,
                        week_of,
                        provider,
                        week_folder_path,
                        self._user_base_path,
                        plan_id,
                        i,
                        len(slots),
                        processing_weight,
                        existing_lesson_json=existing_lesson_json,
                        force_ai=slot.get("slot_number") in (force_slots or []),
                    )
                    print(f"[DEBUG] _process_slot (SEQUENTIAL) completed for slot {i}")
                    # LOGGING: Verify hyperlinks are present before collecting
                    hyperlinks_in_json = lesson_json.get("_hyperlinks", [])
                    print(
                        f"[DEBUG] Collecting sequential result: Slot {slot.get('slot_number')}, "
                        f"Subject {slot.get('subject')}, "
                        f"Hyperlinks in lesson_json: {len(hyperlinks_in_json)}"
                    )
                    logger.info(
                        "sequential_result_collection",
                        extra={
                            "slot": slot.get("slot_number"),
                            "subject": slot.get("subject"),
                            "hyperlinks_count": len(hyperlinks_in_json),
                            "has_hyperlinks_key": "_hyperlinks" in lesson_json,
                        },
                    )
                    # Include original slot data for primary teacher fields
                    # slot is already a dict with primary teacher fields from database
                    slot_data = slot.copy() if isinstance(slot, dict) else {
                        "slot_number": getattr(slot, "slot_number", i),
                        "subject": getattr(slot, "subject", "Unknown"),
                        "primary_teacher_name": getattr(slot, "primary_teacher_name", None),
                        "primary_teacher_first_name": getattr(slot, "primary_teacher_first_name", None),
                        "primary_teacher_last_name": getattr(slot, "primary_teacher_last_name", None),
                    }
                    # Debug: Verify primary teacher fields are present
                    if isinstance(slot_data, dict):
                        print(f"[DEBUG] BATCH_PROCESSOR: Slot {slot_data.get('slot_number')} slot_data has primary_teacher_name: {slot_data.get('primary_teacher_name')}")
                    lessons.append(
                        {
                            "slot_number": slot_data.get("slot_number") if isinstance(slot_data, dict) else getattr(slot, "slot_number", i),
                            "subject": slot_data.get("subject") if isinstance(slot_data, dict) else getattr(slot, "subject", "Unknown"),
                            "lesson_json": lesson_json,
                            "slot_data": slot_data,  # Include original slot data for teacher fields
                        }
                    )
                    print(f"[DEBUG] Lesson appended for slot {i}")
                    logger.info(
                        "batch_slot_completed",
                        extra={
                            "plan_id": plan_id,
                            "slot_index": i,
                            "total_slots": len(slots),
                            "subject": slot.get("subject", "Unknown"),
                        },
                    )
                    print(f"DEBUG: === Completed slot {i}/{len(slots)} ===")

                    # Update progress: slot completed
                    progress_pct = int(i / len(slots) * processing_weight * 100)
                    progress_tracker.update(
                        plan_id,
                        "processing",
                        progress_pct,
                        f"Completed slot {i}/{len(slots)}: {slot.get('subject', 'Unknown')}",
                    )
                except Exception as e:
                    print(
                        f"ERROR: Exception in process_weekly_plan loop for slot {i}: {e}"
                    )
                    traceback.print_exc()
                    # Use safe access for error message
                    slot_num = (
                        slot.get("slot_number")
                        if isinstance(slot, dict)
                        else getattr(slot, "slot_number", i)
                    )
                    slot_subject = (
                        slot.get("subject")
                        if isinstance(slot, dict)
                        else getattr(slot, "subject", "Unknown")
                    )
                    # Safely format error message, handling encoding errors
                    try:
                        error_str = str(e)
                    except UnicodeEncodeError:
                        error_str = repr(e).encode("ascii", "replace").decode("ascii")
                    error_msg = f"Slot {slot_num} ({slot_subject}): {error_str}"
                    errors.append(error_msg)
                    logger.error(
                        "batch_slot_error",
                        extra={
                            "plan_id": plan_id,
                            "slot_index": i,
                            "total_slots": len(slots),
                            "subject": slot.get("subject", "Unknown"),
                            "error": error_msg,
                        },
                    )

                    # Update progress: slot failed
                    progress_tracker.update(
                        plan_id,
                        "error",
                        int(i / len(slots) * processing_weight * 100),
                        f"Failed slot {i}/{len(slots)}: {error_msg}",
                    )

        # Sequential extraction/transformation loop ends here

        # AUTO-GENERATE ORIGINALS AUDIT DOCX (Sequential/Fallback Path)
        # ONLY if not already generated in parallel path
        if not originals_docx:
            try:
                logger.info("batch_auto_generating_originals_docx_sequential")
                originals_docx = await self._generate_combined_original_docx(
                    user_id, week_of, plan_id, week_folder_path
                )
            except Exception as e:
                logger.error(
                    "batch_auto_originals_generation_failed_sequential",
                    extra={"error": str(e)},
                )

        # Handle merging with existing lessons if partial is requested
        all_lessons_for_rendering = lessons.copy()
        if (partial or missing_only) and existing_lesson_json:
            print("DEBUG: Reconstructing existing slots for merge...")
            existing_slots_by_number = self._reconstruct_slots_from_json(
                existing_lesson_json
            )

            # Combine: new lessons override existing ones
            combined_lessons_by_number = existing_slots_by_number
            for lesson in lessons:
                combined_lessons_by_number[lesson["slot_number"]] = lesson

            all_lessons_for_rendering = list(combined_lessons_by_number.values())
            # Sort by slot number for consistent rendering
            all_lessons_for_rendering.sort(key=lambda x: x.get("slot_number", 0))
            print(
                f"DEBUG: Combined to {len(all_lessons_for_rendering)} total slots for rendering"
            )

        # Generate combined DOCX if we have any successful lessons
        print(
            f"\nDEBUG: Finished processing all slots, {len(all_lessons_for_rendering)} total for rendering"
        )
        output_file = None
        if all_lessons_for_rendering:
            try:
                print(
                    f"DEBUG: About to render {len(all_lessons_for_rendering)} lessons"
                )
                # Update progress: rendering
                rendering_progress = int(
                    processing_weight * 100 + rendering_weight * 50
                )
                print("DEBUG: Updating progress tracker for rendering")
                progress_tracker.update(
                    plan_id,
                    "rendering",
                    rendering_progress,
                    f"Rendering {len(all_lessons_for_rendering)} lessons to DOCX...",
                )
                print("DEBUG: Progress tracker updated for rendering")

                print("DEBUG: Calling _combine_lessons (wrapped in asyncio.to_thread)")
                output_file = await asyncio.to_thread(
                    self._combine_lessons,
                    user,
                    all_lessons_for_rendering,
                    week_of,
                    start_time,
                    plan_id,
                )
                print(f"DEBUG: _combine_lessons returned: {output_file}")

                # Note: Objectives and Sentence Frames PDFs are already generated in _combine_lessons_impl
                # with correct enrichment and proper filenames. Removing duplicate generation that was
                # creating incorrect files with _Objectives_ and _SentenceFrames_ patterns.

                # Update progress: complete
                print(
                    f"DEBUG: Updating progress tracker to complete (plan_id={plan_id})"
                )
                progress_tracker.update(
                    plan_id,
                    "complete",
                    100,
                    f"Successfully created lesson plan with {len(all_lessons_for_rendering)} slots",
                )
                print("DEBUG: Progress tracker updated to complete")

                # Also mark as complete using the tracker's complete method
                progress_tracker.complete(plan_id)
                print("DEBUG: Progress tracker marked complete via complete() method")
            except Exception as e:
                error_msg = f"Failed to combine lessons: {str(e)}"
                print(f"ERROR: Exception in _combine_lessons: {error_msg}")
                traceback.print_exc()
                errors.append(error_msg)
                progress_tracker.update(
                    plan_id, "error", rendering_progress, f"Failed to render: {str(e)}"
                )

        # Update plan status
        total_time = (datetime.now() - start_time).total_seconds() * 1000

        if output_file:
            # Get merged lesson_json for database storage
            merged_lesson_json = None
            if all_lessons_for_rendering:
                if len(all_lessons_for_rendering) == 1:
                    # Single-slot: convert to slots format for consistency
                    single_lesson_json = all_lessons_for_rendering[0]["lesson_json"]
                    merged_lesson_json = self._convert_single_slot_to_slots_format(
                        single_lesson_json,
                        all_lessons_for_rendering[0]["slot_number"],
                        all_lessons_for_rendering[0]["subject"],
                    )
                else:
                    # Multi-slot: merge lesson JSONs (already creates slots format)
                    from tools.json_merger import merge_lesson_jsons

                    merged_lesson_json = merge_lesson_jsons(all_lessons_for_rendering)

            await asyncio.to_thread(
                db.update_weekly_plan,
                plan_id,
                status="completed",
                output_file=output_file,
                lesson_json=merged_lesson_json,
                total_slots=len(all_lessons_for_rendering),
            )
            # Update performance summary
            await asyncio.to_thread(self.tracker.update_plan_summary, plan_id)
        else:
            await asyncio.to_thread(
                db.update_weekly_plan,
                plan_id,
                status="failed",
                error_message="; ".join(errors),
            )

        # If we have no output file and no errors were collected, something went wrong silently
        if not output_file and not errors:
            error_msg = "Processing failed: No output file generated and no errors were collected. This may indicate an unhandled exception."
            errors = [error_msg]
            logger.error(
                "batch_process_silent_failure",
                extra={
                    "plan_id": plan_id,
                    "lessons_count": len(lessons),
                    "slots_count": len(slots),
                    "output_file": output_file,
                },
            )
            print(f"ERROR: {error_msg}")
            print(
                f"DEBUG: lessons={len(lessons)}, slots={len(slots)}, output_file={output_file}"
            )

        # End tracking total batch duration
        try:
            if batch_op_id:
                self.tracker.end_operation(
                    batch_op_id,
                    result={
                        "success": bool(output_file),
                        "processed_slots": len(lessons),
                        "failed_slots": len(errors),
                        "error": "; ".join(errors) if errors else None,
                    },
                )
        except Exception as e:
            print(f"WARNING: Failed to end batch tracking: {e}")

        return {
            "success": bool(output_file),
            "plan_id": plan_id,
            "output_file": output_file or "",
            "originals_docx": originals_docx,
            "processed_slots": len(lessons),
            "failed_slots": len(errors),
            "total_time_ms": total_time,
            "consolidated": is_consolidated,
            "total_slots": len(slots),
            "errors": errors if errors else None,
        }

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
        """Process a single class slot.

        Args:
            slot: Class slot data
            week_of: Week date range
            provider: LLM provider
            week_folder_path: Optional week folder override
            user_base_path: User's base path override
            plan_id: Plan ID for progress tracking
            slot_index: Current slot index (1-based)
            total_slots: Total number of slots being processed
            processing_weight: Weight for processing phase (0-1)

        Returns:
            Lesson plan JSON
        """
        # CRITICAL: Sanitize slot input to remove any ModelPrivateAttr objects
        # This prevents "argument of type 'ModelPrivateAttr' is not iterable" errors
        slot = self._sanitize_slot(slot)

        from backend.progress import progress_tracker

        # Helper function to update progress during slot processing
        def update_slot_progress(stage: str, slot_progress: int, message: str):
            """Update progress for current slot processing."""
            if plan_id:
                # Calculate overall progress: base progress for previous slots + current slot progress
                base_progress = int(
                    (slot_index - 1) / total_slots * processing_weight * 100
                )
                current_slot_progress = int(
                    slot_progress / 100 * (1 / total_slots) * processing_weight * 100
                )
                overall_progress = base_progress + current_slot_progress
                progress_tracker.update(plan_id, stage, overall_progress, message)

        print(
            f"DEBUG: _process_slot - Resolving primary file for slot {slot['slot_number']}"
        )
        update_slot_progress(
            "processing", 10, f"Finding lesson plan file for {slot['subject']}..."
        )

        # Track file resolution
        print("DEBUG: _process_slot - calling _resolve_primary_file")
        if plan_id:

            def _resolve_with_tracking():
                try:
                    with self.tracker.track_operation(
                        plan_id,
                        "parse_resolve_file",
                        metadata={
                            "slot_number": slot.get("slot_number"),
                            "subject": slot["subject"],
                            "week_of": week_of,
                        },
                    ):
                        return self._resolve_primary_file(
                            slot, week_of, week_folder_path, user_base_path
                        )
                except Exception as e:
                    print(f"DEBUG: Error in _resolve_with_tracking: {e}")
                    traceback.print_exc()
                    raise

            primary_file = await asyncio.to_thread(_resolve_with_tracking)
        else:
            primary_file = self._resolve_primary_file(
                slot, week_of, week_folder_path, user_base_path
            )
        print(f"DEBUG: _process_slot - Primary file resolved: {primary_file}")

        if not primary_file:
            # Provide helpful error message with guidance
            # Get week folder path for error message
            if week_folder_path:
                week_folder = Path(week_folder_path)
            else:
                file_mgr = get_file_manager(base_path=user_base_path)
                week_folder = file_mgr.get_week_folder(week_of)

            teacher_pattern = (
                slot.get("primary_teacher_file_pattern")
                or slot.get("primary_teacher_name")
                or (
                    f"{slot.get('primary_teacher_first_name', '')} {slot.get('primary_teacher_last_name', '')}".strip()
                    if slot.get("primary_teacher_first_name")
                    or slot.get("primary_teacher_last_name")
                    else None
                )
            )

            error_msg = (
                f"No primary teacher file found for slot {slot['slot_number']} (subject: '{slot['subject']}').\n"
                f"Week folder: {week_folder} (exists: {week_folder.exists()})\n"
            )

            if not teacher_pattern:
                error_msg += (
                    f"\nCONFIGURATION MISSING: Slot {slot['slot_number']} needs primary teacher information.\n"
                    f"Please configure one of the following:\n"
                    f"  - primary_teacher_file_pattern (e.g., 'Davies', 'Savoca')\n"
                    f"  - primary_teacher_name\n"
                    f"  - primary_teacher_first_name + primary_teacher_last_name\n"
                )
            else:
                error_msg += f"\nSearched for pattern: '{teacher_pattern}'\n"
                if week_folder.exists():
                    docx_files = list(week_folder.glob("*.docx"))
                    error_msg += f"Available files ({len(docx_files)} total):\n"
                    for f in docx_files[:10]:
                        error_msg += f"  - {f.name}\n"
                    if len(docx_files) > 10:
                        error_msg += f"  ... and {len(docx_files) - 10} more files\n"
                    error_msg += (
                        "\nTROUBLESHOOTING:\n"
                        "1. Check if the teacher's name appears in any filename\n"
                        "2. Verify the filename format matches the pattern\n"
                        "3. Ensure files are in the correct week folder\n"
                    )
                else:
                    error_msg += "\nWeek folder does not exist. Please create it or check the path.\n"

            raise ValueError(error_msg)

        # Parse the found file (sync I/O - run in thread)
        print("DEBUG: _process_slot - Creating DOCXParser")
        update_slot_progress("processing", 15, "Reading lesson plan document...")

        try:
            # Check file accessibility and retry if needed
            parser = await self._open_docx_with_retry(
                primary_file,
                plan_id=plan_id,
                slot_number=slot.get("slot_number"),
                subject=slot.get("subject"),
            )
            print("DEBUG: _process_slot - DOCXParser created successfully")

            # NEW: Check DB cache for already processed slot (Optimization)
            user_id = getattr(self, "_current_user_id", "unknown")
            db_record = await asyncio.to_thread(
                self.db.get_original_lesson_plan,
                user_id,
                week_of,
                slot["slot_number"],
            )

            # Cache validation: check if source file hasn't changed
            cache_hit = False
            if db_record and db_record.source_file_path == primary_file:
                path_obj = Path(primary_file)
                if path_obj.exists():
                    current_mtime = path_obj.stat().st_mtime
                    if db_record.extracted_at.timestamp() > (current_mtime + 2):
                        print(
                            f"[DEBUG] DB Cache hit for slot {slot['slot_number']} ({slot['subject']})"
                        )
                        cache_hit = True

            # If cache hit and we have existing transformed results, reuse them
            # UNLESS force_ai is requested
            if cache_hit and existing_lesson_json and not force_ai:
                existing_slot_plans = self._reconstruct_slots_from_json(
                    existing_lesson_json
                )
                slot_num = slot.get("slot_number")
                if slot_num in existing_slot_plans:
                    print(
                        f"[DEBUG] REUSING TRANSFORMED PLAN for slot {slot_num} ({slot['subject']}) - Source file unchanged."
                    )
                    update_slot_progress(
                        "processing",
                        100,
                        f"Reusing existing plan for {slot['subject']}",
                    )
                    # CRITICAL: Clean up parser before returning
                    del parser
                    import gc

                    gc.collect()

                    # Ensure metadata is up-to-date with current slot configuration even when using cache
                    # CRITICAL: Create a deep copy to prevent shared state in parallel processing
                    # If multiple slots share the same lesson_json reference, mutations in one
                    # parallel task could affect others, causing all slots to show the same teacher
                    import copy
                    cached_json = copy.deepcopy(existing_slot_plans[slot_num]["lesson_json"])
                    
                    if "metadata" not in cached_json:
                        cached_json["metadata"] = {}
                    
                    # CRITICAL: Update primary teacher fields from current slot data
                    # This ensures cached JSON gets the correct slot-specific teacher, not the old combined name
                    cached_json["metadata"]["primary_teacher_name"] = slot.get("primary_teacher_name")
                    cached_json["metadata"]["primary_teacher_first_name"] = slot.get("primary_teacher_first_name")
                    cached_json["metadata"]["primary_teacher_last_name"] = slot.get("primary_teacher_last_name")
                    
                    # CRITICAL: Also update teacher_name with combined format "Primary / Bilingual"
                    # This ensures the metadata table shows "Kelsey Lang / Wilson Rodrigues" format
                    try:
                        user_dict = {
                            "first_name": getattr(self, "_user_first_name", ""),
                            "last_name": getattr(self, "_user_last_name", ""),
                            "name": getattr(self, "_user_name", ""),
                        }
                        combined_teacher_name = self._build_teacher_name(user_dict, slot)
                        cached_json["metadata"]["teacher_name"] = combined_teacher_name
                    except Exception as e:
                        print(f"[DEBUG] Error building combined teacher name in cache reuse: {e}")
                        # Fallback to just primary teacher name
                        cached_json["metadata"]["teacher_name"] = slot.get("primary_teacher_name") or "Unknown"
                    
                    # Force update key fields from current slot config (Unconditionally)
                    cached_json["metadata"]["grade"] = slot.get("grade")
                    cached_json["metadata"]["homeroom"] = slot.get("homeroom")
                    cached_json["metadata"]["subject"] = slot.get("subject")
                    
                    if slot.get("slot_number") == 2:
                        print(f"DEBUG: Cache Inject Slot 2 -> Grade: '{cached_json['metadata']['grade']}', Homeroom: '{cached_json['metadata']['homeroom']}', Teacher: '{cached_json['metadata'].get('teacher_name')}'")
                        
                    return cached_json
            elif cache_hit and existing_lesson_json and force_ai:
                print(
                    f"[DEBUG] FORCING AI transformation for slot {slot.get('slot_number')} ({slot['subject']}) as requested."
                )

            # Check for "No School" week
            # If the entire document indicates "No School", we generate a standardized
            # "No School" lesson plan instead of trying to parse content.
            if parser.is_no_school_day():
                logger.info(
                    "no_school_week_detected",
                    extra={
                        "slot": slot["slot_number"],
                        "subject": slot["subject"],
                        "file": primary_file,
                    },
                )

                # Reconstruct user dict for teacher name builder
                user_dict = {
                    "first_name": self._user_first_name,
                    "last_name": self._user_last_name,
                    "name": self._user_name,
                }

                # Create standardized "No School" lesson JSON
                return {
                    "metadata": {
                        "teacher_name": self._build_teacher_name(user_dict, slot),
                        "grade": slot.get("grade", ""),
                        "subject": slot["subject"],
                        "week_of": week_of,
                        "homeroom": slot.get("homeroom", ""),
                        "slot_number": slot["slot_number"],
                    },
                    "days": {
                        day: {"unit_lesson": "No School"}
                        for day in [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                        ]
                    },
                    "_images": [],
                    "_hyperlinks": [],
                }

            # Early validation: Check if requested slot exists in document
            print("DEBUG: _process_slot - Validating slot availability")
            total_tables = len(parser.doc.tables)

            # Check for signature table
            has_signature = False
            if total_tables > 0:
                last_table = parser.doc.tables[-1]
                if last_table.rows and last_table.rows[0].cells:
                    first_cell = last_table.rows[0].cells[0].text.strip().lower()
                    if "signature" in first_cell or "required signatures" in first_cell:
                        has_signature = True

            # Calculate available slots
            if has_signature:
                available_slots = (total_tables - 1) // 2
            else:
                available_slots = total_tables // 2

            # Store available_slots for later validation
            # Don't validate immediately - let subject detection try first
            # If subject matches slot 1, we can auto-map slot 5 -> slot 1
            requested_slot = slot["slot_number"]
            print(
                f"DEBUG: _process_slot - Document has {available_slots} available slots, requested: {requested_slot}"
            )

            # Don't validate here - let subject detection and auto-mapping handle it
            # This allows slot 5 to be auto-mapped to slot 1 when document only has 1 slot

            # INSTRUMENTATION: Log table structure for analysis
            print("DEBUG: _process_slot - Logging table structure")
            logger.info(
                "document_table_structure",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "file": Path(primary_file).name,
                    "total_tables": total_tables,
                },
            )

            # Log each table's structure
            for table_idx, table in enumerate(parser.doc.tables):
                first_cell = ""
                if table.rows and table.rows[0].cells:
                    first_cell = table.rows[0].cells[0].text.strip()

                # Get first row text for additional context
                first_row_text = ""
                if table.rows:
                    first_row_text = " | ".join(
                        cell.text.strip()[:30] for cell in table.rows[0].cells[:5]
                    )

                logger.info(
                    "table_structure_detail",
                    extra={
                        "slot": slot["slot_number"],
                        "file": Path(primary_file).name,
                        "table_idx": table_idx,
                        "first_cell": first_cell[:100],
                        "first_row": first_row_text[:200],
                        "row_count": len(table.rows),
                        "col_count": len(table.columns) if table.rows else 0,
                    },
                )

        except Exception as e:
            logger.error(
                "docx_parser_init_failed",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "file": primary_file,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

        # CRITICAL: Extract primary teacher name for disambiguation (normalize once)
        primary_first = slot.get("primary_teacher_first_name", "").strip()
        primary_last = slot.get("primary_teacher_last_name", "").strip()
        teacher_name = (
            f"{primary_first} {primary_last}".strip()
            or slot.get("primary_teacher_name", "").strip()
        )

        # CRITICAL: Find actual slot number by subject in source file
        # This handles cases where slot numbers don't align (e.g., Savoca ELA/SS is Slot 1, Wilson config is Slot 2)
        print(
            f"DEBUG: _process_slot - Finding actual slot for subject '{slot['subject']}'"
        )
        try:
            # Track slot finding operation
            if plan_id:
                # Capture parser in closure to avoid linter warnings
                _parser = parser

                def _find_slot_with_tracking():
                    with self.tracker.track_operation(
                        plan_id,
                        "parse_find_slot",
                        metadata={
                            "requested_slot": slot["slot_number"],
                            "subject": slot["subject"],
                        },
                    ):
                        return _parser.find_slot_by_subject(
                            slot["subject"],
                            teacher_name,
                            slot.get("homeroom"),
                            slot.get("grade"),
                        )

                actual_slot_num = await asyncio.to_thread(_find_slot_with_tracking)
            else:
                actual_slot_num = await asyncio.to_thread(
                    parser.find_slot_by_subject,
                    slot["subject"],
                    teacher_name,
                    slot.get("homeroom"),
                    slot.get("grade"),
                )
            if actual_slot_num != slot["slot_number"]:
                print(
                    f"DEBUG: _process_slot - Slot mismatch! Requested slot {slot['slot_number']}, found subject in slot {actual_slot_num}"
                )

                # Determine if this is expected behavior (single-slot document)
                is_single_slot = available_slots == 1
                is_expected = is_single_slot

                # Build enhanced warning message
                warning_type = "slot_subject_mismatch"
                if is_single_slot:
                    warning_type = "slot_subject_mismatch_single_slot"
                    message = (
                        f"Slot {slot['slot_number']} requested, but document '{Path(primary_file).name}' "
                        f"has only 1 slot. Content correctly extracted from slot 1. "
                        f"This is expected behavior for single-slot documents."
                    )
                else:
                    warning_type = "slot_subject_mismatch_multi_slot"
                    message = (
                        f"Slot {slot['slot_number']} requested for '{slot['subject']}', but document "
                        f"'{Path(primary_file).name}' has '{slot['subject']}' in slot {actual_slot_num}. "
                        f"Content correctly extracted via subject-based detection. "
                        f"Consider updating slot configuration to match document structure (slot {actual_slot_num})."
                    )

                logger.warning(
                    warning_type,
                    extra={
                        "requested_slot": slot["slot_number"],
                        "actual_slot": actual_slot_num,
                        "subject": slot["subject"],
                        "file": Path(primary_file).name,
                        "available_slots": available_slots,
                        "is_single_slot": is_single_slot,
                        "is_expected": is_expected,
                        "message": message,
                        "teacher": teacher_name,
                        "grade": slot.get("grade"),
                        "homeroom": slot.get("homeroom"),
                    },
                )
            slot_num = actual_slot_num
        except ValueError as e:
            # Subject not found - check if requested slot is valid
            print(f"DEBUG: _process_slot - Subject detection failed: {e}")

            # If requested slot exceeds available slots, auto-map to slot 1
            # This handles cases where config says slot 5 but document only has 1 slot
            if slot["slot_number"] > available_slots:
                print(
                    f"DEBUG: _process_slot - Requested slot {slot['slot_number']} > available slots ({available_slots}). "
                    f"Auto-mapping to slot 1."
                )
                logger.warning(
                    "slot_auto_mapped",
                    extra={
                        "requested_slot": slot["slot_number"],
                        "available_slots": available_slots,
                        "mapped_to": 1,
                        "subject": slot["subject"],
                        "file": Path(primary_file).name,
                        "message": (
                            f"Slot {slot['slot_number']} requested, but document '{Path(primary_file).name}' "
                            f"has only {available_slots} slot(s). Auto-mapped to slot 1. "
                            f"This is expected behavior for single-slot documents."
                        ),
                        "teacher": teacher_name,
                        "grade": slot.get("grade"),
                        "homeroom": slot.get("homeroom"),
                    },
                )
                slot_num = 1  # Auto-map to first slot
            else:
                # Requested slot is valid, use it
                print(
                    f"DEBUG: _process_slot - Using requested slot {slot['slot_number']} as fallback (validated: {available_slots} slots available)"
                )
                slot_num = slot["slot_number"]

        # Extract images and hyperlinks (metadata, won't be sent to LLM) - sync I/O
        # Use slot-aware extraction (table-only, no paragraphs) to prevent cross-contamination
        print(
            f"DEBUG: _process_slot - Extracting images and hyperlinks for slot {slot_num} (subject: {slot['subject']})"
        )
        update_slot_progress("processing", 20, "Extracting content from lesson plan...")

        try:
            # Track image and hyperlink extraction
            if plan_id:
                # Capture parser in closure to avoid linter warnings
                _parser = parser

                def _extract_media_with_tracking():
                    images_result = None
                    hyperlinks_result = None
                    with self.tracker.track_operation(
                        plan_id,
                        "parse_extract_images",
                        metadata={
                            "slot_number": slot_num,
                            "subject": slot["subject"],
                        },
                    ):
                        images_result = _parser.extract_images_for_slot(slot_num)
                    with self.tracker.track_operation(
                        plan_id,
                        "parse_extract_hyperlinks",
                        metadata={
                            "slot_number": slot_num,
                            "subject": slot["subject"],
                        },
                    ):
                        hyperlinks_result = _parser.extract_hyperlinks_for_slot(
                            slot_num
                        )
                    return images_result, hyperlinks_result

                images, hyperlinks = await asyncio.to_thread(
                    _extract_media_with_tracking
                )
            else:
                images = await asyncio.to_thread(
                    parser.extract_images_for_slot, slot_num
                )
                hyperlinks = await asyncio.to_thread(
                    parser.extract_hyperlinks_for_slot, slot_num
                )
            print(
                f"[DEBUG] _process_slot (SEQUENTIAL): Extracted {len(images)} images, {len(hyperlinks)} hyperlinks "
                f"for slot {slot['slot_number']}, subject {slot['subject']}"
            )

            # DIAGNOSTIC: Log extracted hyperlinks
            from tools.diagnostic_logger import get_diagnostic_logger

            diag = get_diagnostic_logger()
            diag.log_hyperlinks_extracted(
                slot["slot_number"], slot["subject"], hyperlinks, primary_file
            )

            logger.info(
                "slot_media_extracted",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "images_count": len(images),
                    "hyperlinks_count": len(hyperlinks),
                    "extraction_mode": "slot_aware",
                    "processing_path": "sequential",
                },
            )

            # LOGGING: Log hyperlink details for debugging
            if hyperlinks:
                print(
                    f"[DEBUG] _process_slot (SEQUENTIAL): Hyperlink details: "
                    f"{[(h.get('text', '')[:30], h.get('url', '')[:50]) for h in hyperlinks[:3]]}"
                )
        except ValueError as e:
            # Structure validation failed - log and re-raise
            logger.error(
                "slot_structure_invalid",
                extra={
                    "slot": slot_num,
                    "subject": slot["subject"],
                    "file": primary_file,
                    "error": str(e),
                },
            )
            raise
        except Exception as e:
            logger.error(
                "media_extraction_failed",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "file": primary_file,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            # Continue without media - don't crash the whole process
            images = []
            hyperlinks = []

        # Check for "No School" day - skip LLM processing if detected
        print("DEBUG: _process_slot - Checking for No School day")
        if parser.is_no_school_day():
            print(
                "DEBUG: _process_slot - No School day detected, returning minimal JSON"
            )
            logger.info(
                "no_school_day_skipped",
                extra={
                    "slot": slot["slot_number"],
                    "subject": slot["subject"],
                    "file": primary_file,
                },
            )

            # Filter out all hyperlinks since entire document is No School
            if hyperlinks:
                filtered_count = len(hyperlinks)
                hyperlinks = []
                print(
                    f"DEBUG: _process_slot - Filtered {filtered_count} hyperlinks (entire document is No School)"
                )
                logger.info(
                    "hyperlinks_filtered_no_school",
                    extra={
                        "slot": slot["slot_number"],
                        "subject": slot["subject"],
                        "reason": "entire_document_no_school",
                        "filtered_count": filtered_count,
                    },
                )

            # Return minimal JSON structure indicating "No School"
            # This will be handled specially during rendering
            no_school_json = {
                "metadata": {
                    "week_of": week_of,
                    "grade": slot["grade"],
                    "subject": slot["subject"],
                    "homeroom": slot.get("homeroom"),
                    "no_school": True,
                },
                "days": {
                    day: {
                        "unit_lesson": "No School",
                        "objective": {
                            "content_objective": "No School",
                            "student_goal": "No School",
                            "wida_objective": "No School",
                        },
                        "anticipatory_set": {
                            "original_content": "No School",
                            "bilingual_bridge": "",
                        },
                        "tailored_instruction": {
                            "original_content": "No School",
                            "co_teaching_model": {},
                            "ell_support": [],
                            "special_needs_support": [],
                            "materials": [],
                        },
                        "misconceptions": {
                            "original_content": "No School",
                            "linguistic_note": {},
                        },
                        "assessment": {
                            "primary_assessment": "No School",
                            "bilingual_overlay": {},
                        },
                        "homework": {
                            "original_content": "No School",
                            "family_connection": "",
                        },
                    }
                    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
            }

            # Only include hyperlinks if there are any (should be empty after filtering)
            if hyperlinks:
                no_school_json["_hyperlinks"] = hyperlinks
                no_school_json["_media_schema_version"] = "2.0"

            # CRITICAL: Clean up parser before returning
            del parser
            import gc

            gc.collect()

            return no_school_json

        print("DEBUG: _process_slot - Extracting subject content (SLOT-AWARE)")
        update_slot_progress("processing", 25, "Parsing lesson content...")
        # Track content extraction
        if plan_id:
            # Capture parser in closure to avoid linter warnings
            _parser = parser

            def _extract_content_with_tracking():
                with self.tracker.track_operation(
                    plan_id,
                    "parse_extract_content",
                    metadata={
                        "slot_number": slot_num,
                        "subject": slot["subject"],
                    },
                ):
                    # CRITICAL: strip_urls=False so we can see markdown links/raw URLs
                    # and replace them with tokens before sending to LLM.
                    return _parser.extract_subject_content_for_slot(
                        slot_num, slot["subject"], teacher_name, strip_urls=False
                    )

            content = await asyncio.to_thread(_extract_content_with_tracking)
        else:
            content = await asyncio.to_thread(
                parser.extract_subject_content_for_slot,
                slot_num,
                slot["subject"],
                teacher_name,
                strip_urls=False,
            )
        print(
            f"DEBUG: _process_slot - Content extracted, length: {len(content.get('full_text', ''))}, slot: {slot_num}"
        )

        # Detect which days actually have content
        available_days = []
        if "table_content" in content:
            for day, day_content in content["table_content"].items():
                day_lower = day.lower().strip()
                # Check if it's "All Days" (single-lesson format)
                if day_lower == "all days":
                    # For single-lesson documents, assume it's Monday
                    available_days = ["monday"]
                    print(
                        "DEBUG: _process_slot - Single-lesson format detected, generating only Monday"
                    )
                    break
                # Check if this day has actual content (not empty, not "No School")
                elif day_lower in [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                ]:
                    # Check if day has content
                    day_text = (
                        " ".join(day_content.values())
                        if isinstance(day_content, dict)
                        else str(day_content)
                    )
                    if day_text and day_text.strip().lower() not in [
                        "no school",
                        "n/a",
                        "",
                    ]:
                        available_days.append(day_lower)
                        print(f"DEBUG: _process_slot - Day {day_lower} has content")

        # If no days detected, default to all 5 days (backward compatibility)
        if not available_days:
            available_days = None  # None means generate all days
            print(
                "DEBUG: _process_slot - No specific days detected, will generate all 5 days"
            )
        else:
            print(
                f"DEBUG: _process_slot - Generating content for days: {available_days}"
            )

        # Persistence (extraction cache)
        await self._persist_original_lesson_plan(
            slot,
            week_of,
            primary_file,
            teacher_name,
            content,
            hyperlinks,
            available_days,
            plan_id,
        )

        # CRITICAL: Extract original unit/lesson and objective content for preservation
        original_unit_lessons = {}  # day -> original unit/lesson text
        original_objectives = {}  # day -> original objective text

        if "table_content" in content:
            for day, day_content in content["table_content"].items():
                # day_content is {label: text} dict
                # Find unit/lesson row (stop after first match per day)
                day_lower = day.lower()

                for label, text in day_content.items():
                    label_lower = label.lower().strip()

                    # Match Unit/Lesson row (be specific to avoid false matches)
                    # Look for labels like "Unit, Lesson #, Module:", "Unit/Lesson:", etc.
                    if day_lower not in original_unit_lessons:
                        if (
                            (
                                "unit" in label_lower
                                and ("lesson" in label_lower or "module" in label_lower)
                            )
                            or label_lower.startswith("unit")
                            or label_lower.startswith("lesson")
                        ):
                            original_unit_lessons[day_lower] = text
                            print(
                                f"DEBUG: Extracted unit/lesson for {day}: '{text[:50]}...'"
                            )

                    # Match Objective row (be specific)
                    if day_lower not in original_objectives:
                        if label_lower.startswith("objective"):
                            original_objectives[day_lower] = text
                            print(
                                f"DEBUG: Extracted objective for {day}: '{text[:50]}...'"
                            )

            print(
                f"DEBUG: Extracted {len(original_unit_lessons)} unit/lessons, {len(original_objectives)} objectives"
            )

        # Transform with LLM - track performance
        primary_content = content["full_text"]

        # Check for No School days - we'll handle them post-LLM
        no_school_days = content.get("no_school_days", [])
        if no_school_days:
            print(f"DEBUG: _process_slot - No School days detected: {no_school_days}")
            # Don't add instruction - we'll replace the LLM output for these days later

            # Filter out hyperlinks from No School days
            # Normalize day names for comparison (day_hint might be lowercase, no_school_days might be uppercase)
            no_school_days_normalized = {day.lower().strip() for day in no_school_days}
            initial_count = len(hyperlinks)

            # Track links without day_hint for diagnostics
            links_without_day_hint = [h for h in hyperlinks if not h.get("day_hint")]

            hyperlinks = [
                h
                for h in hyperlinks
                if not h.get("day_hint")
                or h.get("day_hint", "").lower().strip()
                not in no_school_days_normalized
            ]

            filtered_count = initial_count - len(hyperlinks)

            # Log diagnostics for links preserved without day_hint
            if links_without_day_hint:
                logger.info(
                    "hyperlinks_preserved_no_day_hint",
                    extra={
                        "slot": slot["slot_number"],
                        "subject": slot["subject"],
                        "no_school_days": no_school_days,
                        "links_without_day_hint_count": len(links_without_day_hint),
                        "preserved_links": [
                            {
                                "text": h.get("text", "")[:50],
                                "section_hint": h.get("section_hint"),
                            }
                            for h in links_without_day_hint[:5]  # Limit to first 5
                        ],
                    },
                )

            if filtered_count > 0:
                logger.info(
                    "hyperlinks_filtered_no_school",
                    extra={
                        "slot": slot["slot_number"],
                        "subject": slot["subject"],
                        "no_school_days": no_school_days,
                        "filtered_count": filtered_count,
                        "remaining_count": len(hyperlinks),
                    },
                )

        # Get full text content for LLM
        primary_content = content.get("full_text", "")

        # --- PHASE 1: Link Placeholder Strategy (Pre-LLM Scrubbing) ---
        # Initialize a temporary context for scrubbing
        temp_context = SlotProcessingContext(
            slot=slot,
            slot_index=slot_index,
            total_slots=total_slots,
            extracted_content=primary_content,
        )
        self._scrub_hyperlinks(temp_context)
        # Use scrubbed content for LLM
        scrubbed_primary_content = temp_context.extracted_content

        # Add preservation instruction if placeholders were found
        if temp_context.link_map:
            preserve_msg = (
                f"\n\nIMPORTANT: Your input contains placeholders like {', '.join(list(temp_context.link_map.keys())[:5])}. "
                f"These represent hyperlinks. You MUST preserve these exact tokens in your output."
            )
            scrubbed_primary_content += preserve_msg

        print("DEBUG: _process_slot - Starting LLM transformation")
        update_slot_progress("processing", 30, "Preparing for transformation...")

        # Note: Detailed tracking is now handled by sub-operations (LLM service tracks internally)
        # No need for top-level process_slot wrapper - let sub-operations be tracked individually

        try:
            print("DEBUG: _process_slot - Calling LLM service transform_lesson")
            update_slot_progress(
                "processing", 40, f"Transforming {slot['subject']} with AI..."
            )

            # LLM call is sync HTTP request - run in thread to avoid blocking event loop
            # Create a progress callback that updates slot progress
            def llm_progress_callback(stage: str, llm_progress: int, message: str):
                """Callback to update progress during LLM transformation."""
                # Map LLM progress (0-100) to slot progress range (8-70%)
                # LLM starts at 10% and goes to 90%, map to slot range 8-70%
                slot_progress_min = 8
                slot_progress_max = 70
                slot_progress = slot_progress_min + int(
                    (llm_progress - 10)
                    / 80
                    * (slot_progress_max - slot_progress_min)
                )
                update_slot_progress(stage, slot_progress, message)

            success, lesson_json, error = await asyncio.to_thread(
                self.llm_service.transform_lesson,
                primary_content=scrubbed_primary_content,
                grade=slot["grade"],
                subject=slot["subject"],
                week_of=week_of,
                teacher_name=None,  # Will be added later
                homeroom=slot.get("homeroom"),
                plan_id=plan_id,  # Pass plan_id for detailed tracking
                available_days=available_days,  # Pass detected days
                progress_callback=llm_progress_callback,
            )

            print(
                f"DEBUG: _process_slot - LLM transform_lesson returned, success: {success}"
            )
            update_slot_progress(
                "processing", 70, "Processing transformation results..."
            )

            if not success:
                print(f"DEBUG: _process_slot - LLM transformation failed: {error}")
                raise ValueError(f"LLM transformation failed: {error}")

            # Ensure lesson_json is a dictionary immediately after LLM call
            # LLM service may return SQLModel/Pydantic objects that cause ModelPrivateAttr errors
            if not isinstance(lesson_json, dict):
                if hasattr(lesson_json, "model_dump"):
                    lesson_json = lesson_json.model_dump(mode="python")
                elif hasattr(lesson_json, "dict"):
                    lesson_json = lesson_json.dict()
                else:
                    lesson_json = dict(lesson_json) if lesson_json else {}

            # --- PHASE 2: Link Placeholder Strategy (Post-LLM Restoration) ---
            # Restore links from placeholders in the generated JSON
            if temp_context.link_map:
                print(
                    f"DEBUG: _process_slot - Restoring {len(temp_context.link_map)} links from placeholders"
                )
                lesson_json, restored_originals = self._restore_hyperlinks(
                    lesson_json, temp_context.link_map
                )

                # Filter out the hyperlinks that were already restored inline
                # so the renderer doesn't try to place them again (prevent duplication)
                if restored_originals:
                    initial_count = len(hyperlinks)
                    hyperlinks = [
                        h
                        for h in hyperlinks
                        if f"[{h['text']}]({h['url']})" not in restored_originals
                        and h["url"] not in restored_originals
                    ]
                    removed_count = initial_count - len(hyperlinks)
                    if removed_count > 0:
                        print(
                            f"DEBUG: _process_slot - Filtered {removed_count} redundant hyperlinks"
                        )

            # Remove usage information from lesson_json (already tracked by LLM service)
            lesson_json.pop("_usage", {})
            lesson_json.pop("_model", "")
            lesson_json.pop("_provider", "")

            # CRITICAL: Restore original unit/lesson and objective content
            print(
                "DEBUG: _process_slot - Restoring original unit/lesson and objective content"
            )
            for day_lower, day_data in lesson_json.get("days", {}).items():
                # Restore original unit/lesson (exact copy from input)
                if day_lower in original_unit_lessons:
                    day_data["unit_lesson"] = original_unit_lessons[day_lower]
                    print(f"DEBUG: Restored unit/lesson for {day_lower}")

                # Restore original objective content (preserve teacher's wording)
                if day_lower in original_objectives and "objective" in day_data:
                    day_data["objective"]["content_objective"] = original_objectives[
                        day_lower
                    ]
                    print(f"DEBUG: Restored objective content for {day_lower}")

            # Replace No School days with minimal content
            update_slot_progress("processing", 85, "Finalizing lesson plan...")
            if no_school_days:
                print(
                    f"DEBUG: _process_slot - Replacing {len(no_school_days)} No School days in output"
                )
                for day in no_school_days:
                    day_lower = day.lower()
                    if day_lower in lesson_json.get("days", {}):
                        lesson_json["days"][day_lower] = self._no_school_day_stub()

            # Store images and hyperlinks as metadata (underscore prefix = won't be sent to LLM)
            # CRITICAL: Add slot and subject metadata to hyperlinks for proper filtering in multi-slot scenarios
            slot_number = slot.get("slot_number")
            subject = slot.get("subject")
            if hyperlinks:
                for hyperlink in hyperlinks:
                    # Ensure hyperlink has slot/subject metadata for renderer filtering
                    if "_source_slot" not in hyperlink:
                        hyperlink["_source_slot"] = slot_number
                    if "_source_subject" not in hyperlink:
                        hyperlink["_source_subject"] = subject

            if images:
                lesson_json["_images"] = images
            if hyperlinks:
                print(
                    f"[DEBUG] _process_slot (SEQUENTIAL): Adding {len(hyperlinks)} hyperlinks to lesson_json "
                    f"for slot {slot.get('slot_number')}, subject {slot.get('subject')}"
                )
                lesson_json["_hyperlinks"] = hyperlinks
                logger.info(
                    "sequential_hyperlinks_attached",
                    extra={
                        "slot": slot.get("slot_number"),
                        "subject": slot.get("subject"),
                        "hyperlinks_count": len(hyperlinks),
                    },
                )

                # DIAGNOSTIC: Log lesson JSON with hyperlinks
                from tools.diagnostic_logger import get_diagnostic_logger

                diag = get_diagnostic_logger()
                diag.log_lesson_json_created(
                    slot["slot_number"], slot["subject"], lesson_json
                )
            else:
                print(
                    f"[WARN] _process_slot (SEQUENTIAL): No hyperlinks extracted for slot {slot.get('slot_number')}, "
                    f"subject {slot.get('subject')}!"
                )
                logger.warning(
                    "sequential_no_hyperlinks",
                    extra={
                        "slot": slot.get("slot_number"),
                        "subject": slot.get("subject"),
                    },
                )

            # Set schema version for coordinate-based placement (if media present)
            if images or hyperlinks:
                lesson_json["_media_schema_version"] = (
                    "2.0"  # Use v2.0 for coordinate placement
                )

            # Update metadata with structured teacher name and formatted week
            # Ensure lesson_json is a dictionary before using 'in' operator
            if not isinstance(lesson_json, dict):
                if hasattr(lesson_json, "model_dump"):
                    lesson_json = lesson_json.model_dump()
                elif hasattr(lesson_json, "dict"):
                    lesson_json = lesson_json.dict()
                else:
                    lesson_json = dict(lesson_json) if lesson_json else {}

            if "metadata" not in lesson_json:
                lesson_json["metadata"] = {}

            # Build teacher name using structured fields with fallback
            try:
                teacher_name = self._build_teacher_name(
                    {
                        "first_name": getattr(self, "_user_first_name", ""),
                        "last_name": getattr(self, "_user_last_name", ""),
                        "name": getattr(self, "_user_name", ""),
                    },
                    slot,
                )
                lesson_json["metadata"]["teacher_name"] = teacher_name
            except Exception as e:
                print(f"DEBUG: Error in _build_teacher_name: {e}")
                traceback.print_exc()
                # Continue with default
                lesson_json["metadata"]["teacher_name"] = "Unknown"

            # Format week dates consistently
            lesson_json["metadata"]["week_of"] = format_week_dates(week_of)

            # Preserve slot metadata (homeroom, grade, subject, time, primary teacher) from slot data
            # This ensures correct values even if LLM returns incorrect/missing data
            # Use .get() instead of 'in' to avoid ModelPrivateAttr issues
            try:
                # Unconditionally preserve metadata
                lesson_json["metadata"]["slot_number"] = slot.get("slot_number")
                lesson_json["metadata"]["homeroom"] = slot.get("homeroom")
                lesson_json["metadata"]["grade"] = slot.get("grade")
                lesson_json["metadata"]["subject"] = slot.get("subject")
                lesson_json["metadata"]["start_time"] = slot.get("start_time")
                lesson_json["metadata"]["end_time"] = slot.get("end_time")
                lesson_json["metadata"]["day_times"] = slot.get("day_times")
                # Preserve primary teacher fields for slot-specific teacher display
                lesson_json["metadata"]["primary_teacher_name"] = slot.get("primary_teacher_name")
                lesson_json["metadata"]["primary_teacher_first_name"] = slot.get("primary_teacher_first_name")
                lesson_json["metadata"]["primary_teacher_last_name"] = slot.get("primary_teacher_last_name")

                # DIAGNOSTIC LOGGING
                if slot.get("slot_number") == 2:
                    print(f"DEBUG: Preserving Slot 2 Metadata -> Grade: '{lesson_json['metadata']['grade']}', Homeroom: '{lesson_json['metadata']['homeroom']}'")
            except Exception as e:
                print(f"DEBUG: Error copying slot metadata: {e}")
                traceback.print_exc()

            try:
                normalize_objectives_in_lesson(lesson_json)
            except Exception as e:
                print(f"DEBUG: Error in normalize_objectives_in_lesson: {e}")
                traceback.print_exc()

            # CRITICAL: Clean up parser to release file handle
            # This prevents "Package not found" errors when multiple slots use the same file
            del parser
            import gc

            gc.collect()

            return lesson_json

        except Exception:
            # Error tracking is handled by sub-operations
            raise

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
