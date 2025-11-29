"""
Example of using Dagster for slot processing pipeline.
This would make the data flow more consistent and observable.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Would need: pip install dagster dagster-webserver
from dagster import (
    asset, op, job, Out, In, DynamicOut, DynamicOutput,
    AssetMaterialization, ExpectationResult, MetadataValue
)

from backend.database import get_db
from tools.docx_parser import DOCXParser
from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService


@op
def fetch_user_slots(user_id: str) -> List[Dict[str, Any]]:
    """Fetch all slots for a user."""
    db = get_db()
    slots = db.get_user_slots(user_id)
    return slots


@op(out=DynamicOut())
def split_into_slots(slots: List[Dict[str, Any]]):
    """Split batch processing into individual slot operations."""
    for slot in slots:
        yield DynamicOutput(
            value=slot,
            mapping_key=f"slot_{slot['slot_number']}_{slot['subject']}"
        )


@op
def resolve_slot_file(context, slot: Dict[str, Any], week_of: str, week_folder_path: str = None) -> str:
    """Resolve the file path for a specific slot."""
    file_mgr = get_file_manager()
    file_path = file_mgr.resolve_primary_file(slot, week_of, week_folder_path)
    
    if not file_path:
        raise ValueError(f"No file found for slot {slot['slot_number']}: {slot['subject']}")
    
    context.log_event(
        AssetMaterialization(
            asset_key="slot_file_resolved",
            description=f"Resolved file for {slot['subject']}",
            metadata={
                "slot_number": slot['slot_number'],
                "subject": slot['subject'],
                "file_path": file_path
            }
        )
    )
    
    return file_path


@op
def parse_slot_content(file_path: str, slot: Dict[str, Any]) -> Dict[str, Any]:
    """Parse content from a slot's file."""
    parser = DOCXParser(file_path)
    
    # Find actual slot by subject (handles misalignment)
    actual_slot_num = parser.find_slot_by_subject(slot['subject'])
    
    # Extract content for that slot
    content = parser.extract_subject_content_for_slot(
        actual_slot_num, 
        slot['subject'],
        strip_urls=True
    )
    
    return {
        "slot_metadata": slot,
        "actual_slot_number": actual_slot_num,
        "content": content
    }


@op
def transform_to_bilingual(slot_data: Dict[str, Any], provider: str = "openai") -> Dict[str, Any]:
    """Transform slot content to bilingual using LLM."""
    llm_service = LLMService(provider)
    
    # Transform each day's content
    transformed_days = {}
    for day_name, day_content in slot_data["content"]["days"].items():
        transformed = llm_service.transform_lesson_content(day_content)
        transformed_days[day_name] = transformed
    
    return {
        **slot_data,
        "transformed_content": {
            "days": transformed_days,
            "metadata": slot_data["content"]["metadata"]
        }
    }


@op
def validate_slot_output(slot_data: Dict[str, Any]) -> ExpectationResult:
    """Validate that slot transformation meets quality standards."""
    transformed = slot_data["transformed_content"]
    
    # Check all days have content
    missing_days = [
        day for day, content in transformed["days"].items()
        if not content or not any(content.values())
    ]
    
    success = len(missing_days) == 0
    
    return ExpectationResult(
        success=success,
        message=f"Missing content for days: {missing_days}" if not success else "All days have content",
        metadata={
            "slot_number": slot_data["slot_metadata"]["slot_number"],
            "subject": slot_data["slot_metadata"]["subject"],
            "days_with_content": 5 - len(missing_days)
        }
    )


@op
def combine_slots(transformed_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple transformed slots into final document."""
    if not transformed_slots:
        raise ValueError("No slots to combine")
    
    # Sort by slot number
    sorted_slots = sorted(transformed_slots, key=lambda x: x["slot_metadata"]["slot_number"])
    
    # Combine into multi-slot structure
    combined = {
        "metadata": {
            "teacher_name": "Combined Teachers",
            "grade": "Multiple Grades",
            "subject": "Multi-Subject",
            "week_of": sorted_slots[0]["content"]["metadata"].get("week_of"),
            "consolidated": True
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
                    **slot["transformed_content"]["days"][day]
                }
                for slot in sorted_slots
            ]
        }
    
    return combined


@job
def process_weekly_plan():
    """Main pipeline for processing weekly lesson plans."""
    slots = fetch_user_slots()
    slot_files = slots.map(resolve_slot_file)
    parsed_content = slot_files.map(parse_slot_content)
    transformed_content = parsed_content.map(transform_to_bilingual)
    validated_content = transformed_content.map(validate_slot_output)
    combined_result = combine_slots(validated_content.collect())
    
    return combined_result


# Usage:
# result = process_weekly_plan.execute_in_process(
#     run_config={
#         "ops": {
#             "fetch_user_slots": {"inputs": {"user_id": "user123"}},
#             "resolve_slot_file": {"inputs": {"week_of": "2024-11-18"}},
#             "transform_to_bilingual": {"inputs": {"provider": "openai"}}
#         }
#     }
# )
