import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from backend.config import settings
from backend.telemetry import logger

class DatabaseMaintenance:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self.archive_dir = self.db_path.parent / "archives"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> str:
        """Create a timestamped backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.archive_dir / f"lesson_planner_backup_{timestamp}.db"
        
        logger.info(f"Creating database backup at {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        return str(backup_path)

    def cleanup_users(self) -> int:
        """Remove invalid 'password' users."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE name = 'password'")
        users_to_delete = [row[0] for row in cursor.fetchall()]
        
        if users_to_delete:
            logger.info(f"Deleting {len(users_to_delete)} 'password' users")
            # Also delete their plans and schedules to maintain integrity
            placeholders = ",".join("?" for _ in users_to_delete)
            cursor.execute(f"DELETE FROM schedules WHERE user_id IN ({placeholders})", users_to_delete)
            cursor.execute(f"DELETE FROM weekly_plans WHERE user_id IN ({placeholders})", users_to_delete)
            cursor.execute(f"DELETE FROM class_slots WHERE user_id IN ({placeholders})", users_to_delete)
            cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", users_to_delete)
            
        conn.commit()
        count = len(users_to_delete)
        conn.close()
        return count

    def prune_plans(self) -> Tuple[int, int]:
        """
        Prune redundant weekly plans.
        Keeps only the latest 'completed' plan for each user and week.
        Returns (completed_deleted, others_deleted).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all users and their weeks
        cursor.execute("SELECT DISTINCT user_id, week_of FROM weekly_plans")
        targets = cursor.fetchall()
        
        completed_deleted = 0
        others_deleted = 0
        
        for target in targets:
            uid, week = target['user_id'], target['week_of']
            
            # 1. Get all completed plans for this user/week, sorted by generated_at desc
            cursor.execute(
                "SELECT id FROM weekly_plans WHERE user_id = ? AND week_of = ? AND status = 'completed' ORDER BY generated_at DESC",
                (uid, week)
            )
            completed = [row[0] for row in cursor.fetchall()]
            
            # Keep the first one (latest), delete the rest
            if len(completed) > 1:
                to_delete = completed[1:]
                completed_deleted += len(to_delete)
                placeholders = ",".join("?" for _ in to_delete)
                # Delete lesson steps first
                cursor.execute(f"DELETE FROM lesson_steps WHERE lesson_plan_id IN ({placeholders})", to_delete)
                cursor.execute(f"DELETE FROM weekly_plans WHERE id IN ({placeholders})", to_delete)
            
            # 2. Delete all non-completed plans for this user/week (failed, pending, processing)
            # UNLESS there are NO completed plans (maybe keep the latest failed for debugging? No, user wants cleanup)
            cursor.execute(
                "SELECT id FROM weekly_plans WHERE user_id = ? AND week_of = ? AND status != 'completed'",
                (uid, week)
            )
            others = [row[0] for row in cursor.fetchall()]
            if others:
                others_deleted += len(others)
                placeholders = ",".join("?" for _ in others)
                cursor.execute(f"DELETE FROM lesson_steps WHERE lesson_plan_id IN ({placeholders})", others)
                cursor.execute(f"DELETE FROM weekly_plans WHERE id IN ({placeholders})", others)
                
        conn.commit()
        conn.close()
        return completed_deleted, others_deleted

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        stats['db_size_kb'] = os.path.getsize(self.db_path) // 1024
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weekly_plans")
        stats['total_plans'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weekly_plans WHERE status = 'completed'")
        stats['completed_plans'] = cursor.fetchone()[0]
        
        # Get last backup date
        backups = sorted(list(self.archive_dir.glob("lesson_planner_backup_*.db")))
        if backups:
            stats['last_backup'] = datetime.fromtimestamp(backups[-1].stat().st_mtime).isoformat()
        else:
            stats['last_backup'] = None
            
        conn.close()
        return stats

def run_maintenance() -> Dict[str, Any]:
    """Execute full maintenance and return results."""
    m = DatabaseMaintenance()
    
    # 1. Backup
    backup_file = m.create_backup()
    
    # 2. Cleanup
    users_deleted = m.cleanup_users()
    comp_deleted, other_deleted = m.prune_plans()
    
    # 3. New stats
    stats = m.get_stats()
    
    return {
        "success": True,
        "backup_file": backup_file,
        "users_deleted": users_deleted,
        "redundant_plans_deleted": comp_deleted,
        "failed_plans_deleted": other_deleted,
        "stats": stats
    }
