import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import get_db
from backend.schema import ScheduleEntry

def verify_refactor():
    print("Verifying refactor...")
    
    # Initialize DB
    db = get_db()
    
    # Create test user ID
    user_id = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"Test User ID: {user_id}")
    
    try:
        # Create a schedule entry directly
        entry_data = {
            "user_id": user_id,
            "day_of_week": "monday",
            "slot_number": 1,
            "start_time": "08:00",
            "end_time": "09:00",
            "subject": "Math",
            "grade": "5",
            "homeroom": "101",
            "is_active": True
        }
        
        print("Creating schedule entry...")
        schedule_id = db.create_schedule_entry(entry_data)
        print(f"Created schedule entry: {schedule_id}")
        
        # Retrieve schedule
        print("Retrieving schedule...")
        schedule = db.get_user_schedule(user_id)
        
        if not schedule:
            print("ERROR: No schedule found!")
            return False
            
        entry = schedule[0]
        print(f"Retrieved entry type: {type(entry)}")
        
        # Verify it's an object, not a dict
        if isinstance(entry, dict):
            print("ERROR: Entry is a dictionary, expected object!")
            return False
            
        if not hasattr(entry, 'id'):
            print("ERROR: Entry object missing 'id' attribute!")
            return False
            
        # Verify attribute access works
        print(f"Entry ID: {entry.id}")
        print(f"Entry User ID: {entry.user_id}")
        print(f"Entry Subject: {entry.subject}")
        
        if entry.id != schedule_id:
            print(f"ERROR: ID mismatch! Expected {schedule_id}, got {entry.id}")
            return False
            
        print("SUCCESS: Schedule entry retrieved as object and attributes are accessible.")
        
        # Clean up
        print("Cleaning up...")
        db.delete_schedule_entry(schedule_id)
        
        return True
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_refactor():
        print("\nVERIFICATION PASSED")
        sys.exit(0)
    else:
        print("\nVERIFICATION FAILED")
        sys.exit(1)
