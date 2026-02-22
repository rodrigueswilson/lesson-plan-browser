
import asyncio
from backend.database import get_db

async def check_schedule():
    db = get_db()
    # User ID from previous context: 04fe8898-cb89-4a73-affb-64a99a98f820
    user_id = "04fe8898-cb89-4a73-affb-64a99a98f820"
    
    entries = await asyncio.to_thread(db.get_user_schedule, user_id)
    
    print(f"Schedule entries for user {user_id}:")
    for e in entries:
        print(f"Day: {e.day_of_week}, Slot: {e.slot_number}, Subject: {e.subject}, Time: {e.start_time} - {e.end_time}, Active: {e.is_active}")

if __name__ == "__main__":
    asyncio.run(check_schedule())
