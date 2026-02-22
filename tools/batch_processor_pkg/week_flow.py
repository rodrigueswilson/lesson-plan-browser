"""
Week-level batch processing flow: load user/slots, enrich, parallel or sequential process, combine.
Extracted from orchestrator.process_user_week for Session 13.
"""

import asyncio
import copy
import json
import re
import traceback
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.progress import progress_tracker
from backend.telemetry import logger
from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps

from tools.json_merger import merge_lesson_jsons


async def run_process_user_week(
    processor: Any,
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
    """Process all class slots for a user's week. Delegates to processor for DB, tracker, and slot/combine methods."""
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
    db = processor.get_db(user_id=user_id)
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
            try:
                existing_lesson_json = json.loads(existing_lesson_json)
            except Exception:
                existing_lesson_json = None

        if existing_lesson_json:
            # Enrich from steps if needed (api.py logic)
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
    processor._current_user_id = user_id
    # Prefer base_path_override, but fall back to base_path if available in the user object
    processor._user_base_path = user.get("base_path_override") or user.get("base_path")
    processor._user_first_name = user.get("first_name", "")
    processor._user_last_name = user.get("last_name", "")
    processor._user_name = user.get("name", "")
    logger.info(
        "batch_user_base_path",
        extra={
            "user_id": user_id,
            "user_name": user["name"],
            "base_path": processor._user_base_path or "default",
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
    processor._current_plan_id = plan_id

    # Start tracking total batch duration
    batch_op_id = ""
    try:
        batch_op_id = processor.tracker.start_operation(
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
        contexts = await processor._extract_slots_parallel_db(
            slots,
            week_of,
            week_folder_path,
            processor._user_base_path,
            plan_id,
            progress_tracker,
        )

        # AUTO-GENERATE ORIGINALS AUDIT DOCX (Parallel Path)
        try:
            logger.info("batch_auto_generating_originals_docx_parallel")
            originals_docx = await processor._generate_combined_original_docx(
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
            existing_slot_plans = processor._reconstruct_slots_from_json(
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

        contexts = await processor._process_slots_parallel_llm(
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
                    slot = processor._sanitize_slot(slot)
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
                slot = processor._sanitize_slot(slot)

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
                lesson_json = await processor._process_slot(
                    slot,
                    week_of,
                    provider,
                    week_folder_path,
                    processor._user_base_path,
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
            originals_docx = await processor._generate_combined_original_docx(
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
        existing_slots_by_number = processor._reconstruct_slots_from_json(
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
                processor._combine_lessons,
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

    # End tracking total batch duration
    try:
        if batch_op_id:
            processor.tracker.end_operation(
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
