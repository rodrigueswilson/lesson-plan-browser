
import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import get_db
from backend.config import settings

USER_ID = '04fe8898-cb89-4a73-affb-64a97a98f820'

async def debug_slots():
    print("DEBUG: Fetching slots using DB and BatchProcessor logic...")
    db = get_db()
    slots_raw = await asyncio.to_thread(db.get_user_slots, USER_ID)
    print(f"DEBUG: Got {len(slots_raw)} slots")

    slots = []
    for slot_obj in slots_raw:
        print(f"\n--- Slot {getattr(slot_obj, 'slot_number', '?')} ---")
        print(f"Raw Object: {slot_obj}")
        
        slot_dict = None
        # Imitate BatchProcessor conversion logic
        if hasattr(slot_obj, "model_dump"):
            try:
                slot_dict = slot_obj.model_dump(mode="python")
            except:
                try: slot_dict = slot_obj.model_dump() 
                except: pass
        
        if slot_dict is None and hasattr(slot_obj, "dict"):
             try: slot_dict = slot_obj.dict()
             except: pass
             
        if slot_dict is None:
             print("FALLBACK CONVERSION")
             # Fallback logic
             slot_dict = {
                 "grade": str(getattr(slot_obj, "grade", "")) if hasattr(slot_obj, "grade") else "",
                 "homeroom": str(getattr(slot_obj, "homeroom", "")) if hasattr(slot_obj, "homeroom") else None,
             }
        
        print(f"Converted Dict Grade: '{slot_dict.get('grade')}' (Type: {type(slot_dict.get('grade'))})")
        print(f"Converted Dict Homeroom: '{slot_dict.get('homeroom')}' (Type: {type(slot_dict.get('homeroom'))})")
        print(f"Converted Dict Subject: '{slot_dict.get('subject')}'")

if __name__ == "__main__":
    asyncio.run(debug_slots())
