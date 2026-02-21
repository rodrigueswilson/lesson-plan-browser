
import logging
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the parent directory to sys.path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def cleanup_duplicates(dry_run=False):
    """
    Identifies and removes duplicate weekly plans, keeping only the most recent one
    for each user and week.
    """
    logger.info("Starting database cleanup...")
    if dry_run:
        logger.info("[DRY RUN] No changes will be made.")

    db = get_db()
    logger.info(f"Connected to database: {type(db).__name__}")

    try:
        # Fetch ALL plans content (might be heavy, but necessary for grouping)
        # Assuming get_all_weekly_plans exists or we can query directly.
        # If not, we might need to iterate users.
        # Let's check available methods. db.get_all_users() might be needed.
        
        # Strategy:
        # 1. Get all users
        # 2. For each user, get all their plans
        # 3. Group by week_of
        # 4. Sort by generated_at desc
        # 5. Collect IDs to delete
        
        # Note: If db interface doesn't support get_all_users, we can try a raw query if it's SQLite,
        # or just list plans if there's a method. 
        # Checking backend/database.py... assume get_users or list_users exists.
        
        # Actually API endpoint /users exists, so db must have a way.
        # Let's try to query the users table directly using the connector if available,
        # or check if there is a get_users method.
        # For safety, I'll rely on what I know exists: get_weekly_plans(user_id)
        
        users = []
        if hasattr(db, "get_users"):
             users = db.get_users()
        elif hasattr(db, "list_users"):
             users = db.list_users()
        else:
            # Fallback for Supabase/SQLite specific raw queries if needed
            # But let's assume we can get a list of users or just get *all* plans.
            # If get_all_weekly_plans exists, that's best.
            pass
            
        # Since I can't check the DB interface right now without a tool call, 
        # verifying the interface first would be prudent. 
        # But I'll write a generic loop structure and we can refine.
        
        # Wait, the sync script uses `list_local_plan_ids` which does a raw query on SQLite.
        # If using Supabase, `get_weekly_plans(user_id)` is standard.
        
        from sqlmodel import select
        from backend.schema import User
        
        # Use a session to get users directly
        all_users = []
        try:
             with db.get_connection() as session:
                 all_users = session.exec(select(User)).all()
                 logger.info(f"Found {len(all_users)} users.")
        except AttributeError:
             # If db doesn't support get_connection() context manager (e.g. SupabaseDatabase might differ)
             # fall back to get_users or list_users
             logger.warning("get_connection() not available, trying list_users/get_users")
             if hasattr(db, "get_users"):
                  all_users = db.get_users()
             elif hasattr(db, "list_users"):
                  all_users = db.list_users()
             else:
                  logger.error("Could not fetch users. Database interface unknown.")
                  return

        total_deleted = 0
        total_kept = 0
        
        for user in all_users:
            user_id = user.id
            if not user_id: 
                continue
                
            logger.info(f"Checking plans for user: {user.email or user_id}")
            
            from backend.schema import WeeklyPlan
            plans = []
            try:
                with db.get_connection() as session:
                    plans = session.exec(select(WeeklyPlan).where(WeeklyPlan.user_id == user_id)).all()
            except Exception as e:
                logger.error(f"Failed to fetch plans for user {user_id}: {e}")
                continue
                
            if not plans:
                continue

            # Group by week
            plans_by_week = defaultdict(list)
            for plan in plans:
                week = plan.week_of
                if week:
                    plans_by_week[week].append(plan)
            
            for week, week_plans in plans_by_week.items():
                if len(week_plans) <= 1:
                    total_kept += len(week_plans)
                    continue
                
                # Sort by generated_at descending (latest first)
                # Handle potential None generated_at
                week_plans.sort(key=lambda x: x.generated_at or datetime.min, reverse=True)
                
                latest_plan = week_plans[0]
                to_delete = week_plans[1:]
                
                logger.info(f"  Week {week}: Found {len(week_plans)} plans. Keeping {latest_plan.id} ({latest_plan.generated_at})")
                
                for plan_to_remove in to_delete:
                    pid = plan_to_remove.id
                    logger.info(f"    Deleting duplicate: {pid} ({plan_to_remove.generated_at})")
                    if not dry_run:
                        try:
                            with db.get_connection() as session:
                                # We need to fetch the object in the session to delete it
                                p = session.get(WeeklyPlan, pid)
                                if p:
                                    session.delete(p)
                                    session.commit()
                                    total_deleted += 1
                                else:
                                    logger.warning(f"    Plan {pid} not found for deletion.")
                        except Exception as e:
                            logger.error(f"    Failed to delete {pid}: {e}")
                
                total_kept += 1

        logger.info("="*30)
        logger.info(f"Cleanup Complete.")
        logger.info(f"Total Plans Kept: {total_kept}")
        logger.info(f"Total Plans Deleted: {total_deleted}")
        logger.info("="*30)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    # Check for --dry-run flag
    is_dry_run = "--dry-run" in sys.argv
    cleanup_duplicates(dry_run=is_dry_run)
