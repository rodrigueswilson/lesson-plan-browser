"""
Example of using Prefect for slot processing pipeline.
More lightweight than Dagster, good for simple workflows.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Would need: pip install prefect
from prefect import flow, task, get_run_logger
from prefect.orion.schemas.states import Failed, Completed

from backend.database import get_db
from tools.docx_parser import DOCXParser
from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService


@task(retries=2, retry_delay_seconds=30)
def fetch_user_slots(user_id: str) -> List[Dict[str, Any]]:
    """Fetch all slots for a user with retry logic."""
    logger = get_run_logger()
    db = get_db()
    slots = db.get_user_slots(user_id)
    logger.info(f"Found {len(slots)} slots for user {user_id}")
    return slots


@task
def validate_slot_structure(slot_file: str, expected_slot: int) -> bool:
    """Validate that the slot file has expected structure."""
    logger = get_run_logger()
    try:
        parser = DOCXParser(slot_file)
        actual_slot = parser.find_slot_by_subject(
            parser.extract_subject_content_for_slot(expected_slot, "").get("metadata", {}).get("subject", "")
        )
        return True
    except Exception as e:
        logger.warning(f"Slot validation failed: {e}")
        return False


@task(timeout_seconds=300)
def parse_and_transform_slot(
    slot: Dict[str, Any],
    week_of: str,
    week_folder_path: Optional[str] = None,
    provider: str = "openai"
) -> Dict[str, Any]:
    """Parse and transform a single slot."""
    logger = get_run_logger()
    
    # Resolve file
    file_mgr = get_file_manager()
    file_path = file_mgr.resolve_primary_file(slot, week_of, week_folder_path)
    
    if not file_path:
        raise ValueError(f"No file found for slot {slot['slot_number']}: {slot['subject']}")
    
    # Parse content
    parser = DOCXParser(file_path)
    actual_slot_num = parser.find_slot_by_subject(slot['subject'])
    content = parser.extract_subject_content_for_slot(
        actual_slot_num, 
        slot['subject'],
        strip_urls=True
    )
    
    # Transform with LLM
    llm_service = LLMService(provider)
    transformed_days = {}
    
    for day_name, day_content in content["days"].items():
        if any(day_content.values()):  # Only transform if there's content
            transformed = llm_service.transform_lesson_content(day_content)
            transformed_days[day_name] = transformed
        else:
            transformed_days[day_name] = day_content
    
    return {
        "slot_metadata": slot,
        "actual_slot_number": actual_slot_num,
        "transformed_content": {
            "days": transformed_days,
            "metadata": content["metadata"]
        }
    }


@task
def combine_transformed_slots(slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple transformed slots into final document structure."""
    logger = get_run_logger()
    
    if not slots:
        raise ValueError("No slots to combine")
    
    # Sort by slot number for consistent ordering
    sorted_slots = sorted(slots, key=lambda x: x["slot_metadata"]["slot_number"])
    
    # Create combined structure
    combined = {
        "metadata": {
            "teacher_name": " / ".join([
                slot["slot_metadata"].get("primary_teacher_name", "Unknown")
                for slot in sorted_slots
            ]),
            "grade": ", ".join(list(set([
                slot["slot_metadata"]["grade"] 
                for slot in sorted_slots
            ]))),
            "subject": "Multi-Subject",
            "week_of": sorted_slots[0]["transformed_content"]["metadata"].get("week_of"),
            "consolidated": True,
            "slot_count": len(sorted_slots)
        },
        "days": {}
    }
    
    # Combine each day across all slots
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        combined["days"][day] = {
            "slots": [
                {
                    "slot_number": slot["slot_metadata"]["slot_number"],
                    "subject": slot["slot_metadata"]["subject"],
                    "grade": slot["slot_metadata"]["grade"],
                    **slot["transformed_content"]["days"][day]
                }
                for slot in sorted_slots
            ]
        }
    
    logger.info(f"Combined {len(sorted_slots)} slots into single document")
    return combined


@flow(name="process_weekly_lesson_plan")
def process_weekly_plan(
    user_id: str,
    week_of: str,
    week_folder_path: Optional[str] = None,
    provider: str = "openai",
    slot_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main flow for processing weekly lesson plans.
    
    Args:
        user_id: User identifier
        week_of: Week start date (YYYY-MM-DD)
        week_folder_path: Optional custom folder path
        provider: LLM provider (openai/anthropic)
        slot_ids: Optional list of specific slot IDs to process
    
    Returns:
        Combined lesson plan data
    """
    logger = get_run_logger()
    
    try:
        # Fetch slots
        slots = fetch_user_slots(user_id)
        
        # Filter by slot_ids if provided
        if slot_ids:
            slots = [slot for slot in slots if slot["id"] in slot_ids]
            logger.info(f"Filtered to {len(slots)} specific slots")
        
        if not slots:
            raise ValueError(f"No slots found for user {user_id}")
        
        # Process each slot in parallel
        slot_futures = []
        for slot in slots:
            future = parse_and_transform_slot.submit(
                slot=slot,
                week_of=week_of,
                week_folder_path=week_folder_path,
                provider=provider
            )
            slot_futures.append(future)
        
        # Wait for all slots to complete
        transformed_slots = []
        for future in slot_futures:
            try:
                result = future.result()
                transformed_slots.append(result)
            except Exception as e:
                logger.error(f"Slot processing failed: {e}")
                # Continue with other slots - don't fail entire batch
                continue
        
        if not transformed_slots:
            raise ValueError("All slots failed to process")
        
        # Combine results
        combined_plan = combine_transformed_slots(transformed_slots)
        
        logger.info(
            f"Successfully processed {len(transformed_slots)}/{len(slots)} slots "
            f"for week {week_of}"
        )
        
        return {
            "success": True,
            "combined_plan": combined_plan,
            "processed_slots": len(transformed_slots),
            "failed_slots": len(slots) - len(transformed_slots),
            "total_slots": len(slots)
        }
        
    except Exception as e:
        logger.error(f"Weekly plan processing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "processed_slots": 0,
            "failed_slots": 0,
            "total_slots": 0
        }


# Usage example:
# if __name__ == "__main__":
#     result = process_weekly_plan(
#         user_id="user123",
#         week_of="2024-11-18",
#         provider="openai"
#     )
#     print(result)
