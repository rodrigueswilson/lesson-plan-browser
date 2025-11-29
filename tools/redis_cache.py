"""
Using Redis for caching slot data and managing state.
Improves consistency and performance across processing runs.
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Would need: pip install redis
import redis
from redis.exceptions import RedisError

from backend.config import settings


class SlotCacheManager:
    """Manages caching of slot data using Redis."""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(
            redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=False  # We'll handle encoding ourselves
        )
    
    def cache_parsed_content(
        self,
        user_id: str,
        slot_id: str,
        file_path: str,
        content: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """Cache parsed slot content."""
        try:
            key = f"slot_content:{user_id}:{slot_id}"
            
            cache_data = {
                "file_path": file_path,
                "file_mtime": Path(file_path).stat().st_mtime if Path(file_path).exists() else 0,
                "content": content,
                "cached_at": datetime.now().isoformat()
            }
            
            # Use pickle for complex data structures
            serialized = pickle.dumps(cache_data)
            
            self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                serialized
            )
            
            return True
            
        except (RedisError, pickle.PickleError, FileNotFoundError) as e:
            print(f"Cache write failed: {e}")
            return False
    
    def get_cached_content(
        self,
        user_id: str,
        slot_id: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached content if still valid."""
        try:
            key = f"slot_content:{user_id}:{slot_id}"
            serialized = self.redis_client.get(key)
            
            if not serialized:
                return None
            
            cache_data = pickle.loads(serialized)
            
            # Check if file has been modified
            current_mtime = Path(file_path).stat().st_mtime if Path(file_path).exists() else 0
            if current_mtime != cache_data["file_mtime"]:
                # File changed, invalidate cache
                self.redis_client.delete(key)
                return None
            
            return cache_data["content"]
            
        except (RedisError, pickle.PickleError, FileNotFoundError) as e:
            print(f"Cache read failed: {e}")
            return None
    
    def cache_processing_state(
        self,
        plan_id: str,
        state: Dict[str, Any],
        ttl_minutes: int = 30
    ) -> bool:
        """Cache processing state for progress tracking."""
        try:
            key = f"processing_state:{plan_id}"
            
            state_data = {
                "state": state,
                "updated_at": datetime.now().isoformat()
            }
            
            self.redis_client.setex(
                key,
                timedelta(minutes=ttl_minutes),
                json.dumps(state_data, default=str)
            )
            
            return True
            
        except (RedisError, json.JSONDecodeError) as e:
            print(f"State cache failed: {e}")
            return False
    
    def get_processing_state(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get cached processing state."""
        try:
            key = f"processing_state:{plan_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            print(f"State cache read failed: {e}")
            return None
    
    def cache_slot_mapping(
        self,
        user_id: str,
        file_path: str,
        slot_mappings: Dict[int, int],  # requested_slot -> actual_slot
        ttl_hours: int = 168  # 1 week
    ) -> bool:
        """Cache slot number mappings for a file."""
        try:
            key = f"slot_mapping:{user_id}:{hash(file_path)}"
            
            mapping_data = {
                "file_path": file_path,
                "file_mtime": Path(file_path).stat().st_mtime if Path(file_path).exists() else 0,
                "mappings": slot_mappings,
                "cached_at": datetime.now().isoformat()
            }
            
            self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                json.dumps(mapping_data, default=str)
            )
            
            return True
            
        except (RedisError, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Mapping cache failed: {e}")
            return False
    
    def get_cached_slot_mapping(
        self,
        user_id: str,
        file_path: str
    ) -> Optional[Dict[int, int]]:
        """Get cached slot mappings."""
        try:
            key = f"slot_mapping:{user_id}:{hash(file_path)}"
            data = self.redis_client.get(key)
            
            if not data:
                return None
            
            mapping_data = json.loads(data)
            
            # Check if file has been modified
            current_mtime = Path(file_path).stat().st_mtime if Path(file_path).exists() else 0
            if current_mtime != mapping_data["file_mtime"]:
                # File changed, invalidate cache
                self.redis_client.delete(key)
                return None
            
            return mapping_data["mappings"]
            
        except (RedisError, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Mapping cache read failed: {e}")
            return None
    
    def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cached data for a user."""
        try:
            # Find all keys for this user
            pattern1 = f"slot_content:{user_id}:*"
            pattern2 = f"slot_mapping:{user_id}:*"
            
            keys = []
            keys.extend(self.redis_client.keys(pattern1))
            keys.extend(self.redis_client.keys(pattern2))
            
            if keys:
                self.redis_client.delete(*keys)
            
            return True
            
        except RedisError as e:
            print(f"Cache clear failed: {e}")
            return False


# Integration example with BatchProcessor:
class CachedBatchProcessor(BatchProcessor):
    """BatchProcessor with Redis caching."""
    
    def __init__(self, llm_service, redis_url: str = None):
        super().__init__(llm_service)
        self.cache = SlotCacheManager(redis_url)
    
    async def _process_slot(self, slot: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process slot with caching."""
        
        # Resolve file path
        file_path = self._resolve_primary_file(slot, kwargs.get("week_of"))
        
        if not file_path:
            raise ValueError(f"No file found for slot {slot['slot_number']}")
        
        # Check cache first
        user_id = kwargs.get("user_id", "unknown")
        cached_content = self.cache.get_cached_content(user_id, slot["id"], file_path)
        
        if cached_content:
            print(f"✅ Using cached content for slot {slot['slot_number']}")
            return cached_content
        
        # Parse and process normally
        parser = DOCXParser(file_path)
        
        # Check for cached slot mapping
        cached_mapping = self.cache.get_cached_slot_mapping(user_id, file_path)
        if cached_mapping and slot["slot_number"] in cached_mapping:
            actual_slot_num = cached_mapping[slot["slot_number"]]
        else:
            actual_slot_num = parser.find_slot_by_subject(slot["subject"])
            # Cache the mapping
            self.cache.cache_slot_mapping(
                user_id, file_path, {slot["slot_number"]: actual_slot_num}
            )
        
        content = parser.extract_subject_content_for_slot(
            actual_slot_num, slot["subject"]
        )
        
        # Cache the parsed content
        self.cache.cache_parsed_content(user_id, slot["id"], file_path, content)
        
        # Continue with LLM transformation...
        # (rest of the processing logic)
        
        return content
