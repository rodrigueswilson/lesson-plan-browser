"""Check original slot data for primary teacher fields."""
import sys
from backend.database import get_db

def check_original_slot_teachers(user_id: str):
    """Check teacher fields in original slot data."""
    print(f"Checking original slot teachers for user: {user_id}")
    print("=" * 80)
    
    # Get database
    db = get_db(user_id=user_id)
    
    # Get user slots
    slots = db.get_user_slots(user_id)
    
    print(f"\nFound {len(slots)} slots:")
    for slot in slots:
        slot_num = slot.get("slot_number") if isinstance(slot, dict) else getattr(slot, "slot_number", None)
        subject = slot.get("subject") if isinstance(slot, dict) else getattr(slot, "subject", None)
        
        print(f"\nSlot {slot_num} ({subject}):")
        
        # Check if it's a dict or object
        if isinstance(slot, dict):
            print(f"  primary_teacher_name: {slot.get('primary_teacher_name')}")
            print(f"  primary_teacher_first_name: {slot.get('primary_teacher_first_name')}")
            print(f"  primary_teacher_last_name: {slot.get('primary_teacher_last_name')}")
            print(f"  teacher_name: {slot.get('teacher_name')}")
        else:
            print(f"  primary_teacher_name: {getattr(slot, 'primary_teacher_name', None)}")
            print(f"  primary_teacher_first_name: {getattr(slot, 'primary_teacher_first_name', None)}")
            print(f"  primary_teacher_last_name: {getattr(slot, 'primary_teacher_last_name', None)}")
            print(f"  teacher_name: {getattr(slot, 'teacher_name', None)}")

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_original_slot_teachers(user_id)
