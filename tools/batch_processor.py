"""
Batch processor for handling multiple class slots and generating combined lesson plans.
Processes all user's class slots and combines them into a single DOCX output.
"""

import asyncio
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Inches, Pt

from backend.config import settings
import traceback

# DEBUG FLAG: Set to True to skip actual LLM calls and return mock data
# This helps isolate where the ModelPrivateAttr error is occurring
MOCK_LLM_CALL = False  # Changed to False to enable real LLM calls

from backend.database import get_db
from backend.file_manager import get_file_manager
from backend.llm_service import LLMService
from backend.performance_tracker import get_tracker
from backend.progress import progress_tracker
from backend.services.objectives_utils import normalize_objectives_in_lesson
from backend.telemetry import logger
from backend.utils.date_formatter import format_week_dates
from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer


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

    def _build_teacher_name(self, user: Dict[str, Any], slot: Dict[str, Any]) -> str:
        """
        Build teacher name as "Primary First Last / Bilingual First Last".

        Fallback strategy:
        1. Try structured first/last names
        2. Fall back to legacy 'name' and 'primary_teacher_name' fields
        3. Return "Unknown" if all fail

        Args:
            user: User dictionary from database
            slot: Slot dictionary from database

        Returns:
            Formatted teacher name string
        """
        # Primary teacher name - normalize None to empty string before strip
        primary_first = (slot.get("primary_teacher_first_name") or "").strip()
        primary_last = (slot.get("primary_teacher_last_name") or "").strip()

        if primary_first and primary_last:
            primary_name = f"{primary_first} {primary_last}"
        elif primary_first or primary_last:
            primary_name = primary_first or primary_last
        else:
            # Fallback to legacy field
            primary_name = (slot.get("primary_teacher_name") or "").strip()

        # Bilingual teacher name - normalize None to empty string before strip
        bilingual_first = (user.get("first_name") or "").strip()
        bilingual_last = (user.get("last_name") or "").strip()

        if bilingual_first and bilingual_last:
            bilingual_name = f"{bilingual_first} {bilingual_last}"
        elif bilingual_first or bilingual_last:
            bilingual_name = bilingual_first or bilingual_last
        else:
            # Fallback to legacy field
            bilingual_name = (user.get("name") or "").strip()

        # Combine
        if primary_name and bilingual_name:
            return f"{primary_name} / {bilingual_name}"
        elif primary_name:
            return primary_name
        elif bilingual_name:
            return bilingual_name
        else:
            return "Unknown"

    async def process_user_week(
        self,
        user_id: str,
        week_of: str,
        provider: str = "openai",
        week_folder_path: Optional[str] = None,
        slot_ids: Optional[list] = None,
        plan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process all class slots for a user's week.

        Args:
            user_id: User ID
            week_of: Week date range (MM/DD-MM/DD)
            provider: LLM provider to use
            week_folder_path: Optional path to week folder (overrides auto-detection)
            slot_ids: Optional list of specific slot IDs to process
            plan_id: Optional plan ID for progress tracking (if already created)

        Returns:
            Dict with processing results
        """
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
                    slot_dict = slot_obj.model_dump(mode='python')
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
                    if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
                        try:
                            # Try to get the actual value
                            slot_dict[key] = getattr(slot_obj, key, None)
                        except:
                            slot_dict[key] = None
                    else:
                        slot_dict[key] = value
            
            # Fallback: Extract as dictionary from object attributes
            if slot_dict is None:
                slot_dict = {
                    "id": str(getattr(slot_obj, "id", "")) if hasattr(slot_obj, "id") else "",
                    "user_id": str(getattr(slot_obj, "user_id", "")) if hasattr(slot_obj, "user_id") else "",
                    "slot_number": int(getattr(slot_obj, "slot_number", 0)) if hasattr(slot_obj, "slot_number") else 0,
                    "subject": str(getattr(slot_obj, "subject", "")) if hasattr(slot_obj, "subject") else "",
                    "grade": str(getattr(slot_obj, "grade", "")) if hasattr(slot_obj, "grade") else "",
                    "homeroom": str(getattr(slot_obj, "homeroom", "")) if hasattr(slot_obj, "homeroom") else None,
                    "plan_group_label": str(getattr(slot_obj, "plan_group_label", "")) if hasattr(slot_obj, "plan_group_label") else None,
                    "proficiency_levels": str(getattr(slot_obj, "proficiency_levels", "")) if hasattr(slot_obj, "proficiency_levels") else None,
                    "primary_teacher_file": str(getattr(slot_obj, "primary_teacher_file", "")) if hasattr(slot_obj, "primary_teacher_file") else None,
                    "primary_teacher_name": str(getattr(slot_obj, "primary_teacher_name", "")) if hasattr(slot_obj, "primary_teacher_name") else None,
                    "primary_teacher_first_name": str(getattr(slot_obj, "primary_teacher_first_name", "")) if hasattr(slot_obj, "primary_teacher_first_name") else None,
                    "primary_teacher_last_name": str(getattr(slot_obj, "primary_teacher_last_name", "")) if hasattr(slot_obj, "primary_teacher_last_name") else None,
                    "primary_teacher_file_pattern": str(getattr(slot_obj, "primary_teacher_file_pattern", "")) if hasattr(slot_obj, "primary_teacher_file_pattern") else None,
                    "display_order": int(getattr(slot_obj, "display_order", 0)) if hasattr(slot_obj, "display_order") else 0,
                }
            
            # Ensure all values are safe (no ModelPrivateAttr objects)
            for key in list(slot_dict.keys()):
                value = slot_dict[key]
                if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
                    slot_dict[key] = None
                elif not isinstance(value, (str, int, float, bool, type(None), list, dict)):
                    # Convert other non-serializable types to None
                    try:
                        slot_dict[key] = str(value)
                    except:
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
        
        for slot in slots:
            # Find matching schedule entry (most common time for this slot_number)
            matching_entries = [
                e
                for e in schedule_entries_dict
                if e.get("slot_number") == slot.get("slot_number") and e.get("is_active", True)
            ]
            if matching_entries:
                # Use the most common start_time/end_time for this slot
                from collections import Counter

                times = [(e.get("start_time"), e.get("end_time")) for e in matching_entries]
                most_common_time = Counter(times).most_common(1)[0][0]
                slot["start_time"] = most_common_time[0]
                slot["end_time"] = most_common_time[1]
                print(
                    f"DEBUG: Enriched slot {slot.get('slot_number')} with time {slot.get('start_time')}-{slot.get('end_time')}"
                )
            else:
                print(f"DEBUG: No schedule entry found for slot {slot.get('slot_number')}")

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

        # Store user's base path and name fields for file resolution and metadata
        self._user_base_path = user.get("base_path_override")
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
            await asyncio.to_thread(
                db.update_weekly_plan, plan_id, status="processing"
            )

        # Store plan_id for tracking
        self._current_plan_id = plan_id

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

        for i, slot in enumerate(slots, 1):
            # Ensure slot is a dictionary with safe access
            slot_num = slot.get("slot_number") if isinstance(slot, dict) else getattr(slot, "slot_number", i)
            slot_subject = slot.get("subject") if isinstance(slot, dict) else getattr(slot, "subject", "Unknown")
            
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
                            "primary_teacher_name": getattr(slot, "primary_teacher_name", None),
                            "primary_teacher_first_name": getattr(slot, "primary_teacher_first_name", None),
                            "primary_teacher_last_name": getattr(slot, "primary_teacher_last_name", None),
                            "primary_teacher_file": getattr(slot, "primary_teacher_file", None),
                            "primary_teacher_file_pattern": getattr(slot, "primary_teacher_file_pattern", None),
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
                )
                print(f"DEBUG: _process_slot completed for slot {i}")
                print(f"DEBUG: Appending lesson for slot {i}")
                lessons.append(
                    {
                        "slot_number": slot.get("slot_number", i),
                        "subject": slot.get("subject", "Unknown"),
                        "lesson_json": lesson_json,
                    }
                )
                print(f"DEBUG: Lesson appended for slot {i}")
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
                print(f"ERROR: Exception in process_weekly_plan loop for slot {i}: {e}")
                traceback.print_exc()
                # Use safe access for error message
                slot_num = slot.get("slot_number") if isinstance(slot, dict) else getattr(slot, "slot_number", i)
                slot_subject = slot.get("subject") if isinstance(slot, dict) else getattr(slot, "subject", "Unknown")
                # Safely format error message, handling encoding errors
                try:
                    error_str = str(e)
                except UnicodeEncodeError:
                    error_str = repr(e).encode('ascii', 'replace').decode('ascii')
                error_msg = f"Slot {slot_num} ({slot_subject}): {error_str}"
                errors.append(error_msg)
                logger.error(
                    "batch_slot_error",
                    extra={
                        "plan_id": plan_id,
                        "slot_index": i,
                        "total_slots": len(slots),
                        "subject": slot["subject"],
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

        # Generate combined DOCX if we have any successful lessons
        print(f"\nDEBUG: Finished processing all slots, {len(lessons)} successful")
        output_file = None
        if lessons:
            try:
                print(f"DEBUG: About to render {len(lessons)} lessons")
                # Update progress: rendering
                rendering_progress = int(
                    processing_weight * 100 + rendering_weight * 50
                )
                print("DEBUG: Updating progress tracker for rendering")
                progress_tracker.update(
                    plan_id,
                    "rendering",
                    rendering_progress,
                    f"Rendering {len(lessons)} lessons to DOCX...",
                )
                print("DEBUG: Progress tracker updated for rendering")

                print("DEBUG: Calling _combine_lessons (wrapped in asyncio.to_thread)")
                output_file = await asyncio.to_thread(
                    self._combine_lessons, user, lessons, week_of, start_time, plan_id
                )
                print(f"DEBUG: _combine_lessons returned: {output_file}")

                # Update progress: complete
                print(
                    f"DEBUG: Updating progress tracker to complete (plan_id={plan_id})"
                )
                progress_tracker.update(
                    plan_id,
                    "complete",
                    100,
                    f"Successfully created lesson plan with {len(lessons)} slots",
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
            if lessons:
                if len(lessons) == 1:
                    # Single-slot: convert to slots format for consistency
                    single_lesson_json = lessons[0]["lesson_json"]
                    merged_lesson_json = self._convert_single_slot_to_slots_format(
                        single_lesson_json, 
                        lessons[0]["slot_number"],
                        lessons[0]["subject"]
                    )
                else:
                    # Multi-slot: merge lesson JSONs (already creates slots format)
                    from tools.json_merger import merge_lesson_jsons

                    merged_lesson_json = merge_lesson_jsons(lessons)

            await asyncio.to_thread(
                db.update_weekly_plan,
                plan_id,
                status="completed",
                output_file=output_file,
                lesson_json=merged_lesson_json,
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
                }
            )
            print(f"ERROR: {error_msg}")
            print(f"DEBUG: lessons={len(lessons)}, slots={len(slots)}, output_file={output_file}")
        
        return {
            "success": bool(output_file),
            "plan_id": plan_id,
            "output_file": output_file or "",
            "processed_slots": len(lessons),
            "failed_slots": len(errors),
            "total_time_ms": total_time,
            "consolidated": is_consolidated,
            "total_slots": len(slots),
            "errors": errors if errors else None,
        }

    def _sanitize_value(self, value: Any) -> Any:
        """Recursively sanitize a value to remove ModelPrivateAttr objects."""
        # Check for ModelPrivateAttr
        if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
            return None
            
        # Handle lists
        if isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
            
        # Handle dicts
        if isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
            
        # Handle Pydantic models (v1 and v2)
        if hasattr(value, "model_dump") and callable(value.model_dump):
            try:
                return self._sanitize_value(value.model_dump())
            except:
                pass
        
        if hasattr(value, "dict") and callable(value.dict):
            try:
                return self._sanitize_value(value.dict())
            except:
                pass
            
        return value

    def _sanitize_slot(self, slot: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure slot dictionary contains no ModelPrivateAttr objects."""
        print(f"DEBUG: _sanitize_slot called for slot type {type(slot)}")
        if not isinstance(slot, dict):
            # Try to convert to dict if it's a model
            if hasattr(slot, "model_dump"):
                try:
                    slot = slot.model_dump()
                except:
                    pass
            elif hasattr(slot, "dict"):
                try:
                    slot = slot.dict()
                except:
                    pass
            else:
                try:
                    slot = dict(slot)
                except:
                    pass
        
        if not isinstance(slot, dict):
            return slot # Can't do much else
            
        sanitized = {}
        for k, v in slot.items():
            sanitized[k] = self._sanitize_value(v)
            
        return sanitized

    def _convert_single_slot_to_slots_format(
        self, lesson_json: Dict[str, Any], slot_number: int, subject: str
    ) -> Dict[str, Any]:
        """
        Convert a single-slot lesson_json (old format) to the new slots format.
        
        Old format: days = { "monday": { "unit_lesson": ..., "objective": ..., ... } }
        New format: days = { "monday": { "slots": [{ "slot_number": 1, "subject": "...", ... }] } }
        
        Args:
            lesson_json: Lesson JSON in old single-slot format
            slot_number: Slot number to assign to the slot
            subject: Subject name to assign to the slot
            
        Returns:
            Lesson JSON in new slots format
        """
        if not lesson_json or not isinstance(lesson_json, dict):
            return lesson_json
        
        # If already in slots format, return as-is
        days = lesson_json.get("days", {})
        if not days:
            return lesson_json
        
        # Check if already in slots format (has slots array in at least one day)
        is_already_in_slots_format = any(
            isinstance(day_data, dict) 
            and "slots" in day_data 
            and isinstance(day_data["slots"], list)
            for day_data in days.values()
        )
        
        if is_already_in_slots_format:
            return lesson_json
        
        # Convert to slots format
        converted_days = {}
        for day_name, day_data in days.items():
            if not isinstance(day_data, dict):
                converted_days[day_name] = day_data
                continue
            
            # Create a slot from the day data
            slot = {
                "slot_number": slot_number,
                "subject": subject,
            }
            
            # Copy all day-level fields to the slot
            for key, value in day_data.items():
                slot[key] = value
            
            # Add metadata if available in the day data
            metadata = lesson_json.get("metadata", {})
            if "grade" in metadata and "grade" not in slot:
                slot["grade"] = metadata.get("grade")
            if "homeroom" in metadata and "homeroom" not in slot:
                slot["homeroom"] = metadata.get("homeroom")
            if "teacher_name" in metadata and "teacher_name" not in slot:
                slot["teacher_name"] = metadata.get("teacher_name")
            
            # Create new format with slots array
            converted_days[day_name] = {
                "slots": [slot]
            }
        
        # Create converted lesson_json
        converted_lesson_json = {
            **lesson_json,
            "days": converted_days
        }
        
        return converted_lesson_json

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
            # Track DOCX opening - wrap parser creation with tracking
            if plan_id:
                # Use track_operation context manager for parse_open_docx
                def _create_parser():
                    with self.tracker.track_operation(plan_id, "parse_open_docx"):
                        return DOCXParser(primary_file)

                parser = await asyncio.to_thread(_create_parser)
            else:
                parser = await asyncio.to_thread(DOCXParser, primary_file)
            print("DEBUG: _process_slot - DOCXParser created successfully")

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
                    "name": self._user_name
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
                        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
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
                            slot["subject"], teacher_name
                        )

                actual_slot_num = await asyncio.to_thread(_find_slot_with_tracking)
            else:
                actual_slot_num = await asyncio.to_thread(
                    parser.find_slot_by_subject, slot["subject"], teacher_name
                )
            if actual_slot_num != slot["slot_number"]:
                print(
                    f"DEBUG: _process_slot - Slot mismatch! Requested slot {slot['slot_number']}, found subject in slot {actual_slot_num}"
                )
                logger.warning(
                    "slot_subject_mismatch",
                    extra={
                        "requested_slot": slot["slot_number"],
                        "actual_slot": actual_slot_num,
                        "subject": slot["subject"],
                        "file": Path(primary_file).name,
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
                f"DEBUG: _process_slot - Extracted {len(images)} images, {len(hyperlinks)} hyperlinks"
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
                },
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
                    return _parser.extract_subject_content_for_slot(
                        slot_num, slot["subject"], teacher_name
                    )

            content = await asyncio.to_thread(_extract_content_with_tracking)
        else:
            content = await asyncio.to_thread(
                parser.extract_subject_content_for_slot,
                slot_num,
                slot["subject"],
                teacher_name,
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

        # Extract hyperlink texts to preserve them in LLM output
        hyperlink_texts = [h["text"] for h in hyperlinks if h.get("text")]
        if hyperlink_texts:
            # Add instruction to preserve exact hyperlink text
            preserve_instruction = (
                f"\n\nIMPORTANT: Preserve these exact phrases in your output "
                f"(they are hyperlinks): {', '.join(hyperlink_texts[:20])}"  # Limit to 20 to avoid token bloat
            )
            primary_content += preserve_instruction

        print("DEBUG: _process_slot - Starting LLM transformation")
        update_slot_progress("processing", 30, "Preparing for transformation...")

        # Note: Detailed tracking is now handled by sub-operations (LLM service tracks internally)
        # No need for top-level process_slot wrapper - let sub-operations be tracked individually

        try:
            print("DEBUG: _process_slot - Calling LLM service transform_lesson")
            update_slot_progress(
                "processing", 40, f"Transforming {slot['subject']} with AI..."
            )
            
            # Check MOCK_MODE flag
            if MOCK_LLM_CALL:
                print("DEBUG: MOCK_LLM_CALL is True - skipping actual LLM call")
                # Simulate delay
                await asyncio.sleep(1)
                success = True
                error = None
                # Generate mock lesson JSON
                lesson_json = {
                    "metadata": {
                        "week_of": week_of,
                        "grade": slot.get("grade", "6"),
                        "subject": slot.get("subject", "Mock Subject")
                    },
                    "days": {
                        day: {
                            "unit_lesson": f"Mock Unit - {day.capitalize()}",
                            "objective": {
                                "content_objective": "Mock Content Objective",
                                "student_goal": "Mock Student Goal",
                                "wida_objective": "Mock WIDA Objective"
                            },
                            "anticipatory_set": {
                                "original_content": "Mock Anticipatory",
                                "bilingual_bridge": "Mock Bridge"
                            },
                            "tailored_instruction": {
                                "original_content": "Mock Instruction",
                                "co_teaching_model": {"model_name": "Mock Model"},
                                "ell_support": [],
                                "special_needs_support": [],
                                "materials": []
                            },
                            "misconceptions": {
                                "original_content": "Mock Misconception",
                                "linguistic_note": {}
                            },
                            "assessment": {
                                "primary_assessment": "Mock Assessment",
                                "bilingual_overlay": {}
                            },
                            "homework": {
                                "original_content": "Mock Homework",
                                "family_connection": "Mock Family"
                            }
                        } for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    }
                }
            else:
                # LLM call is sync HTTP request - run in thread to avoid blocking event loop
                success, lesson_json, error = await asyncio.to_thread(
                    self.llm_service.transform_lesson,
                    primary_content=primary_content,
                    grade=slot["grade"],
                    subject=slot["subject"],
                    week_of=week_of,
                    teacher_name=None,  # Will be added later
                    homeroom=slot.get("homeroom"),
                    plan_id=plan_id,  # Pass plan_id for detailed tracking
                    available_days=available_days,  # Pass detected days
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

            # CRITICAL: Ensure lesson_json is a dictionary immediately after LLM call
            # LLM service may return SQLModel/Pydantic objects that cause ModelPrivateAttr errors
            if not isinstance(lesson_json, dict):
                if hasattr(lesson_json, "model_dump"):
                    lesson_json = lesson_json.model_dump(mode='python')
                elif hasattr(lesson_json, "dict"):
                    lesson_json = lesson_json.dict()
                else:
                    lesson_json = dict(lesson_json) if lesson_json else {}

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
                        lesson_json["days"][day_lower] = {
                            "unit_lesson": "No School",
                            "objective": {
                                "content_objective": "",
                                "student_goal": "",
                                "wida_objective": "",
                            },
                            "anticipatory_set": {
                                "original_content": "",
                                "bilingual_bridge": "",
                            },
                            "tailored_instruction": {
                                "original_content": "",
                                "co_teaching_model": {},
                                "ell_support": [],
                                "special_needs_support": [],
                                "materials": [],
                            },
                            "misconceptions": {
                                "original_content": "",
                                "linguistic_note": {},
                            },
                            "assessment": {
                                "primary_assessment": "",
                                "bilingual_overlay": {},
                            },
                            "homework": {
                                "original_content": "",
                                "family_connection": "",
                            },
                        }

            # Store images and hyperlinks as metadata (underscore prefix = won't be sent to LLM)
            if images:
                lesson_json["_images"] = images
            if hyperlinks:
                print(
                    f"[DEBUG] BATCH_PROCESSOR: Adding {len(hyperlinks)} hyperlinks to lesson_json"
                )
                lesson_json["_hyperlinks"] = hyperlinks

                # DIAGNOSTIC: Log lesson JSON with hyperlinks
                from tools.diagnostic_logger import get_diagnostic_logger

                diag = get_diagnostic_logger()
                diag.log_lesson_json_created(
                    slot["slot_number"], slot["subject"], lesson_json
                )
            else:
                print("[WARN] BATCH_PROCESSOR: No hyperlinks extracted!")

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

            # Preserve slot metadata (homeroom, grade, subject, time) from slot data
            # This ensures correct values even if LLM returns incorrect/missing data
            # Use .get() instead of 'in' to avoid ModelPrivateAttr issues
            try:
                if slot.get("homeroom"):
                    lesson_json["metadata"]["homeroom"] = slot["homeroom"]
                if slot.get("grade"):
                    lesson_json["metadata"]["grade"] = slot["grade"]
                if slot.get("subject"):
                    lesson_json["metadata"]["subject"] = slot["subject"]
                if slot.get("start_time"):
                    lesson_json["metadata"]["start_time"] = slot["start_time"]
                if slot.get("end_time"):
                    lesson_json["metadata"]["end_time"] = slot["end_time"]
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
        """
        Resolve primary teacher file using hybrid approach.

        Priority:
        1. Direct path if absolute and exists
        2. Direct path relative to week folder if exists
        3. Pattern-based search in week folder
        4. Fallback to input/ directory for testing

        Args:
            slot: Class slot data
            week_of: Week date range
            week_folder_path: Optional week folder override
            user_base_path: User's base path override

        Returns:
            Path to primary teacher file or None
        """
        from pathlib import Path

        # Get week folder
        if week_folder_path:
            week_folder = Path(week_folder_path)
        else:
            # Use user's base path override if available
            file_mgr = get_file_manager(base_path=user_base_path)
            week_folder = file_mgr.get_week_folder(week_of)

        logger.debug(
            "primary_file_resolve_start",
            extra={
                "slot_number": slot.get("slot_number"),
                "week_folder": str(week_folder),
                "week_folder_exists": week_folder.exists(),
                "primary_teacher_file": slot.get("primary_teacher_file"),
                "primary_teacher_name": slot.get("primary_teacher_name"),
                "primary_teacher_file_pattern": slot.get(
                    "primary_teacher_file_pattern"
                ),
            },
        )

        # Priority 1: Absolute path
        if slot.get("primary_teacher_file"):
            file_path = Path(slot["primary_teacher_file"])
            if file_path.is_absolute() and file_path.exists():
                logger.debug(
                    "primary_file_resolve_absolute",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "path": str(file_path),
                    },
                )
                return str(file_path)

            # Priority 2: Relative to week folder
            if week_folder.exists():
                relative_path = week_folder / file_path.name
                if relative_path.exists():
                    logger.debug(
                        "primary_file_resolve_relative",
                        extra={
                            "slot_number": slot.get("slot_number"),
                            "path": str(relative_path),
                        },
                    )
                    return str(relative_path)

        # Priority 3: Pattern-based search in week folder
        # Try pattern first, but if it doesn't match, fall back to last name
        
        def _safe_get(d, key, default=None):
            val = d.get(key, default)
            # Check if value is ModelPrivateAttr (which is not iterable and breaks boolean checks)
            if hasattr(val, "__class__") and "ModelPrivateAttr" in str(type(val)):
                return default
            return val

        teacher_pattern = _safe_get(slot, "primary_teacher_file_pattern")
        primary_name = _safe_get(slot, "primary_teacher_name")
        first_name = _safe_get(slot, "primary_teacher_first_name", "")
        last_name = _safe_get(slot, "primary_teacher_last_name", "")

        # If pattern is set, try it first
        if teacher_pattern:
            print(f"DEBUG: Using primary_teacher_file_pattern: '{teacher_pattern}'")
        # If no pattern, try primary_teacher_name
        elif primary_name:
            teacher_pattern = primary_name
            print(f"DEBUG: Using primary_teacher_name: '{teacher_pattern}'")
        # Fallback to first_name + last_name
        elif first_name or last_name:
            teacher_pattern = f"{first_name} {last_name}".strip()
            print(f"DEBUG: Using first_name + last_name: '{teacher_pattern}'")
        else:
            teacher_pattern = None
            print("DEBUG: No teacher pattern available")
        if teacher_pattern and week_folder.exists():
            print(f"DEBUG: Searching for pattern '{teacher_pattern}' in week folder")
            logger.debug(
                "primary_file_resolve_pattern",
                extra={
                    "slot_number": slot.get("slot_number"),
                    "pattern": teacher_pattern,
                },
            )

            # List available files for debugging
            if week_folder.exists():
                docx_files = list(week_folder.glob("*.docx"))
                file_names = [f.name for f in docx_files[:10]]
                print(
                    f"DEBUG: Found {len(docx_files)} DOCX files in week folder: {file_names}"
                )
                logger.debug(
                    "primary_file_candidates",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "candidate_count": len(docx_files),
                        "candidates": file_names,
                    },
                )

            file_mgr = get_file_manager(base_path=user_base_path)

            # Try pattern first
            patterns_to_try = []
            if teacher_pattern:
                patterns_to_try.append(teacher_pattern)

            # If pattern doesn't match and we have last_name, try that
            if last_name and last_name not in (patterns_to_try or []):
                patterns_to_try.append(last_name)

            # Also try full name if available
            if primary_name and primary_name not in patterns_to_try:
                patterns_to_try.append(primary_name)
            elif (
                first_name and last_name
            ) and f"{first_name} {last_name}".strip() not in patterns_to_try:
                patterns_to_try.append(f"{first_name} {last_name}".strip())

            found = None
            for pattern in patterns_to_try:
                print(
                    f"DEBUG: Trying pattern '{pattern}' for subject '{slot['subject']}'"
                )
                found = file_mgr.find_primary_teacher_file(
                    week_folder, pattern, slot["subject"]
                )
                if found:
                    print(
                        f"DEBUG: Found primary file using pattern '{pattern}': {found}"
                    )
                    logger.debug(
                        "primary_file_resolve_pattern_success",
                        extra={
                            "slot_number": slot.get("slot_number"),
                            "pattern": pattern,
                            "path": found,
                        },
                    )
                    return found

            # None of the patterns matched
            print(f"DEBUG: None of the patterns matched: {patterns_to_try}")
            # List all files that weren't skipped for debugging
            all_files = list(week_folder.glob("*.docx"))
            skipped_files = [
                f.name for f in all_files if file_mgr._should_skip_file(f.name)
            ]
            available_files = [
                f.name for f in all_files if not file_mgr._should_skip_file(f.name)
            ]
            print(f"DEBUG: Available files (not skipped): {available_files}")
            if skipped_files:
                print(f"DEBUG: Skipped files: {skipped_files}")
            logger.debug(
                "primary_file_resolve_pattern_failed",
                extra={
                    "slot_number": slot.get("slot_number"),
                    "patterns_tried": patterns_to_try,
                    "available_files": available_files,
                    "skipped_files": skipped_files,
                },
            )
        else:
            if not teacher_pattern:
                print(
                    f"DEBUG: Slot {slot.get('slot_number')} has no teacher pattern or name configured"
                )
                print(
                    f"DEBUG: primary_teacher_file_pattern: {slot.get('primary_teacher_file_pattern')}"
                )
                print(
                    f"DEBUG: primary_teacher_name: {slot.get('primary_teacher_name')}"
                )
                logger.debug(
                    "primary_file_no_pattern",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "primary_teacher_file_pattern": slot.get(
                            "primary_teacher_file_pattern"
                        ),
                        "primary_teacher_name": slot.get("primary_teacher_name"),
                    },
                )
            if not week_folder.exists():
                print(f"DEBUG: Week folder does not exist: {week_folder}")
                logger.debug(
                    "primary_file_week_folder_missing",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "week_folder": str(week_folder),
                    },
                )

        # Priority 4: Fallback to input/ for testing
        if slot.get("primary_teacher_file"):
            fallback = Path("input") / Path(slot["primary_teacher_file"]).name
            if fallback.exists():
                logger.debug(
                    "primary_file_resolve_fallback",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "path": str(fallback),
                    },
                )
                return str(fallback)

        # Enhanced error logging with all diagnostic info
        print(f"DEBUG: PRIMARY FILE NOT FOUND for slot {slot.get('slot_number')}")
        print(f"DEBUG: Week folder: {week_folder} (exists: {week_folder.exists()})")
        print("DEBUG: Slot config:")
        print(f"  - primary_teacher_file: {slot.get('primary_teacher_file')}")
        print(
            f"  - primary_teacher_file_pattern: {slot.get('primary_teacher_file_pattern')}"
        )
        print(f"  - primary_teacher_name: {slot.get('primary_teacher_name')}")
        print(
            f"  - primary_teacher_first_name: {slot.get('primary_teacher_first_name')}"
        )
        print(f"  - primary_teacher_last_name: {slot.get('primary_teacher_last_name')}")
        print(f"  - subject: {slot.get('subject')}")

        if week_folder.exists():
            docx_files = list(week_folder.glob("*.docx"))
            print(f"DEBUG: Available files in week folder ({len(docx_files)} total):")
            for f in docx_files[:20]:
                print(f"  - {f.name}")

        logger.warning(
            "primary_file_not_found",
            extra={
                "slot_number": slot.get("slot_number"),
                "week_folder": str(week_folder),
                "week_folder_exists": week_folder.exists(),
                "primary_teacher_file": slot.get("primary_teacher_file"),
                "primary_teacher_file_pattern": slot.get(
                    "primary_teacher_file_pattern"
                ),
                "primary_teacher_name": slot.get("primary_teacher_name"),
                "available_files": [
                    f.name for f in list(week_folder.glob("*.docx"))[:20]
                ]
                if week_folder.exists()
                else [],
            },
        )
        return None

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

        Args:
            user: User data
            lessons: List of lesson dicts with slot_number, subject, lesson_json
            week_of: Week date range
            generated_at: Generation timestamp

        Returns:
            Path to output DOCX file
        """
        # Sort lessons by slot number
        lessons.sort(key=lambda x: x["slot_number"])

        logger.info(
            "batch_combining_lessons",
            extra={"lesson_count": len(lessons), "user_id": user["id"]},
        )

        # Track combine lessons operation - wrap the entire method logic
        if plan_id:
            with self.tracker.track_operation(
                plan_id,
                "render_combine_lessons",
                metadata={
                    "slot_count": len(lessons),
                    "consolidated": len(lessons) > 1,
                },
            ):
                return self._combine_lessons_impl(
                    user, lessons, week_of, generated_at, plan_id
                )
        else:
            return self._combine_lessons_impl(
                user, lessons, week_of, generated_at, plan_id
            )

    def _combine_lessons_impl(
        self,
        user: Dict[str, Any],
        lessons: List[Dict[str, Any]],
        week_of: str,
        generated_at: datetime,
        plan_id: Optional[str] = None,
    ) -> str:
        """Internal implementation of _combine_lessons (without tracking wrapper)."""
        from tools.diagnostic_logger import finalize_diagnostics
        from tools.json_merger import (
            get_merge_summary,
            merge_lesson_jsons,
            validate_merged_json,
        )

        def _safe_finalize():
            """Safely finalize diagnostics, never crash."""
            try:
                finalize_diagnostics()
            except Exception:
                logger.warning("diagnostic_finalize_failed", exc_info=True)

        # Merge all lesson JSONs into a single multi-slot structure
        merged_json = merge_lesson_jsons(lessons)

        # Validate merged structure
        is_valid, error_msg = validate_merged_json(merged_json)
        if not is_valid:
            raise ValueError(f"Merged JSON validation failed: {error_msg}")

        # Log merge summary
        logger.debug(
            "batch_merge_summary", extra={"summary": get_merge_summary(merged_json)}
        )

        # Add user info to metadata
        merged_json["metadata"]["user_name"] = user["name"]

        # Get output path using user's base path
        file_mgr = get_file_manager(base_path=user.get("base_path_override"))
        week_folder = file_mgr.get_week_folder(week_of)

        # Determine output filename based on number of slots
        if len(lessons) > 1:
            # Multi-slot: Use consolidated "Weekly" filename with timestamp
            from datetime import datetime

            week_num = self._get_week_num(week_of)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user['name'].replace(' ', '_')}_Weekly_W{week_num:02d}_{week_of.replace('/', '-')}_{timestamp}.docx"
            output_path = str(week_folder / filename)

            # Add consolidated metadata
            merged_json["metadata"]["total_slots"] = len(lessons)

            # Extract unique teachers and subjects
            teachers = set()
            subjects = set()
            for lesson in lessons:
                if (
                    lesson.get("lesson_json", {})
                    .get("metadata", {})
                    .get("teacher_name")
                ):
                    teachers.add(lesson["lesson_json"]["metadata"]["teacher_name"])
                if lesson.get("subject"):
                    subjects.add(lesson["subject"])

            # Update metadata for multi-slot display - join names instead of "Multiple..."
            if len(teachers) > 1:
                merged_json["metadata"]["teacher_name"] = " / ".join(sorted(teachers))
            if len(subjects) > 1:
                merged_json["metadata"]["subject"] = " / ".join(sorted(subjects))
        else:
            # Single slot: Use timestamped filename format to prevent overwrites
            output_path = file_mgr.get_output_path_with_timestamp(
                week_folder, user["name"], week_of
            )

        # Render to DOCX - use user-specific template if available, otherwise default
        template_path = (
            user.get("template_path") or "input/Lesson Plan Template SY'25-26.docx"
        )
        if not Path(template_path).exists():
            logger.warning(
                "user_template_not_found",
                extra={"user_id": user.get("id"), "template_path": template_path},
            )
            # Fallback to default template
            template_path = "input/Lesson Plan Template SY'25-26.docx"
        
        # Verify template exists before creating renderer
        if not Path(template_path).exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}. "
                f"Please ensure the template exists at this path."
            )
            
        renderer = DOCXRenderer(template_path)

        if len(lessons) == 1:
            # Single slot: render directly
            # CRITICAL: Add slot metadata to the lesson JSON before rendering
            lesson = lessons[0]
            slot_num = lesson["slot_number"]
            subject = lesson["subject"]
            lesson_json = lesson["lesson_json"]

            # Ensure lesson_json is a dictionary before using 'in' operator
            if not isinstance(lesson_json, dict):
                if hasattr(lesson_json, "model_dump"):
                    lesson_json = lesson_json.model_dump()
                elif hasattr(lesson_json, "dict"):
                    lesson_json = lesson_json.dict()
                else:
                    lesson_json = dict(lesson_json) if lesson_json else {}

            # Add slot metadata to lesson JSON metadata
            if "metadata" not in lesson_json:
                lesson_json["metadata"] = {}
            lesson_json["metadata"]["slot_number"] = slot_num
            lesson_json["metadata"]["subject"] = subject

            # Add slot metadata to hyperlinks and images
            
            if "_hyperlinks" in lesson_json:
                for link in lesson_json.get("_hyperlinks", []):
                    if isinstance(link, dict):
                        link["_source_slot"] = slot_num
                        link["_source_subject"] = subject

            if "_images" in lesson_json:
                for image in lesson_json.get("_images", []):
                    if isinstance(image, dict):
                        image["_source_slot"] = slot_num
                        image["_source_subject"] = subject

            logger.info(
                "batch_render_single_slot",
                extra={"output_file": Path(output_path).name, "week_of": week_of},
            )

            # DIAGNOSTIC: Log before rendering
            from tools.diagnostic_logger import get_diagnostic_logger

            diag = get_diagnostic_logger()
            diag.log_before_render(slot_num, subject, lesson_json, "single_slot")

            # Verify output directory exists and is writable before rendering
            output_dir = Path(output_path).parent
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                # Test write permissions by creating a temp file
                test_file = output_dir / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception as perm_error:
                    raise PermissionError(
                        f"Cannot write to output directory '{output_dir}': {perm_error}"
                    )
            except Exception as dir_error:
                error_msg = f"Failed to create or access output directory '{output_dir}': {str(dir_error)}"
                print(f"ERROR: {error_msg}")
                traceback.print_exc()
                raise RuntimeError(error_msg) from dir_error
            
            # Pass plan_id for detailed tracking
            try:
                render_success = renderer.render(lesson_json, output_path, plan_id=plan_id)
                if not render_success:
                    raise RuntimeError(f"Renderer returned False - rendering failed silently. Check logs for details.")
            except Exception as e:
                error_msg = f"Renderer failed to generate file '{output_path}': {str(e)}"
                print(f"ERROR: {error_msg}")
                traceback.print_exc()
                raise RuntimeError(error_msg) from e

            if not Path(output_path).exists():
                error_msg = f"Renderer failed to create output file: {output_path}. File does not exist after render() call."
                print(f"ERROR: {error_msg}")
                # Check if parent directory exists
                output_dir = Path(output_path).parent
                if not output_dir.exists():
                    error_msg += f" Parent directory does not exist: {output_dir}"
                else:
                    error_msg += f" Parent directory exists: {output_dir}"
                raise FileNotFoundError(error_msg)

            # Modify the existing signature table in the rendered document
            # (add date and signature image/name)
            try:
                doc = Document(output_path)
            except Exception as e:
                error_msg = f"Failed to open rendered file '{output_path}': {str(e)}"
                print(f"ERROR: {error_msg}")
                traceback.print_exc()
                raise FileNotFoundError(error_msg)
            
            signature_image_path = user.get("signature_image_path")
            if signature_image_path and not signature_image_path.strip():
                signature_image_path = None
            
            try:
                self._modify_existing_signature_table(
                    doc, generated_at, signature_image_path, user.get("name")
                )
                doc.save(output_path)
            except Exception as e:
                error_msg = f"Failed to modify/save document '{output_path}': {str(e)}"
                print(f"ERROR: {error_msg}")
                traceback.print_exc()
                raise

            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix(".json")
            import json

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            logger.info("batch_json_saved", extra={"json_path": str(json_path)})

            # Generate objectives DOCX file
            try:
                from backend.services.objectives_printer import ObjectivesPrinter

                objectives_printer = ObjectivesPrinter()
                objectives_output_path = Path(output_path).with_name(
                    Path(output_path).stem + "_objectives.docx"
                )
                objectives_printer.generate_docx(
                    lesson_json,
                    str(objectives_output_path),
                    user_name=user.get("name"),
                    week_of=week_of,
                )
                logger.info(
                    "batch_objectives_docx_generated",
                    extra={"objectives_path": str(objectives_output_path)},
                )
            except Exception as e:
                logger.warning(
                    "batch_objectives_docx_failed",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                # Don't fail the entire process if objectives generation fails

            # Generate objectives PDF and HTML files
            # Write debug marker to confirm this code is reached
            debug_marker = Path(output_path).parent / f"{Path(output_path).stem}_objectives_debug.txt"
            try:
                with open(debug_marker, "w", encoding="utf-8") as f:
                    f.write(f"Objectives generation started at {datetime.now()}\n")
                    f.write(f"Output path: {output_path}\n")
            except:
                pass  # Don't fail if we can't write debug file
            
            try:
                from backend.services.objectives_pdf_generator import generate_objectives_pdf

                objectives_pdf_path = Path(output_path).with_name(
                    Path(output_path).stem + "_objectives.pdf"
                )
                print(f"DEBUG: Generating objectives PDF at: {objectives_pdf_path}")
                try:
                    with open(debug_marker, "a", encoding="utf-8") as f:
                        f.write(f"PDF path: {objectives_pdf_path}\n")
                        f.write(f"About to call generate_objectives_pdf\n")
                        f.write(f"Sanitizing lesson_json before PDF generation\n")
                except:
                    pass
                
                # CRITICAL: Sanitize lesson_json to remove ModelPrivateAttr objects before PDF generation
                lesson_json_for_pdf = self._sanitize_value(lesson_json)
                
                logger.info(
                    "batch_objectives_pdf_html_starting",
                    extra={"objectives_pdf_path": str(objectives_pdf_path)},
                )
                # Generate PDF with keep_html=True to also create the HTML file
                generate_objectives_pdf(
                    lesson_json_for_pdf,
                    str(objectives_pdf_path),
                    user_name=user.get("name"),
                    keep_html=True,  # Keep HTML file (it will be created with .html extension)
                )
                # The HTML file will be created with the same name but .html extension
                objectives_html_path = objectives_pdf_path.with_suffix(".html")
                
                # Verify files were created
                if not objectives_pdf_path.exists():
                    logger.error(
                        "batch_objectives_pdf_not_created",
                        extra={"expected_path": str(objectives_pdf_path)},
                    )
                if not objectives_html_path.exists():
                    logger.error(
                        "batch_objectives_html_not_created",
                        extra={"expected_path": str(objectives_html_path)},
                    )
                
                print(f"DEBUG: Objectives PDF generated: {objectives_pdf_path.exists()}")
                print(f"DEBUG: Objectives HTML generated: {objectives_html_path.exists()}")
                try:
                    with open(debug_marker, "a", encoding="utf-8") as f:
                        f.write(f"PDF exists: {objectives_pdf_path.exists()}\n")
                        f.write(f"HTML exists: {objectives_html_path.exists()}\n")
                except:
                    pass
                logger.info(
                    "batch_objectives_pdf_html_generated",
                    extra={
                        "objectives_pdf_path": str(objectives_pdf_path),
                        "objectives_html_path": str(objectives_html_path),
                        "pdf_exists": objectives_pdf_path.exists(),
                        "html_exists": objectives_html_path.exists(),
                    },
                )

                # Generate sentence frames PDF/HTML for the same lesson JSON
                try:
                    print("DEBUG: Attempting to import sentence_frames_pdf_generator")
                    from backend.services.sentence_frames_pdf_generator import generate_sentence_frames_pdf
                    print("DEBUG: Successfully imported sentence_frames_pdf_generator")

                    # Use the same directory as the output_path to ensure files are in the correct folder
                    output_dir = Path(output_path).parent
                    output_stem = Path(output_path).stem
                    sentence_frames_pdf_path = output_dir / f"{output_stem}_sentence_frames.pdf"

                    logger.info(
                        "batch_sentence_frames_pdf_html_starting",
                        extra={
                            "sentence_frames_pdf_path": str(sentence_frames_pdf_path),
                            "output_path": str(output_path),
                            "output_dir": str(output_dir),
                        },
                    )
                    
                    print(f"DEBUG: Output path: {output_path}")
                    print(f"DEBUG: Output directory: {output_dir}")
                    print(f"DEBUG: Sentence frames PDF path: {sentence_frames_pdf_path}")
                    
                    # Check if sentence_frames exist in the data
                    # Use the original lesson_json, not the sanitized one, to ensure we don't miss frames
                    has_frames = False
                    frames_count = 0
                    if "days" in lesson_json:
                        for day_name, day in lesson_json["days"].items():
                            if not isinstance(day, dict):
                                continue
                            # Check day-level frames
                            day_frames = day.get("sentence_frames")
                            if day_frames and isinstance(day_frames, list) and len(day_frames) > 0:
                                has_frames = True
                                frames_count += len(day_frames)
                            # Check slot-level frames
                            slots = day.get("slots", [])
                            if isinstance(slots, list):
                                for slot in slots:
                                    if not isinstance(slot, dict):
                                        continue
                                    slot_frames = slot.get("sentence_frames")
                                    if slot_frames and isinstance(slot_frames, list) and len(slot_frames) > 0:
                                        has_frames = True
                                        frames_count += len(slot_frames)
                    
                    print(f"DEBUG: lesson_json has sentence_frames: {has_frames} (count: {frames_count})")
                    
                    # Also check the sanitized version as a fallback
                    if not has_frames and "days" in lesson_json_for_pdf:
                        for day in lesson_json_for_pdf["days"].values():
                            if not isinstance(day, dict):
                                continue
                            if "sentence_frames" in day and day["sentence_frames"]:
                                has_frames = True
                                frames_count += len(day.get("sentence_frames", []))
                                break
                            if "slots" in day:
                                for s in day["slots"]:
                                    if not isinstance(s, dict):
                                        continue
                                    if "sentence_frames" in s and s["sentence_frames"]:
                                        has_frames = True
                                        frames_count += len(s.get("sentence_frames", []))
                                        break
                        print(f"DEBUG: After checking sanitized version, has_frames: {has_frames} (count: {frames_count})")

                    if has_frames:
                        # Ensure output directory exists
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Use the sanitized version for generation to avoid ModelPrivateAttr issues
                        generate_sentence_frames_pdf(
                            lesson_json_for_pdf,
                            str(sentence_frames_pdf_path),
                            user_name=user.get("name"),
                            keep_html=True,
                        )
                        
                        # Verify files were created
                        sentence_frames_html_path = sentence_frames_pdf_path.with_suffix(".html")
                        if not sentence_frames_pdf_path.exists():
                            logger.error(
                                "batch_sentence_frames_pdf_not_created",
                                extra={"expected_path": str(sentence_frames_pdf_path)},
                            )
                        if not sentence_frames_html_path.exists():
                            logger.error(
                                "batch_sentence_frames_html_not_created",
                                extra={"expected_path": str(sentence_frames_html_path)},
                            )
                        
                        print(f"DEBUG: Sentence frames PDF generated: {sentence_frames_pdf_path.exists()}")
                        print(f"DEBUG: Sentence frames HTML generated: {sentence_frames_html_path.exists()}")
                        print(f"DEBUG: generate_sentence_frames_pdf completed successfully")
                        logger.info(
                            "batch_sentence_frames_pdf_generated",
                            extra={
                                "path": str(sentence_frames_pdf_path),
                                "pdf_exists": sentence_frames_pdf_path.exists(),
                                "html_exists": sentence_frames_html_path.exists(),
                                "frames_count": frames_count,
                            }
                        )
                    else:
                        print("DEBUG: Skipping sentence frames PDF generation (no frames found)")
                        logger.warning(
                            "batch_sentence_frames_skipped_no_data",
                            extra={
                                "plan_id": plan_id,
                                "output_path": str(output_path),
                                "has_days": "days" in lesson_json,
                            }
                        )
                except ImportError as ie:
                    print(f"ERROR: Could not import sentence_frames_pdf_generator: {ie}")
                    logger.error(
                        "batch_sentence_frames_import_failed",
                        extra={"error": str(ie)}
                    )
                except Exception as e:
                    print(f"ERROR: Failed to generate sentence frames PDF: {e}")
                    traceback.print_exc()
                    logger.warning(
                        "batch_sentence_frames_pdf_html_failed",
                        extra={"error": str(e), "error_type": type(e).__name__},
                        exc_info=True,
                    )
            except Exception as e:
                error_msg = f"Failed to generate objectives PDF/HTML: {str(e)}"
                print(f"ERROR: {error_msg}")
                try:
                    with open(debug_marker, "a", encoding="utf-8") as f:
                        f.write(f"ERROR: {error_msg}\n")
                        f.write(f"Error type: {type(e).__name__}\n")
                        try:
                            f.write(f"Traceback:\n{traceback.format_exc()}\n")
                        except:
                            f.write("Traceback: (unavailable)\n")
                except Exception as debug_err:
                    # If we can't write to debug file, just log it
                    print(f"WARNING: Could not write to debug file: {debug_err}")
                    pass
                logger.warning(
                    "batch_objectives_pdf_html_failed",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                try:
                    traceback.print_exc()
                except:
                    print(f"Could not print traceback: {e}")
                # Don't fail the entire process if PDF/HTML generation fails

            logger.info(
                "batch_render_single_slot_success", extra={"output_path": output_path}
            )
            _safe_finalize()
            return output_path
        else:
            # Multi-slot: render each slot separately to preserve 2-table structure
            # Then merge DOCX files
            logger.info(
                "batch_render_multi_slot_start",
                extra={
                    "lesson_count": len(lessons),
                    "output_file": Path(output_path).name,
                },
            )

            temp_files = []
            week_folder = file_mgr.get_week_folder(week_of)

            # Render each slot to temporary file
            # Add slot metadata to hyperlinks/images BEFORE rendering for proper filtering
            for lesson in lessons:
                slot_num = lesson["slot_number"]
                subject = lesson["subject"]
                lesson_json = lesson["lesson_json"]

                # CRITICAL: Add slot metadata to lesson JSON metadata
                # The renderer will extract this to enable strict filtering
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
                lesson_json["metadata"]["slot_number"] = slot_num
                lesson_json["metadata"]["subject"] = subject

                # Also add slot metadata to hyperlinks and images
                # This enables the renderer's strict filtering to work correctly
                if "_hyperlinks" in lesson_json:
                    for link in lesson_json.get("_hyperlinks", []):
                        if isinstance(link, dict):
                            link["_source_slot"] = slot_num
                            link["_source_subject"] = subject

                if "_images" in lesson_json:
                    for image in lesson_json.get("_images", []):
                        if isinstance(image, dict):
                            image["_source_slot"] = slot_num
                            image["_source_subject"] = subject

                # Create temp filename
                temp_filename = f"_temp_slot{slot_num}_{subject.replace('/', '_')}.docx"
                temp_path = str(week_folder / temp_filename)

                logger.debug(
                    "batch_render_slot",
                    extra={
                        "slot_number": slot_num,
                        "subject": subject,
                        "hyperlinks": len(lesson_json.get("_hyperlinks", [])),
                        "images": len(lesson_json.get("_images", [])),
                    },
                )

                # DIAGNOSTIC: Log before rendering
                from tools.diagnostic_logger import get_diagnostic_logger

                diag = get_diagnostic_logger()
                diag.log_before_render(slot_num, subject, lesson_json, "multi_slot")

                # Render this slot (will have 2 tables: original + bilingual)
                # Pass plan_id for detailed tracking
                renderer.render(lesson_json, temp_path, plan_id=plan_id)
                temp_files.append(temp_path)

            # Merge all temp files into one consolidated DOCX
            logger.info(
                "batch_merge_slots",
                extra={"slot_count": len(temp_files), "output_file": output_path},
            )
            try:
                # Track file merging operation
                if plan_id:
                    with self.tracker.track_operation(
                        plan_id,
                        "render_merge_files",
                        metadata={"file_count": len(temp_files)},
                    ):
                        self._merge_docx_files(temp_files, output_path)
                else:
                    self._merge_docx_files(temp_files, output_path)
                logger.info(
                    "batch_merge_slots_success", extra={"slot_count": len(temp_files)}
                )
            except Exception as e:
                logger.exception("batch_merge_slots_error", extra={"error": str(e)})
                raise

            # Remove all signature boxes from merged document, then add one at the end
            logger.debug("batch_clean_signature_boxes")
            doc = Document(output_path)
            # Track signature operations
            # Use user-specific signature image if available (optional - only if path is provided)
            signature_image_path = user.get("signature_image_path")
            # Only use signature image if path is provided and not empty
            if signature_image_path and not signature_image_path.strip():
                signature_image_path = None
            if plan_id:
                with self.tracker.track_operation(plan_id, "render_remove_signatures"):
                    self._remove_signature_boxes(doc)
                with self.tracker.track_operation(plan_id, "render_add_signature"):
                    self._add_signature_box(
                        doc,
                        generated_at,
                        template_path,
                        signature_image_path,
                        user.get("name"),
                    )
                doc.save(output_path)
            else:
                self._remove_signature_boxes(doc)
                self._add_signature_box(
                    doc,
                    generated_at,
                    template_path,
                    signature_image_path,
                    user.get("name"),
                )
                doc.save(output_path)

            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix(".json")
            import json

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(merged_json, f, indent=2, ensure_ascii=False)
            logger.info("batch_json_saved", extra={"json_path": str(json_path)})

            # Generate objectives DOCX file
            try:
                from backend.services.objectives_printer import ObjectivesPrinter

                objectives_printer = ObjectivesPrinter()
                objectives_output_path = Path(output_path).with_name(
                    Path(output_path).stem + "_objectives.docx"
                )
                objectives_printer.generate_docx(
                    merged_json,
                    str(objectives_output_path),
                    user_name=user.get("name"),
                    week_of=week_of,
                )
                logger.info(
                    "batch_objectives_docx_generated",
                    extra={"objectives_path": str(objectives_output_path)},
                )
            except Exception as e:
                logger.warning(
                    "batch_objectives_docx_failed",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                # Don't fail the entire process if objectives generation fails

            # Generate objectives PDF and HTML files
            try:
                from backend.services.objectives_pdf_generator import generate_objectives_pdf

                objectives_pdf_path = Path(output_path).with_name(
                    Path(output_path).stem + "_objectives.pdf"
                )
                print(f"DEBUG: Generating objectives PDF at: {objectives_pdf_path}")
                
                # CRITICAL: Sanitize merged_json to remove ModelPrivateAttr objects before PDF generation
                merged_json_for_pdf = self._sanitize_value(merged_json)
                
                logger.info(
                    "batch_objectives_pdf_html_starting",
                    extra={"objectives_pdf_path": str(objectives_pdf_path)},
                )
                # Generate PDF with keep_html=True to also create the HTML file
                generate_objectives_pdf(
                    merged_json_for_pdf,
                    str(objectives_pdf_path),
                    user_name=user.get("name"),
                    keep_html=True,  # Keep HTML file (it will be created with .html extension)
                )
                # The HTML file will be created with the same name but .html extension
                objectives_html_path = objectives_pdf_path.with_suffix(".html")
                
                # Verify files were created
                if not objectives_pdf_path.exists():
                    logger.error(
                        "batch_objectives_pdf_not_created",
                        extra={"expected_path": str(objectives_pdf_path)},
                    )
                if not objectives_html_path.exists():
                    logger.error(
                        "batch_objectives_html_not_created",
                        extra={"expected_path": str(objectives_html_path)},
                    )
                
                print(f"DEBUG: Objectives PDF generated: {objectives_pdf_path.exists()}")
                print(f"DEBUG: Objectives HTML generated: {objectives_html_path.exists()}")
                logger.info(
                    "batch_objectives_pdf_html_generated",
                    extra={
                        "objectives_pdf_path": str(objectives_pdf_path),
                        "objectives_html_path": str(objectives_html_path),
                        "pdf_exists": objectives_pdf_path.exists(),
                        "html_exists": objectives_html_path.exists(),
                    },
                )
            except Exception as e:
                error_msg = f"Failed to generate objectives PDF/HTML: {str(e)}"
                print(f"ERROR: {error_msg}")
                logger.warning(
                    "batch_objectives_pdf_html_failed",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                try:
                    traceback.print_exc()
                except:
                    print(f"Could not print traceback: {e}")
                # Don't fail the entire process if PDF/HTML generation fails

            # Generate sentence frames PDF/HTML for multi-slot plans
            try:
                print("DEBUG: Attempting to import sentence_frames_pdf_generator for multi-slot")
                from backend.services.sentence_frames_pdf_generator import generate_sentence_frames_pdf
                print("DEBUG: Successfully imported sentence_frames_pdf_generator")

                # Use the same directory as the output_path to ensure files are in the correct folder
                output_dir = Path(output_path).parent
                output_stem = Path(output_path).stem
                sentence_frames_pdf_path = output_dir / f"{output_stem}_sentence_frames.pdf"

                logger.info(
                    "batch_sentence_frames_pdf_html_starting",
                    extra={
                        "sentence_frames_pdf_path": str(sentence_frames_pdf_path),
                        "output_path": str(output_path),
                        "output_dir": str(output_dir),
                        "multi_slot": True,
                    },
                )
                
                print(f"DEBUG: Output path: {output_path}")
                print(f"DEBUG: Output directory: {output_dir}")
                print(f"DEBUG: Sentence frames PDF path: {sentence_frames_pdf_path}")
                
                # Check if sentence_frames exist in the merged JSON
                has_frames = False
                frames_count = 0
                if "days" in merged_json:
                    for day_name, day in merged_json["days"].items():
                        if not isinstance(day, dict):
                            continue
                        # Check day-level frames
                        day_frames = day.get("sentence_frames")
                        if day_frames and isinstance(day_frames, list) and len(day_frames) > 0:
                            has_frames = True
                            frames_count += len(day_frames)
                        # Check slot-level frames
                        slots = day.get("slots", [])
                        if isinstance(slots, list):
                            for slot in slots:
                                if not isinstance(slot, dict):
                                    continue
                                slot_frames = slot.get("sentence_frames")
                                if slot_frames and isinstance(slot_frames, list) and len(slot_frames) > 0:
                                    has_frames = True
                                    frames_count += len(slot_frames)
                
                print(f"DEBUG: merged_json has sentence_frames: {has_frames} (count: {frames_count})")
                
                # Also check the sanitized version as a fallback
                if not has_frames and "days" in merged_json_for_pdf:
                    for day in merged_json_for_pdf["days"].values():
                        if not isinstance(day, dict):
                            continue
                        if "sentence_frames" in day and day["sentence_frames"]:
                            has_frames = True
                            frames_count += len(day.get("sentence_frames", []))
                            break
                        if "slots" in day:
                            for s in day["slots"]:
                                if not isinstance(s, dict):
                                    continue
                                if "sentence_frames" in s and s["sentence_frames"]:
                                    has_frames = True
                                    frames_count += len(s.get("sentence_frames", []))
                                    break
                    print(f"DEBUG: After checking sanitized version, has_frames: {has_frames} (count: {frames_count})")

                if has_frames:
                    # Ensure output directory exists
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Use the sanitized version for generation to avoid ModelPrivateAttr issues
                    generate_sentence_frames_pdf(
                        merged_json_for_pdf,
                        str(sentence_frames_pdf_path),
                        user_name=user.get("name"),
                        keep_html=True,
                    )
                    
                    # Verify files were created
                    sentence_frames_html_path = sentence_frames_pdf_path.with_suffix(".html")
                    if not sentence_frames_pdf_path.exists():
                        logger.error(
                            "batch_sentence_frames_pdf_not_created",
                            extra={"expected_path": str(sentence_frames_pdf_path)},
                        )
                    if not sentence_frames_html_path.exists():
                        logger.error(
                            "batch_sentence_frames_html_not_created",
                            extra={"expected_path": str(sentence_frames_html_path)},
                        )
                    
                    print(f"DEBUG: Sentence frames PDF generated: {sentence_frames_pdf_path.exists()}")
                    print(f"DEBUG: Sentence frames HTML generated: {sentence_frames_html_path.exists()}")
                    print(f"DEBUG: generate_sentence_frames_pdf completed successfully for multi-slot")
                    logger.info(
                        "batch_sentence_frames_pdf_generated",
                        extra={
                            "path": str(sentence_frames_pdf_path),
                            "pdf_exists": sentence_frames_pdf_path.exists(),
                            "html_exists": sentence_frames_html_path.exists(),
                            "frames_count": frames_count,
                            "multi_slot": True,
                        }
                    )
                else:
                    print("DEBUG: Skipping sentence frames PDF generation (no frames found in merged JSON)")
                    logger.warning(
                        "batch_sentence_frames_skipped_no_data",
                        extra={
                            "plan_id": plan_id,
                            "output_path": str(output_path),
                            "has_days": "days" in merged_json,
                            "multi_slot": True,
                        }
                    )
            except ImportError as ie:
                print(f"ERROR: Could not import sentence_frames_pdf_generator: {ie}")
                logger.error(
                    "batch_sentence_frames_import_failed",
                    extra={"error": str(ie), "multi_slot": True}
                )
            except Exception as e:
                print(f"ERROR: Failed to generate sentence frames PDF for multi-slot: {e}")
                traceback.print_exc()
                logger.warning(
                    "batch_sentence_frames_pdf_html_failed",
                    extra={"error": str(e), "error_type": type(e).__name__, "multi_slot": True},
                    exc_info=True,
                )

            # Clean up temp files - ensure they're deleted even if there's an error
            for temp_file in temp_files:
                try:
                    temp_path = Path(temp_file)
                    if temp_path.exists():
                        temp_path.unlink()
                        logger.debug(
                            "batch_temp_file_deleted", extra={"temp_file": temp_file}
                        )
                except Exception as e:
                    logger.warning(
                        "batch_temp_cleanup_failed",
                        extra={"temp_file": temp_file, "error": str(e)},
                    )

            logger.info(
                "batch_render_multi_slot_success",
                extra={"lesson_count": len(lessons), "output_path": output_path},
            )
            _safe_finalize()
            return output_path

    def _merge_docx_files(self, file_paths: List[str], output_path: str):
        """
        Merge multiple DOCX files into one using docxcompose.
        Each document is separated by a page break.

        Args:
            file_paths: List of DOCX file paths to merge
            output_path: Path for merged output file
        """
        from docx import Document
        from docxcompose.composer import Composer

        if not file_paths:
            raise ValueError("No files to merge")

        logger.debug("batch_merge_docx_start", extra={"file_count": len(file_paths)})
        for i, fp in enumerate(file_paths, 1):
            logger.debug(
                "batch_merge_docx_file", extra={"index": i, "file_name": Path(fp).name}
            )

        # Load the first document as the base
        master = Document(file_paths[0])
        composer = Composer(master)

        # Append all other documents with explicit page breaks
        for i, file_path in enumerate(file_paths[1:], 2):
            logger.debug(
                "batch_merge_docx_append",
                extra={"index": i, "file_name": Path(file_path).name},
            )
            doc = Document(file_path)

            # CRITICAL: Add page break at the beginning of each document being appended
            # This ensures each slot pair (metadata + daily plans) starts on a new page
            # Create page break paragraph and insert it at the beginning
            page_break_para = doc.add_page_break()

            # Move the page break paragraph to the beginning of the document
            # Remove it from its current position and insert at index 0
            para_element = page_break_para._element
            para_element.getparent().remove(para_element)
            doc._element.body.insert(0, para_element)

            composer.append(doc)

        # Save the merged document
        logger.debug(
            "batch_merge_docx_save", extra={"output_file": Path(output_path).name}
        )
        composer.save(output_path)

    def _get_week_num(self, week_of: str) -> int:
        """Extract week number from week_of string.

        Supports formats:
        - MM/DD-MM/DD (e.g., 10/13-10/17)
        - MM-DD-MM-DD (e.g., 10-13-10-17)
        """
        try:
            from datetime import datetime

            # Normalize format: convert all hyphens to slashes first, then split
            # Handle both "10/13-10/17" and "10-13-10-17" formats
            if "/" in week_of:
                # Format: MM/DD-MM/DD
                first_date = week_of.split("-")[0].strip()
                month, day = map(int, first_date.split("/"))
            else:
                # Format: MM-DD-MM-DD (all hyphens)
                parts = week_of.split("-")
                if len(parts) >= 2:
                    month, day = int(parts[0]), int(parts[1])
                else:
                    raise ValueError(f"Invalid week_of format: {week_of}")

            year = datetime.now().year
            date_obj = datetime(year, month, day)
            week_num = date_obj.isocalendar()[1]
            logger.debug(
                "week_number_calculated",
                extra={
                    "week_of": week_of,
                    "month": month,
                    "day": day,
                    "year": year,
                    "week_number": week_num,
                },
            )
            return week_num
        except Exception as e:
            logger.warning(
                "week_number_calculation_failed",
                extra={"week_of": week_of, "error": str(e)},
            )
            return 1

    def _remove_signature_boxes(self, doc: Document):
        """Remove signature boxes/tables from document.

        Args:
            doc: Document to remove signatures from
        """
        # Find and remove tables containing signature text
        tables_to_remove = []
        for table in doc.tables:
            # Check if table contains signature-related text
            table_text = "\n".join(
                [cell.text for row in table.rows for cell in row.cells]
            )
            if any(
                keyword in table_text
                for keyword in [
                    "Required Signatures",
                    "Teacher Signature:",
                    "Administrator Signature:",
                    "Administrative Feedback:",
                    "I certify that these lessons",
                ]
            ):
                tables_to_remove.append(table)

        # Remove the signature tables
        for table in tables_to_remove:
            tbl_element = table._element
            tbl_element.getparent().remove(tbl_element)

        # Also remove paragraphs containing signature text
        paragraphs_to_remove = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text.startswith("Signature:") or text.startswith("Date:"):
                paragraphs_to_remove.append(para)

        # Remove the paragraphs
        for para in paragraphs_to_remove:
            p_element = para._element
            p_element.getparent().remove(p_element)

    def _modify_existing_signature_table(
        self,
        doc: Document,
        date: datetime,
        signature_image_path: str = None,
        user_name: str = None,
    ):
        """Modify existing signature table in document (for single-slot documents).

        Args:
            doc: Document containing the signature table
            date: Date to display
            signature_image_path: Optional path to signature image file
            user_name: User's name to use if no signature image is provided
        """
        # Find the signature table in the document
        signature_table = None
        for table in doc.tables:
            table_text = "\n".join(
                [cell.text for row in table.rows for cell in row.cells]
            )
            if "Required Signatures" in table_text:
                signature_table = table
                break

        if not signature_table:
            logger.warning("signature_table_not_found_in_doc")
            return

        # Fill date and add signature/name using the same logic as _add_signature_box
        date_formatted = date.strftime("%m/%d/%Y")

        # Find the cell containing "Teacher Signature:" and update the Date that appears AFTER it
        for row in signature_table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                # Look for cell containing "Teacher Signature:"
                if "Teacher Signature:" in cell_text:
                    # Find the SPECIFIC paragraph that contains "Teacher Signature:" followed by "Date:"
                    # (not the certification paragraph which might have other text)
                    target_para = None
                    for para in cell.paragraphs:
                        para_text = para.text.strip()
                        # Must start with or contain "Teacher Signature:" and have "Date:" after it
                        if "Teacher Signature:" in para_text:
                            teacher_pos = para_text.find("Teacher Signature:")
                            date_pos = (
                                para_text.find("Date:", teacher_pos)
                                if teacher_pos >= 0
                                else -1
                            )
                            # Only select if Date appears AFTER Teacher Signature
                            if date_pos > teacher_pos:
                                target_para = para
                                break

                    if target_para:
                        para = target_para
                        para_text = para.text
                        # Find the "Date:" that appears AFTER "Teacher Signature:" in the paragraph
                        teacher_pos = para_text.find("Teacher Signature:")
                        date_pos = para_text.find(
                            "Date:", teacher_pos
                        )  # Find Date after Teacher Signature

                        if (
                            date_pos > teacher_pos
                        ):  # Date appears after Teacher Signature
                            # Find the run containing this Date (the one after Teacher Signature)
                            date_run = None
                            original_font_size = None
                            original_font_name = None

                            # Track position in paragraph to find the right Date run
                            current_pos = 0
                            for run in para.runs:
                                run_text = run.text
                                run_start = current_pos
                                run_end = current_pos + len(run_text)

                                # Check if this run contains the Date we're looking for (after Teacher Signature)
                                if "Date:" in run_text and run_start >= teacher_pos:
                                    # This is the Date run after Teacher Signature
                                    date_run = run
                                    if run.font.size:
                                        original_font_size = run.font.size
                                    if run.font.name:
                                        original_font_name = run.font.name
                                    break

                                current_pos = run_end

                            if date_run:
                                # Update this Date field using TAB STOPS for precise alignment
                                run_text = date_run.text
                                if "Date:" in run_text:
                                    # Clear and rebuild with tab stop
                                    para.clear()

                                    # Add tab stop at 5.5 inches (matches Administrator row)
                                    # This ensures perfect alignment regardless of font metrics
                                    DATE_TAB_POSITION = Inches(5.5)
                                    para.paragraph_format.tab_stops.add_tab_stop(
                                        DATE_TAB_POSITION, WD_TAB_ALIGNMENT.LEFT
                                    )

                                    # Add "Teacher Signature:" label
                                    teacher_run = para.add_run("Teacher Signature: ")
                                    teacher_run.font.bold = True
                                    if original_font_size:
                                        teacher_run.font.size = original_font_size
                                    if original_font_name:
                                        teacher_run.font.name = original_font_name

                                    # Placeholder for signature/name (will be replaced by _add_signature_image_to_table or _add_user_name_to_table)
                                    placeholder_run = para.add_run("_" * 49)
                                    if original_font_size:
                                        placeholder_run.font.size = original_font_size
                                    if original_font_name:
                                        placeholder_run.font.name = original_font_name

                                    # Add TAB character to jump to tab stop position
                                    para.add_run("\t")

                                    # Add Date label and value
                                    date_label_run = para.add_run("Date: ")
                                    date_label_run.font.bold = True
                                    if original_font_size:
                                        date_label_run.font.size = original_font_size
                                    if original_font_name:
                                        date_label_run.font.name = original_font_name

                                    date_value_run = para.add_run(date_formatted)
                                    date_value_run.font.underline = True
                                    if original_font_size:
                                        date_value_run.font.size = original_font_size
                                    if original_font_name:
                                        date_value_run.font.name = original_font_name

                                    logger.info("signature_date_updated_with_tab_stop")
                                break
                    break

        # Add signature image or user name
        if (
            signature_image_path
            and signature_image_path.strip()
            and Path(signature_image_path).exists()
        ):
            self._add_signature_image_to_table(signature_table, signature_image_path)
        elif user_name:
            self._add_user_name_to_table(signature_table, user_name)

    def _add_signature_image_to_table(self, table, signature_image_path: str):
        """Add signature image to the signature table."""
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if "Teacher Signature:" in cell_text:
                    for para in cell.paragraphs:
                        # Re-read paragraph text to get current state (may have been modified by date insertion)
                        para_text = para.text
                        if "Teacher Signature:" in para_text:
                            # Get font size for image sizing
                            text_font_size = Pt(11)
                            for run in para.runs:
                                if run.font.size:
                                    text_font_size = run.font.size
                                    break

                            text_height_inches = text_font_size.pt / 72.0
                            image_height_inches = text_height_inches * 1.4

                            # Find the position of "Teacher Signature:" and "Date:" in the CURRENT paragraph
                            teacher_pos = para_text.find("Teacher Signature:")
                            date_pos = (
                                para_text.find("Date:", teacher_pos)
                                if teacher_pos >= 0
                                else -1
                            )

                            if teacher_pos >= 0 and date_pos > teacher_pos:
                                try:
                                    # Get text before "Teacher Signature:"
                                    before_teacher = para_text[:teacher_pos]

                                    # Get text between "Teacher Signature:" and "Date:"
                                    # This is where we'll insert the image
                                    between_text = para_text[
                                        teacher_pos
                                        + len("Teacher Signature:") : date_pos
                                    ].strip()
                                    # Remove underscores that are placeholders
                                    between_text = between_text.lstrip("_").strip()

                                    # Check if date was already updated (look for formatted date in paragraph)
                                    date_updated = False
                                    date_value = None
                                    # Look for date pattern MM/DD/YYYY in the paragraph after "Date:"
                                    import re

                                    date_pattern = r"Date:\s*(\d{1,2}/\d{1,2}/\d{4})"
                                    date_match = re.search(date_pattern, para_text)
                                    if date_match:
                                        date_updated = True
                                        date_value = date_match.group(1)

                                    # Get text after "Date:" (not needed - we rebuild the paragraph)
                                    # Removed unused after_date variable

                                    # Save font properties
                                    original_font_size = None
                                    original_font_name = None
                                    for run in para.runs:
                                        if run.font.size:
                                            original_font_size = run.font.size
                                        if run.font.name:
                                            original_font_name = run.font.name
                                        if original_font_size and original_font_name:
                                            break

                                    # Rebuild the paragraph
                                    para.clear()

                                    # Add text before "Teacher Signature:"
                                    if before_teacher.strip():
                                        before_run = para.add_run(before_teacher)
                                        if original_font_size:
                                            before_run.font.size = original_font_size
                                        if original_font_name:
                                            before_run.font.name = original_font_name

                                    # Add "Teacher Signature:" label (bold)
                                    teacher_run = para.add_run("Teacher Signature: ")
                                    teacher_run.font.bold = True
                                    if original_font_size:
                                        teacher_run.font.size = original_font_size
                                    if original_font_name:
                                        teacher_run.font.name = original_font_name

                                    # Add the signature image
                                    image_run = para.add_run()
                                    try:
                                        if not Path(signature_image_path).exists():
                                            logger.error(
                                                "signature_image_file_not_found",
                                                extra={"path": signature_image_path},
                                            )
                                            raise FileNotFoundError(
                                                f"Signature image not found: {signature_image_path}"
                                            )

                                        with open(
                                            signature_image_path, "rb"
                                        ) as img_file:
                                            img_stream = BytesIO(img_file.read())
                                            image_run.add_picture(
                                                img_stream,
                                                height=Inches(image_height_inches),
                                            )

                                        # Verify image was added
                                        if not image_run._element.xpath(".//a:blip"):
                                            logger.error(
                                                "signature_image_not_inserted",
                                                extra={"path": signature_image_path},
                                            )
                                    except Exception as img_error:
                                        logger.error(
                                            "signature_image_insertion_error",
                                            extra={
                                                "path": signature_image_path,
                                                "error": str(img_error),
                                            },
                                        )
                                        import traceback

                                        logger.debug(
                                            "signature_image_error_traceback",
                                            extra={"traceback": traceback.format_exc()},
                                        )
                                        # Don't re-raise - continue without image

                                    # Add any text between signature and date (should be minimal/empty)
                                    if between_text:
                                        between_run = para.add_run(between_text)
                                        if original_font_size:
                                            between_run.font.size = original_font_size
                                        if original_font_name:
                                            between_run.font.name = original_font_name

                                    # Use TAB STOP for precise alignment (same as Administrator row)
                                    # Add tab stop at 5.5 inches
                                    DATE_TAB_POSITION = Inches(5.5)
                                    para.paragraph_format.tab_stops.add_tab_stop(
                                        DATE_TAB_POSITION, WD_TAB_ALIGNMENT.LEFT
                                    )

                                    # Add TAB character to jump to tab stop position
                                    para.add_run("\t")

                                    # Add Date label and value (preserve if already updated, otherwise add placeholder)
                                    # Date label should be bold
                                    date_label_run = para.add_run("Date: ")
                                    date_label_run.font.bold = True
                                    if original_font_size:
                                        date_label_run.font.size = original_font_size
                                    if original_font_name:
                                        date_label_run.font.name = original_font_name

                                    if date_updated and date_value:
                                        # Date was already updated, preserve it with underline
                                        date_value_run = para.add_run(date_value)
                                        date_value_run.font.underline = True
                                        if original_font_size:
                                            date_value_run.font.size = (
                                                original_font_size
                                            )
                                        if original_font_name:
                                            date_value_run.font.name = (
                                                original_font_name
                                            )
                                    else:
                                        # Date not updated yet, add placeholder
                                        date_placeholder_run = para.add_run(
                                            "__________________"
                                        )
                                        if original_font_size:
                                            date_placeholder_run.font.size = (
                                                original_font_size
                                            )
                                        if original_font_name:
                                            date_placeholder_run.font.name = (
                                                original_font_name
                                            )

                                    logger.info(
                                        "signature_image_added",
                                        extra={"path": signature_image_path},
                                    )
                                    # Verify the result
                                    final_text = para.text
                                    if "Teacher Signature:" not in final_text:
                                        logger.error(
                                            "signature_text_missing_after_insertion",
                                            extra={
                                                "path": signature_image_path,
                                                "final_text": final_text,
                                            },
                                        )
                                except Exception as e:
                                    logger.warning(
                                        "signature_image_failed",
                                        extra={
                                            "path": signature_image_path,
                                            "error": str(e),
                                        },
                                    )
                                    import traceback

                                    logger.debug(
                                        "signature_image_traceback",
                                        extra={"traceback": traceback.format_exc()},
                                    )
                                break  # Break from paragraph loop after processing
                    break  # Break from cell loop after finding Teacher Signature

    def _add_user_name_to_table(self, table, user_name: str):
        """Add user name (underlined) to the signature table."""
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if "Teacher Signature:" in cell_text:
                    for para in cell.paragraphs:
                        # Re-read paragraph text to get current state (may have been modified by date insertion)
                        para_text = para.text
                        if "Teacher Signature:" in para_text:
                            # Find the position of "Teacher Signature:" and "Date:" in the CURRENT paragraph
                            teacher_pos = para_text.find("Teacher Signature:")
                            date_pos = (
                                para_text.find("Date:", teacher_pos)
                                if teacher_pos >= 0
                                else -1
                            )

                            if teacher_pos >= 0 and date_pos > teacher_pos:
                                # Get text before "Teacher Signature:"
                                before_teacher = para_text[:teacher_pos]

                                # Get text between "Teacher Signature:" and "Date:"
                                between_text = para_text[
                                    teacher_pos + len("Teacher Signature:") : date_pos
                                ].strip()
                                between_text = between_text.lstrip("_").strip()

                                # Check if date was already updated (look for formatted date in paragraph)
                                date_updated = False
                                date_value = None
                                import re

                                date_pattern = r"Date:\s*(\d{1,2}/\d{1,2}/\d{4})"
                                date_match = re.search(date_pattern, para_text)
                                if date_match:
                                    date_updated = True
                                    date_value = date_match.group(1)

                                # Get text after "Date:" (not needed - we rebuild the paragraph)
                                # Removed unused after_date variable

                                # Save font properties
                                original_font_size = None
                                original_font_name = None
                                for run in para.runs:
                                    if run.font.size:
                                        original_font_size = run.font.size
                                    if run.font.name:
                                        original_font_name = run.font.name
                                    if original_font_size and original_font_name:
                                        break

                                # Rebuild the paragraph
                                para.clear()

                                # Add text before "Teacher Signature:"
                                if before_teacher.strip():
                                    before_run = para.add_run(before_teacher)
                                    if original_font_size:
                                        before_run.font.size = original_font_size
                                    if original_font_name:
                                        before_run.font.name = original_font_name

                                # Add "Teacher Signature:" label (bold)
                                teacher_run = para.add_run("Teacher Signature: ")
                                teacher_run.font.bold = True
                                if original_font_size:
                                    teacher_run.font.size = original_font_size
                                if original_font_name:
                                    teacher_run.font.name = original_font_name

                                # Add user's name underlined
                                name_run = para.add_run(user_name)
                                name_run.font.underline = True
                                if original_font_size:
                                    name_run.font.size = original_font_size
                                if original_font_name:
                                    name_run.font.name = original_font_name

                                # Add any text between signature and date
                                if between_text:
                                    between_run = para.add_run(between_text)
                                    if original_font_size:
                                        between_run.font.size = original_font_size
                                    if original_font_name:
                                        between_run.font.name = original_font_name

                                # Use TAB STOP for precise alignment (same as Administrator row)
                                # Add tab stop at 5.5 inches
                                DATE_TAB_POSITION = Inches(5.5)
                                para.paragraph_format.tab_stops.add_tab_stop(
                                    DATE_TAB_POSITION, WD_TAB_ALIGNMENT.LEFT
                                )

                                # Add TAB character to jump to tab stop position
                                para.add_run("\t")

                                # Add Date label and value (preserve if already updated, otherwise add placeholder)
                                # Date label should be bold
                                date_label_run = para.add_run("Date: ")
                                date_label_run.font.bold = True
                                if original_font_size:
                                    date_label_run.font.size = original_font_size
                                if original_font_name:
                                    date_label_run.font.name = original_font_name

                                if date_updated and date_value:
                                    # Date was already updated, preserve it with underline
                                    date_value_run = para.add_run(date_value)
                                    date_value_run.font.underline = True
                                    if original_font_size:
                                        date_value_run.font.size = original_font_size
                                    if original_font_name:
                                        date_value_run.font.name = original_font_name
                                else:
                                    # Date not updated yet, add placeholder
                                    date_placeholder_run = para.add_run(
                                        "__________________"
                                    )
                                    if original_font_size:
                                        date_placeholder_run.font.size = (
                                            original_font_size
                                        )
                                    if original_font_name:
                                        date_placeholder_run.font.name = (
                                            original_font_name
                                        )

                                # Verify the result
                                final_text = para.text
                                if "Teacher Signature:" not in final_text:
                                    logger.error(
                                        "signature_text_missing_after_name_insertion",
                                        extra={
                                            "user_name": user_name,
                                            "final_text": final_text,
                                        },
                                    )
                            break  # Break from paragraph loop after processing
                    break  # Break from cell loop after finding Teacher Signature

    def _add_signature_box(
        self,
        doc: Document,
        date: datetime,
        template_path: str,
        signature_image_path: str = None,
        user_name: str = None,
    ):
        """Add signature box from template to the end of document.

        Args:
            doc: Document to add signature to
            date: Date to display
            template_path: Path to the template document (user-specific or default)
            signature_image_path: Optional path to signature image file (user-specific)
            user_name: User's name to use if no signature image is provided
        """
        # Load the template to get the signature table
        template_doc = Document(template_path)

        # Find the signature table in the template (look for "Required Signatures")
        signature_table = None
        for table in template_doc.tables:
            table_text = "\n".join(
                [cell.text for row in table.rows for cell in row.cells]
            )
            if "Required Signatures" in table_text:
                signature_table = table
                break

        if signature_table:
            # Add some space before signature
            doc.add_paragraph()

            # Copy the signature table from template
            from copy import deepcopy

            new_table = deepcopy(signature_table._element)
            doc._element.body.append(new_table)

            # Get the newly added table (last table in doc)
            added_table = doc.tables[-1]

            # Find and fill the date field in the signature table (underlined)
            # Find the cell containing "Teacher Signature:" and update the Date that appears AFTER it
            date_formatted = date.strftime("%m/%d/%Y")

            for row in added_table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    # Look for cell containing "Teacher Signature:"
                    if "Teacher Signature:" in cell_text:
                        # Find the paragraph containing both "Teacher Signature:" and "Date:"
                        for para in cell.paragraphs:
                            para_text = para.text
                            if (
                                "Teacher Signature:" in para_text
                                and "Date:" in para_text
                            ):
                                # Find the "Date:" that appears AFTER "Teacher Signature:" in the paragraph
                                teacher_pos = para_text.find("Teacher Signature:")
                                date_pos = para_text.find(
                                    "Date:", teacher_pos
                                )  # Find Date after Teacher Signature

                                if (
                                    date_pos > teacher_pos
                                ):  # Date appears after Teacher Signature
                                    # Find the run containing this Date (the one after Teacher Signature)
                                    date_run = None
                                    original_font_size = None
                                    original_font_name = None

                                    # Track position in paragraph to find the right Date run
                                    current_pos = 0
                                    for run in para.runs:
                                        run_text = run.text
                                        run_start = current_pos
                                        run_end = current_pos + len(run_text)

                                        # Check if this run contains the Date we're looking for (after Teacher Signature)
                                        if (
                                            "Date:" in run_text
                                            and run_start >= teacher_pos
                                        ):
                                            # This is the Date run after Teacher Signature
                                            date_run = run
                                            if run.font.size:
                                                original_font_size = run.font.size
                                            if run.font.name:
                                                original_font_name = run.font.name
                                            break

                                        current_pos = run_end

                                    if date_run:
                                        # Update this Date field
                                        run_text = date_run.text
                                        if "Date:" in run_text:
                                            para.clear()
                                            # Rebuild paragraph: keep everything before Date, then add Date with value
                                            before_date_text = para_text[:date_pos]
                                            if before_date_text.strip():
                                                before_run = para.add_run(
                                                    before_date_text
                                                )
                                                if original_font_size:
                                                    before_run.font.size = (
                                                        original_font_size
                                                    )
                                                if original_font_name:
                                                    before_run.font.name = (
                                                        original_font_name
                                                    )

                                            # Add Date label and value (Date label should be bold)
                                            # NOTE: This spacing will be overwritten by _add_signature_image_to_table
                                            # or _add_user_name_to_table which rebuild the paragraph.
                                            # Actual spacing is set in those functions (91 spaces with image, 45 without)
                                            spacing_text = (
                                                " " * 90
                                            )  # This value is overwritten - see _add_signature_image_to_table/_add_user_name_to_table
                                            date_label_run = para.add_run(
                                                spacing_text + "Date: "
                                            )
                                            date_label_run.font.bold = True
                                            date_value_run = para.add_run(
                                                date_formatted
                                            )
                                            date_value_run.font.underline = True
                                            if original_font_size:
                                                date_label_run.font.size = (
                                                    original_font_size
                                                )
                                                date_value_run.font.size = (
                                                    original_font_size
                                                )
                                            if original_font_name:
                                                date_label_run.font.name = (
                                                    original_font_name
                                                )
                                                date_value_run.font.name = (
                                                    original_font_name
                                                )

                                            # Add any text after Date
                                            after_date_text = para_text[
                                                date_pos + len("Date: ") :
                                            ]
                                            after_date_text = after_date_text.lstrip(
                                                "_"
                                            ).strip()
                                            if after_date_text:
                                                after_run = para.add_run(
                                                    after_date_text
                                                )
                                                if original_font_size:
                                                    after_run.font.size = (
                                                        original_font_size
                                                    )
                                                if original_font_name:
                                                    after_run.font.name = (
                                                        original_font_name
                                                    )
                                        break
                        break

            # Now find the "Teacher Signature: " cell and add image/name inline
            # Use the helper methods for consistency
            if (
                signature_image_path
                and signature_image_path.strip()
                and Path(signature_image_path).exists()
            ):
                self._add_signature_image_to_table(added_table, signature_image_path)
            elif user_name:
                self._add_user_name_to_table(added_table, user_name)
        else:
            # Fallback to simple signature if template table not found
            doc.add_paragraph()
            doc.add_paragraph()
            sig_para = doc.add_paragraph()
            sig_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            sig_run = sig_para.add_run("Signature: _" + "_" * 50)
            sig_run.font.size = Pt(11)
            date_para = doc.add_paragraph()
            date_run = date_para.add_run(f"Date: {date.strftime('%m/%d/%Y')}")
            date_run.font.size = Pt(11)

    def _calculate_week_number(self, week_of: str) -> int:
        """Calculate week number from date range.

        Args:
            week_of: Week date range (MM/DD-MM/DD)

        Returns:
            Week number (1-52)
        """
        try:
            # Parse first date from range
            first_date = week_of.split("-")[0].strip()
            month, day = map(int, first_date.split("/"))

            # Simple week calculation (can be improved)
            # Assuming school year starts in September
            if month >= 9:  # Sept-Dec
                week_num = (month - 9) * 4 + (day // 7) + 1
            else:  # Jan-June
                week_num = (month + 3) * 4 + (day // 7) + 1

            return min(week_num, 52)
        except Exception:
            return 1


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
