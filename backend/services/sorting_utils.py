
from typing import Any, Dict, List, Union

def sort_slots(slots: Union[List[Any], Dict[str, Any]]) -> List[Any]:
    """
    Sort lesson plan slots by start_time (chronological) with slot_number as fallback.
    
    This ensures slots are ordered by their actual schedule times for each day, which is
    critical since subjects, grades, and rooms vary by day. The chronological ordering
    ensures objectives and sentence frames PDFs reflect the correct daily schedule order.
    
    Handles both list and dictionary slot structures.
    """
    if not slots:
        return []

    # Convert dictionary to list if necessary
    slot_list = []
    if isinstance(slots, dict):
        for key, value in slots.items():
            if isinstance(value, dict):
                # Ensure slot_number is preserved if not present in value
                if "slot_number" not in value:
                    try:
                        value["slot_number"] = int(key)
                    except (ValueError, TypeError):
                        pass
                slot_list.append(value)
    else:
        slot_list = list(slots)

    def get_sort_key(slot: Any) -> tuple:
        if not isinstance(slot, dict):
            return (1, "", 0)
        
        # Primary key: presence of time (0 if has time, 1 if no time)
        # Secondary key: start_time (HH:MM or similar) - chronological order
        # Tertiary key: slot_number (fallback if no time)
        # This ensures slots are ordered by their actual schedule time for each day
        start_time = slot.get("start_time", "") or ""
        
        slot_num = slot.get("slot_number", 0)
        try:
            slot_num = int(slot_num)
        except (ValueError, TypeError):
            slot_num = 0
        
        # Convert time to sortable format (HH:MM -> minutes since midnight)
        # This ensures proper chronological ordering
        time_sort = 0
        if start_time:
            try:
                parts = str(start_time).split(":")
                if len(parts) >= 2:
                    time_sort = int(parts[0]) * 60 + int(parts[1])
            except (ValueError, TypeError):
                time_sort = 0
            return (0, time_sort, slot_num)  # Has time: sort by time, then slot_number
        else:
            return (1, 0, slot_num)  # No time: sort by slot_number only

    return sorted(slot_list, key=get_sort_key)
