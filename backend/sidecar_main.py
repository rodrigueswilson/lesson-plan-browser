#!/usr/bin/env python3
"""
Python Sidecar Entry Point for Tauri IPC.
Runs as subprocess, communicates via stdin/stdout JSON.
"""

import json
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Configure logging to stderr (stdout is for IPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

from backend.ipc_database import IPCDatabaseAdapter
from backend.supabase_database import SupabaseDatabase
from backend.schema import User, ClassSlot, WeeklyPlan


class SyncSidecar:
    """Main sidecar process handler."""
    
    def __init__(self):
        self.local_db = IPCDatabaseAdapter()
        self.remote_db: Optional[SupabaseDatabase] = None
        self._running = True
    
    def _init_supabase(self) -> bool:
        """Initialize Supabase connection."""
        try:
            self.remote_db = SupabaseDatabase()
            return True
        except Exception as e:
            logger.warning(f"Supabase not available: {e}")
            return False
    
    def handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route and handle incoming commands."""
        command = message.get("command")
        request_id = message.get("request_id", "unknown")
        user_id = message.get("user_id")
        
        try:
            if command == "full_sync":
                result = self.full_sync(user_id)
            elif command == "sync_pull":
                result = self.sync_from_supabase(user_id)
            elif command == "sync_push":
                result = self.sync_to_supabase(user_id)
            elif command == "health_check":
                result = {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
            elif command == "shutdown":
                self._running = False
                result = {"status": "shutting_down"}
            else:
                return {"type": "response", "request_id": request_id, "status": "error", "error": f"Unknown: {command}"}
            
            return {"type": "response", "request_id": request_id, "status": "success", "data": result}
            
        except Exception as e:
            logger.exception(f"Error handling {command}")
            return {"type": "response", "request_id": request_id, "status": "error", "error": str(e)}
    
    def sync_from_supabase(self, user_id: str) -> Dict:
        """Pull data from Supabase to local SQLite."""
        if not self.remote_db and not self._init_supabase():
            raise Exception("Supabase not configured")
        
        synced = 0
        errors = []
        
        try:
            # Sync users (all users, not just current user)
            users = self.remote_db.list_users()  # Use list_users() method
            for user in users:
                try:
                    self.local_db.execute(
                        """INSERT OR REPLACE INTO users 
                           (id, first_name, last_name, email, name, created_at, updated_at, sync_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 'synced')""",
                        [
                            user.id, 
                            user.first_name, 
                            user.last_name, 
                            user.email,
                            getattr(user, 'name', None) or f"{user.first_name} {user.last_name}".strip(),
                            user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at),
                            user.updated_at.isoformat() if hasattr(user.updated_at, 'isoformat') else str(user.updated_at)
                        ]
                    )
                    synced += 1
                except Exception as e:
                    logger.error(f"Failed to sync user {user.id}: {e}")
                    errors.append(f"User {user.id}: {str(e)}")
            
            # Sync class slots for user
            if user_id:
                slots = self.remote_db.get_user_slots(user_id)
                for slot in slots:
                    try:
                        self.local_db.execute(
                            """INSERT OR REPLACE INTO class_slots
                               (id, user_id, slot_number, subject, grade, homeroom,
                                proficiency_levels, created_at, updated_at, sync_status)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced')""",
                            [
                                slot.id, 
                                slot.user_id, 
                                slot.slot_number, 
                                slot.subject,
                                slot.grade, 
                                slot.homeroom,
                                getattr(slot, 'proficiency_levels', None),
                                slot.created_at.isoformat() if hasattr(slot.created_at, 'isoformat') else str(slot.created_at),
                                slot.updated_at.isoformat() if hasattr(slot.updated_at, 'isoformat') else str(slot.updated_at)
                            ]
                        )
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to sync slot {slot.id}: {e}")
                        errors.append(f"Slot {slot.id}: {str(e)}")
        except Exception as e:
            logger.exception("Sync from Supabase failed")
            raise Exception(f"Sync failed: {str(e)}")
        
        return {
            "synced_count": synced, 
            "direction": "pull",
            "errors": errors if errors else None
        }
    
    def sync_to_supabase(self, user_id: str) -> Dict:
        """Push pending local changes to Supabase."""
        if not self.remote_db and not self._init_supabase():
            raise Exception("Supabase not configured")
        
        # Get pending plans (check for sync_status column, default to all if missing)
        try:
            pending = self.local_db.query(
                "SELECT * FROM weekly_plans WHERE user_id = ? AND (sync_status IS NULL OR sync_status != 'synced')",
                [user_id]
            )
        except Exception:
            # Fallback if sync_status column doesn't exist yet
            pending = self.local_db.query(
                "SELECT * FROM weekly_plans WHERE user_id = ?",
                [user_id]
            )
        
        synced = 0
        conflicts = []
        
        for plan_data in pending:
            try:
                # Convert dict to WeeklyPlan object
                # Handle JSON fields that might be strings
                if isinstance(plan_data.get('lesson_json'), str):
                    plan_data['lesson_json'] = json.loads(plan_data['lesson_json'])
                
                plan = WeeklyPlan(**plan_data)
                
                # Check if plan exists in Supabase
                existing = self.remote_db.get_weekly_plan(plan.id)
                if existing:
                    # Update existing plan
                    self.remote_db.update_weekly_plan(
                        plan.id,
                        status=plan.status,
                        output_file=plan.output_file,
                        error_message=plan.error_message,
                        lesson_json=plan.lesson_json
                    )
                else:
                    # Create new plan
                    self.remote_db.create_weekly_plan(
                        user_id=plan.user_id,
                        week_of=plan.week_of,
                        output_file=plan.output_file or "",
                        week_folder_path=plan.week_folder_path or "",
                        consolidated=bool(plan.consolidated),
                        total_slots=plan.total_slots
                    )
                    # Update with lesson_json if present
                    if plan.lesson_json:
                        self.remote_db.update_weekly_plan(
                            plan.id,
                            lesson_json=plan.lesson_json
                        )
                
                # Update sync status if column exists
                try:
                    self.local_db.execute(
                        "UPDATE weekly_plans SET sync_status = 'synced' WHERE id = ?",
                        [plan.id]
                    )
                except Exception:
                    # Column might not exist, that's okay
                    pass
                
                synced += 1
            except Exception as e:
                logger.error(f"Failed to sync plan {plan_data.get('id')}: {e}")
                conflicts.append({
                    "id": plan_data.get("id", "unknown"), 
                    "error": str(e)
                })
        
        return {
            "synced_count": synced, 
            "conflicts": conflicts if conflicts else None, 
            "direction": "push"
        }
    
    def full_sync(self, user_id: str) -> Dict:
        """Bidirectional sync."""
        pull = self.sync_from_supabase(user_id)
        push = self.sync_to_supabase(user_id)
        return {"pulled": pull["synced_count"], "pushed": push["synced_count"]}
    
    def run(self):
        """Main event loop."""
        logger.info("Sidecar started")
        
        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                message = json.loads(line)
                response = self.handle_command(message)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.exception("Error in main loop")
        
        logger.info("Sidecar shutdown")


def main():
    SyncSidecar().run()


if __name__ == "__main__":
    main()

