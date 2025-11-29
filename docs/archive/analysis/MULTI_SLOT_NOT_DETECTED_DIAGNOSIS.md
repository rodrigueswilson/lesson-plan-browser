# Multi-Slot Not Detected - Diagnosis Guide

## Problem

The screenshot shows **old single-slot behavior** instead of the new multi-slot refactor:
- ❌ No bold "Slot 1 / Slot 2" headers
- ❌ Math hyperlinks in ELA cells
- ❌ Coordinate placement running (should be disabled for multi-slot)

This means the renderer is treating the document as **single-slot**, not multi-slot.

---

## Root Cause

The multi-slot detection is failing:

```python
# In docx_renderer.py line 375
if "slots" in day_data and isinstance(day_data["slots"], list):
    # Multi-slot path
    self._fill_multi_slot_day(...)
else:
    # Single-slot path (OLD BEHAVIOR)
    self._fill_single_slot_day(...)
```

**If this check returns `False`, the renderer uses the old single-slot logic.**

---

## Diagnosis Steps

### Step 1: Restart the Backend ⚠️

**CRITICAL:** FastAPI's auto-reload doesn't always work reliably.

```bash
# Stop the backend (Ctrl+C)
# Then restart:
python -m uvicorn backend.api:app --reload --port 8000
```

**Look for:**
```
✓ Cache cleared on startup
INFO: Application startup complete.
```

---

### Step 2: Check the Merged JSON Structure

The merged JSON **must** have a `slots` array for each day:

```json
{
  "days": {
    "monday": {
      "slots": [                    // ← REQUIRED for multi-slot
        {
          "slot_number": 1,
          "subject": "ELA",
          "unit_lesson": "...",
          ...
        },
        {
          "slot_number": 2,
          "subject": "Math",
          "unit_lesson": "...",
          ...
        }
      ]
    }
  }
}
```

**Run the diagnostic:**
```bash
python tools\diagnostics\check_json_structure.py output/your_merged_file.json
```

**Expected output:**
```
✓ Has 'slots' array with 2 slots
  - Slot 1: ELA
  - Slot 2: Math
```

**If you see:**
```
✗ No 'slots' array - will be treated as SINGLE-SLOT
```

Then the **JSON merger didn't create the slots structure!**

---

### Step 3: Check the JSON Merger

The `json_merger.py` is responsible for creating the `slots` array:

<function_calls>
<invoke name="read_file">
<parameter name="file_path">d:\LP\tools\json_merger.py
