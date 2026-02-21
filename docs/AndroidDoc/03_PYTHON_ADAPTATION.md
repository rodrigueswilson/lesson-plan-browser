# Phase 3: Python Sidecar Adaptation

## 3.1 IPC Database Adapter

**File:** `backend/ipc_database.py`

```python
"""
Drop-in replacement for SQLiteDatabase that routes SQL through Rust IPC.
Implements critical methods first, then expands to full DatabaseInterface.
"""

import json
import sys
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class IPCDatabaseAdapter:
    """Routes database calls to Rust via stdin/stdout IPC."""
    
    def __init__(self):
        self._request_id = 0
    
    def _ipc_call(self, msg_type: str, sql: str, params: List = None) -> Any:
        """Send SQL request to Rust, receive response."""
        self._request_id += 1
        request_id = str(self._request_id)
        
        request = {
            "type": msg_type,
            "request_id": request_id,
            "sql": sql,
            "params": params or []
        }
        
        try:
            # stdout -> Rust reads this
            print(json.dumps(request), flush=True)
            
            # stdin <- Rust writes response here
            response_line = sys.stdin.readline()
            if not response_line:
                raise IOError("No response from Rust bridge (EOF)")
            
            response_line = response_line.strip()
            if not response_line:
                raise IOError("Empty response from Rust bridge")
            
            response = json.loads(response_line)
            
            # Verify request_id matches
            if response.get("request_id") != request_id:
                logger.warning(f"Request ID mismatch: expected {request_id}, got {response.get('request_id')}")
            
            if response.get("status") == "error":
                error_msg = response.get("error", "Unknown IPC error")
                raise Exception(f"IPC error: {error_msg}")
            
            return response.get("data")
            
        except json.JSONDecodeError as e:
            raise IOError(f"Invalid JSON response from Rust: {e}")
        except Exception as e:
            logger.error(f"IPC call failed: {e}")
            raise
    
    def execute(self, sql: str, params: List = None) -> Dict:
        """Execute INSERT/UPDATE/DELETE via Rust."""
        return self._ipc_call("sql_execute", sql, params)
    
    def query(self, sql: str, params: List = None) -> List[Dict]:
        """Execute SELECT via Rust."""
        return self._ipc_call("sql_query", sql, params)
    
    def query_one(self, sql: str, params: List = None) -> Optional[Dict]:
        """Execute SELECT expecting single row."""
        rows = self.query(sql, params)
        return rows[0] if rows else None
```

**Implementation Strategy:**
- Start with critical methods: `get_user`, `get_user_slots`, `create_weekly_plan`, `get_weekly_plan`
- Expand to full `DatabaseInterface` as needed
- Each method translates SQLModel operations to raw SQL queries

## 3.2 Sidecar Entry Point

**File:** `backend/sidecar_main.py`

```python
#!/usr/bin/env python3
"""
Python Sidecar Entry Point for Tauri IPC.
Runs as subprocess, communicates via stdin/stdout JSON.
"""

import json
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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
                result = {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
            elif command == "shutdown":
                self._running = False
                result = {"status": "shutting_down"}
            else:
                return {"request_id": request_id, "status": "error", "error": f"Unknown: {command}"}
            
            return {"request_id": request_id, "status": "success", "data": result}
            
        except Exception as e:
            logger.exception(f"Error handling {command}")
            return {"request_id": request_id, "status": "error", "error": str(e)}
    
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
                    import json
                    plan_data['lesson_json'] = json.loads(plan_data['lesson_json'])
                
                plan = WeeklyPlan(**plan_data)
                self.remote_db.save_weekly_plan(plan)
                
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
```

## 3.3 Modify Existing Database Class

**File:** `backend/database.py` (modifications)

```python
# Add to __init__ method:

class SQLiteDatabase(DatabaseInterface):
    def __init__(self, use_ipc: bool = False):
        """
        Initialize database.
        
        Args:
            use_ipc: If True, route SQL through Rust IPC (for Android sidecar mode)
        """
        self.use_ipc = use_ipc
        
        if use_ipc:
            from backend.ipc_database import IPCDatabaseAdapter
            self._adapter = IPCDatabaseAdapter()
        else:
            # Existing SQLAlchemy setup
            self.db_path = settings.SQLITE_DB_PATH
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            sqlite_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID - works in both modes."""
        if self.use_ipc:
            row = self._adapter.query_one(
                "SELECT * FROM users WHERE id = ?", [user_id]
            )
            return User(**row) if row else None
        else:
            # Existing SQLAlchemy implementation
            with self.get_session() as session:
                return session.exec(select(User).where(User.id == user_id)).first()
    
    # Similar pattern for all other methods...
```

## 3.4 IPC Message Protocol

### Command Flow (Rust → Python)

```json
{
    "type": "command",
    "command": "full_sync",
    "request_id": "uuid-string",
    "user_id": "user-uuid"
}
```

### SQL Request (Python → Rust)

```json
{
    "type": "sql_query",
    "request_id": "req_1",
    "sql": "SELECT * FROM users WHERE id = ?",
    "params": ["user-uuid"]
}
```

### SQL Response (Rust → Python)

```json
{
    "request_id": "req_1",
    "status": "success",
    "data": [{"id": "...", "first_name": "..."}]
}
```

### Final Response (Python → Rust)

```json
{
    "type": "response",
    "request_id": "uuid-string",
    "status": "success",
    "data": {"pulled": 5, "pushed": 2}
}
```
