"""
Utility functions for enriching lesson_json with data from lesson steps.

This module provides functions to backfill missing vocabulary_cognates and sentence_frames
from lesson steps when they're missing from the lesson_json structure.
"""
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
from backend.database_interface import DatabaseInterface
from backend.telemetry import logger


def enrich_lesson_json_from_steps(
    lesson_json: Dict[str, Any],
    plan_id: str,
    db: DatabaseInterface,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Enrich lesson_json with vocabulary_cognates and sentence_frames from lesson steps
    if they're missing from the JSON structure.
    
    This ensures DOCX export includes vocabulary/frames even if they're not in the
    original JSON, by extracting them from the database steps.
    
    Args:
        lesson_json: The lesson plan JSON structure
        plan_id: The plan ID to query steps for
        db: Database interface to query lesson steps
        use_cache: Whether to use caching for step queries (default: True)
        
    Returns:
        Enriched lesson_json with vocabulary_cognates and sentence_frames backfilled
    """
    if not lesson_json or "days" not in lesson_json:
        return lesson_json
    
    # Collect all slots that need enrichment
    slots_to_enrich: List[Tuple[str, int, Dict[str, Any]]] = []
    days_to_check = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    print(f"[DEBUG] Starting enrichment for plan_id={plan_id}")
    print(f"[DEBUG] lesson_json has 'days' key: {'days' in lesson_json}")
    if "days" in lesson_json:
        print(f"[DEBUG] Days in lesson_json: {list(lesson_json['days'].keys())}")
    
    for day in days_to_check:
        day_data = lesson_json.get("days", {}).get(day, {})
        if not day_data:
            print(f"[DEBUG] No data for {day}")
            continue
        print(f"[DEBUG] Checking {day}, has 'slots' key: {'slots' in day_data}")
        
        # Check if this day has slots structure
        # If "slots" key exists and is a list, it's multi-slot structure
        # Otherwise, it's single-slot structure (or legacy structure)
        if "slots" in day_data and isinstance(day_data.get("slots"), list):
            # Multi-slot structure - check each slot
            slots = day_data["slots"]
            for slot_data in slots:
                if not isinstance(slot_data, dict):
                    continue
                slot_number = slot_data.get("slot_number")
                if slot_number is None:
                    continue
                
                has_vocab = bool(slot_data.get("vocabulary_cognates"))
                has_frames = bool(slot_data.get("sentence_frames"))
                needs_enrichment = not has_vocab or not has_frames
                
                if needs_enrichment:
                    print(f"[DEBUG] {day} slot {slot_number} needs enrichment: vocab={has_vocab}, frames={has_frames}")
                    slots_to_enrich.append((day, slot_number, slot_data))
        else:
            # Single-slot structure - check day_data directly
            slot_number = day_data.get("slot_number")
            if slot_number is not None:
                has_vocab = bool(day_data.get("vocabulary_cognates"))
                has_frames = bool(day_data.get("sentence_frames"))
                needs_enrichment = not has_vocab or not has_frames
                
                if needs_enrichment:
                    print(f"[DEBUG] {day} slot {slot_number} (single-slot) needs enrichment: vocab={has_vocab}, frames={has_frames}")
                    slots_to_enrich.append((day, slot_number, day_data))
    
    # Batch enrich all slots
    if slots_to_enrich:
        print(f"[DEBUG] Enriching {len(slots_to_enrich)} slots")
        _batch_enrich_slots_from_steps(slots_to_enrich, plan_id, db, use_cache)
    else:
        print(f"[DEBUG] No slots need enrichment")
    
    return lesson_json


def _batch_enrich_slots_from_steps(
    slots_to_enrich: List[Tuple[str, int, Dict[str, Any]]],
    plan_id: str,
    db: DatabaseInterface,
    use_cache: bool = True,
) -> None:
    """
    Batch enrich multiple slots from steps, using caching to avoid duplicate queries.
    
    Args:
        slots_to_enrich: List of (day, slot_number, slot_data) tuples to enrich
        plan_id: The plan ID to query steps for
        db: Database interface to query lesson steps
        use_cache: Whether to use caching for step queries
    """
    print(f"[DEBUG] Starting batch enrichment for {len(slots_to_enrich)} slots in plan {plan_id}")
    
    # Cache for step queries to avoid duplicate database calls
    step_cache: Dict[Tuple[str, int], List[Any]] = {}
    
    for day, slot_number, slot_data in slots_to_enrich:
        needs_vocab = not slot_data.get("vocabulary_cognates")
        needs_frames = not slot_data.get("sentence_frames")
        
        if not needs_vocab and not needs_frames:
            print(f"[DEBUG] Skipping {day} slot {slot_number} - already has both vocab and frames")
            continue  # Nothing to do for this slot
        
        cache_key = (day, slot_number)
        
        # Get steps from cache or database
        if use_cache and cache_key in step_cache:
            steps = step_cache[cache_key]
            print(f"[DEBUG] Using cached steps for {day} slot {slot_number}")
        else:
            try:
                print(f"[DEBUG] Querying database for steps: plan_id={plan_id}, day={day}, slot={slot_number}")
                steps = db.get_lesson_steps(plan_id, day_of_week=day, slot_number=slot_number)
                print(f"[DEBUG] Database returned {len(steps)} steps for {day} slot {slot_number}")
                if use_cache:
                    step_cache[cache_key] = steps
            except Exception as e:
                print(f"[DEBUG] ERROR querying steps: {e}")
                logger.debug(
                    "could_not_extract_from_steps",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot_number,
                        "error": str(e),
                    },
                )
                continue
        
        # Extract data from steps
        _extract_data_from_steps(
            slot_data, steps, plan_id, day, slot_number, needs_vocab, needs_frames
        )


def _extract_data_from_steps(
    slot_data: Dict[str, Any],
    steps: List[Any],
    plan_id: str,
    day: str,
    slot_number: int,
    needs_vocab: bool,
    needs_frames: bool,
) -> None:
    """
    Extract vocabulary_cognates and sentence_frames from steps into slot_data.
    
    Args:
        slot_data: The slot data dictionary to enrich (modified in place)
        steps: List of lesson steps to search through
        plan_id: The plan ID (for logging)
        day: Day of week (for logging)
        slot_number: Slot number (for logging)
        needs_vocab: Whether vocabulary_cognates is needed
        needs_frames: Whether sentence_frames is needed
    """
    # Debug: Log what we're looking for and what we found
    print(f"[DEBUG] Enrichment: plan_id={plan_id}, day={day}, slot={slot_number}, needs_vocab={needs_vocab}, needs_frames={needs_frames}")
    print(f"[DEBUG] Found {len(steps)} steps for {day} slot {slot_number}")
    
    if not steps:
        print(f"[DEBUG] WARNING: No steps found for {day} slot {slot_number} - cannot enrich")
        logger.debug(
            "no_steps_found_for_enrichment",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot_number,
            },
        )
        return
    
    # Log all step names for debugging
    step_names = [getattr(step, 'step_name', 'unknown') for step in steps]
    print(f"[DEBUG] Step names found: {step_names}")
    
    vocab_step_found = False
    frames_step_found = False
    
    for step in steps:
        step_name = getattr(step, 'step_name', 'unknown')
        
        # Extract vocabulary_cognates if missing
        if needs_vocab and step_name == "Vocabulary / Cognate Awareness":
            vocab_step_found = True
            has_vocab_attr = hasattr(step, 'vocabulary_cognates')
            vocab_value = getattr(step, 'vocabulary_cognates', None)
            vocab_is_truthy = bool(vocab_value)
            
            print(f"[DEBUG] Found Vocabulary step - has_attr={has_vocab_attr}, value_is_truthy={vocab_is_truthy}")
            if vocab_value:
                print(f"[DEBUG] Vocabulary value type: {type(vocab_value)}, length: {len(vocab_value) if isinstance(vocab_value, (list, dict)) else 'N/A'}")
            
            if has_vocab_attr and vocab_value:
                slot_data["vocabulary_cognates"] = vocab_value
                logger.info(
                    "vocabulary_cognates_extracted_from_step",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot_number,
                        "vocab_count": len(vocab_value) 
                        if isinstance(vocab_value, list) 
                        else 0,
                    },
                )
                print(f"[DEBUG] SUCCESS: Added vocabulary_cognates to slot {slot_number}")
                needs_vocab = False  # Found it, no need to keep looking
            else:
                print(f"[DEBUG] WARNING: Vocabulary step found but no valid vocabulary_cognates data")
        
        # Extract sentence_frames if missing
        if needs_frames and step_name == "Sentence Frames / Stems / Questions":
            frames_step_found = True
            has_frames_attr = hasattr(step, 'sentence_frames')
            frames_value = getattr(step, 'sentence_frames', None)
            frames_is_truthy = bool(frames_value)
            
            print(f"[DEBUG] Found Sentence Frames step - has_attr={has_frames_attr}, value_is_truthy={frames_is_truthy}")
            if frames_value:
                print(f"[DEBUG] Frames value type: {type(frames_value)}, length: {len(frames_value) if isinstance(frames_value, (list, dict)) else 'N/A'}")
            
            if has_frames_attr and frames_value:
                slot_data["sentence_frames"] = frames_value
                logger.info(
                    "sentence_frames_extracted_from_step",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot_number,
                        "frames_count": len(frames_value) 
                        if isinstance(frames_value, list) 
                        else 0,
                    },
                )
                print(f"[DEBUG] SUCCESS: Added sentence_frames to slot {slot_number}")
                needs_frames = False  # Found it, no need to keep looking
            else:
                print(f"[DEBUG] WARNING: Sentence Frames step found but no valid sentence_frames data")
        
        # Early exit if we found both
        if not needs_vocab and not needs_frames:
            break
    
    # Log if we didn't find the expected steps
    if needs_vocab and not vocab_step_found:
        print(f"[DEBUG] WARNING: Needed vocabulary but no 'Vocabulary / Cognate Awareness' step found")
    if needs_frames and not frames_step_found:
        print(f"[DEBUG] WARNING: Needed sentence_frames but no 'Sentence Frames / Stems / Questions' step found")

