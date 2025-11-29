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

