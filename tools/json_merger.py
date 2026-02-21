"""
JSON Merger for combining multiple lesson plan JSONs into a single multi-slot structure.

This module merges multiple single-slot lesson JSONs into a unified structure where
each day contains an array of slots, allowing the renderer to produce a single DOCX
with all class slots properly organized by day.
"""

from typing import List, Dict, Any
from collections import defaultdict
from backend.services.sorting_utils import sort_slots


def merge_lesson_jsons(lessons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple lesson JSONs into a single combined structure.
    
    Each input lesson has structure:
    {
        'slot_number': int,
        'subject': str,
        'lesson_json': {
            'metadata': {...},
            'days': {
                'monday': {...day_plan...},
                'tuesday': {...day_plan...},
                ...
            }
        }
    }
    
    Output structure:
    {
        'metadata': {...},  # From first lesson, with merged info
        'days': {
            'monday': {
                'slots': [
                    {
                        'slot_number': 1,
                        'subject': 'ELA',
                        'teacher_name': 'Lang',
                        ...day_plan_fields...
                    },
                    {
                        'slot_number': 3,
                        'subject': 'Science',
                        'teacher_name': 'Savoca',
                        ...day_plan_fields...
                    }
                ]
            },
            'tuesday': {...},
            ...
        }
    }
    
    Args:
        lessons: List of dicts with 'slot_number', 'subject', 'lesson_json'
        
    Returns:
        Combined JSON with all slots organized by day
    """
    if not lessons:
        raise ValueError("No lessons provided to merge")
    
    # Initialize merged structure
    merged = {
        "metadata": {},
        "days": {
            "monday": {"slots": []},
            "tuesday": {"slots": []},
            "wednesday": {"slots": []},
            "thursday": {"slots": []},
            "friday": {"slots": []}
        }
    }
    
    # Extract metadata from first lesson (week_of, grade, etc.)
    if lessons:
        first_lesson = lessons[0]['lesson_json']
        if 'metadata' in first_lesson:
            merged['metadata'] = first_lesson['metadata'].copy()
    
    # Collect all hyperlinks and images from all lessons
    # CRITICAL: Tag each media item with its source slot to prevent cross-slot contamination
    all_hyperlinks = []
    all_images = []
    media_schema_version = None
    
    for lesson in lessons:
        lesson_json = lesson['lesson_json']
        slot_number = lesson['slot_number']
        subject = lesson['subject']
        
        # Collect hyperlinks and tag with source slot
        if '_hyperlinks' in lesson_json:
            for link in lesson_json['_hyperlinks']:
                # Add slot metadata to each hyperlink
                link['_source_slot'] = slot_number
                link['_source_subject'] = subject
                all_hyperlinks.append(link)
        
        # Collect images and tag with source slot
        if '_images' in lesson_json:
            for image in lesson_json['_images']:
                # Add slot metadata to each image
                image['_source_slot'] = slot_number
                image['_source_subject'] = subject
                all_images.append(image)
        
        # Get schema version (use the highest version found)
        if '_media_schema_version' in lesson_json:
            if media_schema_version is None or lesson_json['_media_schema_version'] > media_schema_version:
                media_schema_version = lesson_json['_media_schema_version']
    
    # Add collected media to merged JSON
    if all_hyperlinks:
        print(f"[DEBUG] JSON_MERGER: Adding {len(all_hyperlinks)} hyperlinks to merged JSON")
        merged['_hyperlinks'] = all_hyperlinks
    else:
        print(f"[WARN] JSON_MERGER: No hyperlinks found in lessons!")
        # DIAGNOSTIC: Log details about each lesson to help debug
        for i, lesson in enumerate(lessons):
            lesson_json = lesson.get('lesson_json', {})
            has_hyperlinks_key = '_hyperlinks' in lesson_json
            hyperlinks_count = len(lesson_json.get('_hyperlinks', []))
            print(
                f"[DEBUG] JSON_MERGER: Lesson {i+1}: slot={lesson.get('slot_number')}, "
                f"subject={lesson.get('subject')}, has_hyperlinks_key={has_hyperlinks_key}, "
                f"hyperlinks_count={hyperlinks_count}"
            )
    if all_images:
        merged['_images'] = all_images
    if media_schema_version:
        merged['_media_schema_version'] = media_schema_version
    
    # Merge slots by day
    for lesson in lessons:
        lesson_json = lesson['lesson_json']
        
        # Create slot metadata - include all identifying information
        slot_info = {
            'slot_number': lesson['slot_number'],
            'subject': lesson['subject']
        }
        
        # Get primary teacher fields from original slot data (preferred) or metadata (fallback)
        slot_data = lesson.get('slot_data', {})
        metadata = lesson_json.get('metadata', {})
        
        # Priority: Use original slot data for primary teacher fields, fallback to metadata
        # This ensures each slot gets its own primary teacher, not the combined teacher name
        if slot_data:
            # Extract from slot_data (original slot from database)
            if isinstance(slot_data, dict):
                slot_info['primary_teacher_name'] = slot_data.get('primary_teacher_name')
                slot_info['primary_teacher_first_name'] = slot_data.get('primary_teacher_first_name')
                slot_info['primary_teacher_last_name'] = slot_data.get('primary_teacher_last_name')
            else:
                # Handle database object
                slot_info['primary_teacher_name'] = getattr(slot_data, 'primary_teacher_name', None)
                slot_info['primary_teacher_first_name'] = getattr(slot_data, 'primary_teacher_first_name', None)
                slot_info['primary_teacher_last_name'] = getattr(slot_data, 'primary_teacher_last_name', None)
        
        # Fallback to metadata if slot_data doesn't have primary teacher fields
        if not slot_info.get('primary_teacher_name'):
            if 'primary_teacher_name' in metadata:
                slot_info['primary_teacher_name'] = metadata['primary_teacher_name']
            if 'primary_teacher_first_name' in metadata:
                slot_info['primary_teacher_first_name'] = metadata['primary_teacher_first_name']
            if 'primary_teacher_last_name' in metadata:
                slot_info['primary_teacher_last_name'] = metadata['primary_teacher_last_name']
        
        # Don't copy teacher_name from metadata - it's the combined name and should not override slot-specific teachers
        
        # Add grade, homeroom, and time for accurate slot matching
        # CRITICAL: Use metadata values which should be preserved from original slot data
        if 'grade' in metadata:
            slot_info['grade'] = metadata['grade']
            print(f"[DEBUG] JSON_MERGER: Slot {slot_number} grade from metadata: {metadata['grade']}")
        if 'homeroom' in metadata:
            slot_info['homeroom'] = metadata['homeroom']
            print(f"[DEBUG] JSON_MERGER: Slot {slot_number} homeroom from metadata: {metadata['homeroom']}")
        if 'start_time' in metadata:
            slot_info['start_time'] = metadata['start_time']
        if 'end_time' in metadata:
            slot_info['end_time'] = metadata['end_time']
        
        # Add each day's content to the merged structure
        if 'days' in lesson_json:
            for day_name, day_content in lesson_json['days'].items():
                day_lower = day_name.lower()
                if day_lower in merged['days']:
                    if not isinstance(day_content, dict):
                        print(f"[WARN] JSON_MERGER: Day content for {day_lower} in slot {slot_number} is not a dictionary: {type(day_content)}. Skipping.")
                        continue
                    # Combine slot info with day content
                    # CRITICAL: Preserve day-specific times if available in day_times metadata
                    day_slot_info = slot_info.copy()
                    day_times = metadata.get("day_times")
                    if isinstance(day_times, dict) and day_lower in day_times:
                        day_specific = day_times[day_lower]
                        if day_specific.get("start_time"):
                            day_slot_info["start_time"] = day_specific["start_time"]
                        if day_specific.get("end_time"):
                            day_slot_info["end_time"] = day_specific["end_time"]

                    # CRITICAL: day_slot_info must come AFTER day_content to ensure slot-specific
                    # metadata (grade, homeroom, time) is preserved and not overwritten by day_content
                    slot_data = {**day_content, **day_slot_info}
                    merged['days'][day_lower]['slots'].append(slot_data)
    
    # Sort slots using the chronological sorting utility (start_time first)
    for day in merged['days']:
        if 'slots' in merged['days'][day]:
            merged['days'][day]['slots'] = sort_slots(merged['days'][day]['slots'])
    
    # If only one slot, flatten the structure (remove slots array)
    # This prevents "Slot 1: Subject" from appearing in every cell
    if len(lessons) == 1:
        print(f"[DEBUG] JSON_MERGER: Single slot detected, flattening structure")
        for day in merged['days']:
            if merged['days'][day]['slots']:
                # Take the first (and only) slot and merge its content directly into the day
                slot_data = merged['days'][day]['slots'][0]
                # Remove slot metadata fields
                slot_data.pop('slot_number', None)
                slot_data.pop('subject', None)
                slot_data.pop('teacher_name', None)
                # Replace slots array with flattened content
                merged['days'][day] = slot_data
    
    return merged


def validate_merged_json(merged: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the merged JSON structure.
    
    Args:
        merged: Merged JSON to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required keys
    if 'metadata' not in merged:
        return False, "Missing 'metadata' key"
    
    if 'days' not in merged:
        return False, "Missing 'days' key"
    
    # Check all days present
    required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    for day in required_days:
        if day not in merged['days']:
            return False, f"Missing day: {day}"
    
    # Check structure: either all days have 'slots' array (multi-slot) or none do (single-slot)
    days_with_slots = sum(1 for day in required_days if 'slots' in merged['days'][day])
    
    if days_with_slots == 0:
        # Single-slot structure (flattened) - check that days have content
        for day in required_days:
            day_data = merged['days'][day]
            # At least one day should have some content
            if any(key in day_data for key in ['unit_lesson', 'objective', 'anticipatory_set', 
                                                 'tailored_instruction', 'misconceptions', 
                                                 'assessment', 'homework']):
                return True, ""  # Found content in at least one day
        return False, "No content found in any day"
    
    elif days_with_slots == len(required_days):
        # Multi-slot structure - check that we have at least one slot somewhere
        total_slots = sum(len(merged['days'][day]['slots']) for day in required_days)
        if total_slots == 0:
            return False, "No slots found in any day"
        return True, ""
    
    else:
        # Mixed structure - invalid
        return False, f"Inconsistent structure: {days_with_slots}/{len(required_days)} days have 'slots' array"


def get_merge_summary(merged: Dict[str, Any]) -> str:
    """
    Generate a summary of the merged JSON for logging.
    
    Args:
        merged: Merged JSON
        
    Returns:
        Human-readable summary string
    """
    lines = []
    lines.append("Merged JSON Summary:")
    lines.append(f"  Week: {merged.get('metadata', {}).get('week_of', 'N/A')}")
    lines.append(f"  Grade: {merged.get('metadata', {}).get('grade', 'N/A')}")
    
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        slots = merged.get('days', {}).get(day, {}).get('slots', [])
        if slots:
            slot_info = ', '.join([
                f"Slot {s.get('slot_number', '?')}: {s.get('subject', '?')}"
                for s in slots
            ])
            lines.append(f"  {day.capitalize()}: {len(slots)} slots ({slot_info})")
        else:
            lines.append(f"  {day.capitalize()}: 0 slots")
    
    return '\n'.join(lines)
