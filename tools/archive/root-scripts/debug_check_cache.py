import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db
from tools.batch_processor import BatchProcessor

# Force encoding
sys.stdout.reconfigure(encoding='utf-8')

USER_ID = "29fa9ed7-3174-4999-86fd-40a542c28cff"

async def main():
    print(f"Checking cache for user: {USER_ID}")
    db = get_db(user_id=USER_ID)
    
    # 1. Get All Plans
    plans = await asyncio.to_thread(db.get_user_plans, USER_ID, limit=10)
    print(f"\nFound {len(plans)} plans:")
    
    target_plan = None
    for p in plans:
        print(f"  - ID: {p.id}, Week: {p.week_of}")
        if "12-30" in p.week_of or "12/30" in p.week_of or "01-03" in p.week_of:
            target_plan = p
            
    if target_plan:
        latest_plan = target_plan
        print(f"\nTargeting plan: {latest_plan.id} ({latest_plan.week_of})")
    else:
        print("\nNo plan found for week of Dec 30. Using first available.")
        latest_plan = plans[0] if plans else None
        
    if not latest_plan:
        print("No plans found.")
        return

    print(f"\nFound plan: {latest_plan.id}")
    print(f"    Week: {latest_plan.week_of}")
    print(f"    Created: {getattr(latest_plan, 'generated_at', getattr(latest_plan, 'created_at', 'N/A'))}")
    print(f"    Status: {latest_plan.status}")
    
    plans = [latest_plan] # To keep compatible with loop below (logic adjustment needed)
    week_of = latest_plan.week_of
    print(f"\nAnalyzing latest plan: {latest_plan.id} ({week_of})")
    
    # 2. Check Slots
    slots = await asyncio.to_thread(db.get_user_slots, USER_ID)
    print(f"Found {len(slots)} slots.")
    
    # 3. Check All Slots
    for slot in slots:
        slot_num = getattr(slot, 'slot_number', 0)
        subject = getattr(slot, 'subject', 'N/A')
        print(f"\n[{slot_num}] Checking Slot: {subject}")
        
        # Resolve file
        bp = BatchProcessor(llm_service=None) # Mock LLM service
        # Need to convert slot to dict potentially
        slot_dict = slot.dict() if hasattr(slot, 'dict') else slot.model_dump() if hasattr(slot, 'model_dump') else dict(slot)

        # Mock user dict
        user = db.get_user(USER_ID)
        user_dict = user.dict() if hasattr(user, 'dict') else user.model_dump()
        
        primary_file = bp._resolve_primary_file(slot_dict, week_of, None, user_dict.get('base_path'))
        print(f"    Resolved Primary File: {primary_file}")
        
        if not primary_file or not Path(primary_file).exists():
            print("    Primary file does not exist.")
        else:
            mtime = Path(primary_file).stat().st_mtime
            print(f"    File mtime: {timestamp_to_str(mtime)} ({mtime})")
            
            # Check OriginalLessonPlan
            original = await asyncio.to_thread(db.get_original_lesson_plan, USER_ID, week_of, slot_num)
            if original:
                print(f"    OriginalLessonPlan found in DB.")
                print(f"      Extracted At: {original.extracted_at} ({original.extracted_at.timestamp()})")
                print(f"      Source File: {original.source_file_path}")
                
                # Check correctness of cache logic
                cutoff = mtime + 2
                is_cache_hit = original.extracted_at.timestamp() > cutoff
                print(f"      Check: {original.extracted_at.timestamp()} > {cutoff}?")
                print(f"      Cache Hit Result: {is_cache_hit}")
                
            else:
                print("    OriginalLessonPlan NOT found in DB.")
                
        # 4. Check Existing Transformed Plan content
        import json
        existing_json = latest_plan.lesson_json
        if isinstance(existing_json, str):
            try:
                existing_json = json.loads(existing_json)
            except:
                existing_json = {}
            
        if existing_json:
            reconstructed = bp._reconstruct_slots_from_json(existing_json)
            if slot_num in reconstructed:
                print(f"    Slot {slot_num} found in existing JSON.")
            else:
                print(f"    Slot {slot_num} NOT found in existing JSON.")
        else:
            print("    WeeklyPlan.lesson_json is empty.")

def timestamp_to_str(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    asyncio.run(main())
