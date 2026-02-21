"""Check class slots configuration to see what grades/homerooms they should have."""
import sys
from backend.database import get_db

def check_class_slots(user_id: str):
    """Check class slots configuration."""
    print(f"Checking class slots for user: {user_id}")
    print("=" * 80)
    
    db = get_db(user_id=user_id)
    slots = db.get_user_slots(user_id)
    
    if not slots:
        print("No slots found")
        return
    
    print(f"Found {len(slots)} slots:")
    print()
    
    for slot in slots:
        print(f"Slot {slot.slot_number} ({slot.subject}):")
        print(f"  Grade: {slot.grade}")
        print(f"  Homeroom: {slot.homeroom}")
        print(f"  Primary Teacher: {slot.primary_teacher_first_name} {slot.primary_teacher_last_name}")
        print()

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "04fe8898-cb89-4a73-affb-64a97a98f820"
    check_class_slots(user_id)
