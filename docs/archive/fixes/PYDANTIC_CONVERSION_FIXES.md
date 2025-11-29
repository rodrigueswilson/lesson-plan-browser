# Pydantic Model to Dictionary Conversion Fixes

## Problem
Multiple Pydantic model objects (User, ClassSlot, PerformanceMetric) were being accessed with dictionary syntax (`.get()` or `[key]`), causing errors like:
- `'User' object has no attribute 'get'`
- `'ClassSlot' object is not subscriptable`
- `'PerformanceMetric' object has no attribute 'get'`

## Root Cause
Database methods return Pydantic SQLModel objects, but the code was treating them as dictionaries. This happened because:
1. FastAPI automatically converts Pydantic models to JSON for API responses
2. But internal Python code needs explicit conversion to dictionaries

## Fixes Applied

### 1. User Object Conversion (`batch_processor.py` lines 127-139)
**Before:**
```python
user = await asyncio.to_thread(self.db.get_user, user_id)
print(f"DEBUG: Got user: {user.get('name') if user else 'None'}")  # ERROR!
```

**After:**
```python
user_raw = await asyncio.to_thread(self.db.get_user, user_id)
if not user_raw:
    return {"success": False, "error": f"User not found: {user_id}"}

# Convert User object to dictionary
if hasattr(user_raw, 'model_dump'):
    user = user_raw.model_dump()
elif hasattr(user_raw, 'dict'):
    user = user_raw.dict()
else:
    user = dict(user_raw)
```

### 2. ClassSlot Objects Conversion (`batch_processor.py` lines 142-152)
**Before:**
```python
slots = await asyncio.to_thread(self.db.get_user_slots, user_id)
for slot in slots:
    matching_entries = [e for e in schedule_entries if e.slot_number == slot['slot_number']]  # ERROR!
```

**After:**
```python
slots_raw = await asyncio.to_thread(self.db.get_user_slots, user_id)

# Convert ClassSlot objects to dictionaries so we can enrich them
slots = []
for slot_obj in slots_raw:
    if hasattr(slot_obj, 'model_dump'):
        slot_dict = slot_obj.model_dump()
    elif hasattr(slot_obj, 'dict'):
        slot_dict = slot_obj.dict()
    else:
        slot_dict = dict(slot_obj)
    slots.append(slot_dict)
```

### 3. ClassSlot in API (`api.py` lines 1941-1949)
**Before:**
```python
slots = db.get_user_slots(batch_request.user_id)
if batch_request.slot_ids:
    slots = [slot for slot in slots if slot["id"] in batch_request.slot_ids]  # ERROR!
```

**After:**
```python
slots_raw = db.get_user_slots(batch_request.user_id)

# Convert ClassSlot objects to dictionaries for filtering
slots = []
for slot_obj in slots_raw:
    if hasattr(slot_obj, 'model_dump'):
        slots.append(slot_obj.model_dump())
    elif hasattr(slot_obj, 'dict'):
        slots.append(slot_obj.dict())
    else:
        slots.append(dict(slot_obj))
```

### 4. PerformanceMetric Objects (`database.py` line 444-450)
**Before:**
```python
def get_plan_metrics(self, plan_id: str) -> List[PerformanceMetric]:
    """Get all metrics for a weekly plan."""
    with Session(self.engine) as session:
        statement = select(PerformanceMetric).where(PerformanceMetric.plan_id == plan_id)
        return list(session.exec(statement).all())  # Returns Pydantic objects
```

**After:**
```python
def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
    """Get all metrics for a weekly plan."""
    with Session(self.engine) as session:
        statement = select(PerformanceMetric).where(PerformanceMetric.plan_id == plan_id)
        metrics = session.exec(statement).all()
        # Convert PerformanceMetric objects to dictionaries
        return [m.model_dump() if hasattr(m, 'model_dump') else m.dict() for m in metrics]
```

### 5. Same for Supabase (`supabase_database.py` line 500-512)
Updated `get_plan_metrics` to return `List[Dict[str, Any]]` instead of `List[PerformanceMetric]`

### 6. Interface Update (`database_interface.py`)
Updated abstract method signatures to match implementations:
```python
@abstractmethod
def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:  # Was List[PerformanceMetric]
    """Get all metrics for a weekly plan."""
    pass
```

### 7. Removed Dead Code (`api.py` lines 1220-1230, 1277-1287)
Removed unused Supabase-specific code that imported non-existent `_find_slot_project` function in both update and delete slot endpoints.

## Files Modified
1. `tools/batch_processor.py` - User and ClassSlot conversions
2. `backend/api.py` - ClassSlot conversion and dead code removal
3. `backend/database.py` - PerformanceMetric conversion
4. `backend/supabase_database.py` - PerformanceMetric conversion
5. `backend/database_interface.py` - Return type updates

## Pattern for Future Conversions
When working with SQLModel/Pydantic objects that need to be treated as dictionaries:

```python
# Convert single object
if hasattr(obj, 'model_dump'):
    dict_obj = obj.model_dump()
elif hasattr(obj, 'dict'):
    dict_obj = obj.dict()
else:
    dict_obj = dict(obj)

# Convert list of objects
dicts = [m.model_dump() if hasattr(m, 'model_dump') else m.dict() for m in objects]
```

## Testing
Backend has automatically reloaded with all fixes. Ready to test W47 generation.
