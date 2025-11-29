"""
Utility functions for schedule management.
Handles normalization of subject names and detection of non-class periods.
"""

from typing import Optional

NON_CLASS_PERIODS = [
    "PREP",
    "Prep Time",
    "PREP TIME",
    "Prep",
    "A.M. Routine",
    "AM Routine",
    "Morning Routine",
    "Lunch",
    "LUNCH",
    "Dismissal",
    "DISMISSAL"
]


def is_non_class_period(subject: str) -> bool:
    """Check if subject is a non-class period.
    
    Args:
        subject: Subject name to check
        
    Returns:
        True if subject is a non-class period (PREP, Lunch, etc.)
    """
    if not subject:
        return False
    return subject.strip().upper() in [s.upper() for s in NON_CLASS_PERIODS]


def normalize_subject(subject: str) -> str:
    """Normalize subject names (e.g., 'PREP' and 'Prep Time' -> 'PREP').
    
    Args:
        subject: Subject name to normalize
        
    Returns:
        Normalized subject name
    """
    if not subject:
        return ""
    
    subject_upper = subject.strip().upper()
    
    # Normalize PREP variations
    if subject_upper in ["PREP", "PREP TIME", "PREP TIME"]:
        return "PREP"
    
    # Normalize A.M. Routine variations
    if subject_upper in ["A.M. ROUTINE", "AM ROUTINE", "MORNING ROUTINE"]:
        return "A.M. Routine"
    
    # Normalize Lunch
    if subject_upper == "LUNCH":
        return "Lunch"
    
    # Normalize Dismissal
    if subject_upper == "DISMISSAL":
        return "Dismissal"
    
    # Return original if no normalization needed
    return subject.strip()


def prepare_schedule_entry(
    user_id: str,
    day_of_week: str,
    start_time: str,
    end_time: str,
    subject: str,
    homeroom: str = None,
    grade: str = None,
    slot_number: int = 0,
    plan_slot_group_id: Optional[str] = None,
) -> dict:
    """Prepare a schedule entry with automatic normalization and is_active detection.
    
    Args:
        user_id: User ID
        day_of_week: Day of week
        start_time: Start time
        end_time: End time
        subject: Subject name
        homeroom: Homeroom (optional)
        grade: Grade (optional)
        slot_number: Slot number
        
    Returns:
        Dictionary ready for database insertion
    """
    normalized_subject = normalize_subject(subject)
    plan_slot_group_id = plan_slot_group_id.strip() if plan_slot_group_id else None
    is_non_class = is_non_class_period(normalized_subject)
    
    # Auto-clear homeroom and grade for non-class periods
    if is_non_class:
        homeroom = None
        grade = None
        plan_slot_group_id = None
        is_active = False
    else:
        is_active = True
    
    return {
        'user_id': user_id,
        'day_of_week': day_of_week.lower(),
        'start_time': start_time,
        'end_time': end_time,
        'subject': normalized_subject,
        'homeroom': homeroom,
        'grade': grade,
        'slot_number': slot_number,
        'plan_slot_group_id': plan_slot_group_id,
        'is_active': is_active
    }

