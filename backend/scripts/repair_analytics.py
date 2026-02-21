import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Load env vars
load_dotenv(project_root / ".env")

from backend.config import settings

# Force DB path to be relative to project root, not CWD
settings.SQLITE_DB_PATH = project_root / "data" / "lesson_planner.db"
settings.DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"

from backend.database import get_db
from backend.performance_tracker import get_tracker

def repair_analytics():
    print("Starting analytics repair...")
    print(f"DB Path: {settings.SQLITE_DB_PATH}")
    db = get_db()
    tracker = get_tracker()
    
    # Get all plans
    plans = db.get_user_plans("user_20241029153011", limit=100) # Using a likely user ID or just generic fetch if possible
    # Wait, get_user_plans requires user_id. 
    # Let's use get_session_breakdown to get all plans instead, which iterates plans.
    # Actually, let's just use SQLModel directly to get all plans if possible, or use a known user_id.
    # The previous analytics output showed stats, so data exists.
    # The user_id is likely passed in context or I can find it.
    # In 'task.md' I saw "user_id" mentioned in contexts.
    # Let's try to fetch all users and iterate.
    
    users = db.list_users()
    print(f"Found {len(users)} users.")
    
    total_updated = 0
    
    for user in users:
        print(f"Checking plans for user {user.id} ({user.name})...")
        plans = db.get_user_plans(user.id)
        
        for plan in plans:
            print(f"  Processing plan {plan.id}...")
            if tracker.update_plan_summary(plan.id):
                print(f"    -> Updated summary for plan {plan.id}")
                total_updated += 1
            else:
                print(f"    -> No metrics found or update failed for plan {plan.id}")
                
    print(f"Repair complete. Updated {total_updated} plans.")

if __name__ == "__main__":
    repair_analytics()
