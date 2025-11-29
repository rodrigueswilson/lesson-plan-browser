# CRITICAL BUG: Hyperlinks Extracted But Not Appearing in Output

## Problem Statement
Hyperlinks are successfully extracted from input DOCX files but are NOT appearing in the output DOCX files. The system processes lesson plans and should preserve hyperlinks through the entire pipeline: extraction → storage → merging → rendering.

## Evidence

### ✅ Extraction Works
Backend log shows:
```
DEBUG: _process_slot - Extracted 0 images, 16 hyperlinks
```

### ❌ Rendering Fails
Backend log does NOT show:
```
INFO: hyperlinks_restored, extra={'count': 16}
```

### ❌ Output Has Zero Hyperlinks
Running `check_single_slot_output.py` confirms:
```
TOTAL: 0 hyperlinks
```

## System Architecture

### Pipeline Flow
```
Input DOCX → Parser → lesson_json → Merger → merged_json → Renderer → Output DOCX
```

### Key Files
1. **tools/docx_parser.py** - Extracts hyperlinks with coordinates (schema v2.0)
2. **tools/batch_processor.py** - Stores hyperlinks in lesson_json
3. **tools/json_merger.py** - Merges multiple lesson JSONs (SUSPECTED BUG LOCATION)
4. **tools/docx_renderer.py** - Inserts hyperlinks into output DOCX

## Code Analysis

### 1. Parser (WORKING ✅)
File: `tools/docx_parser.py`
- Method: `extract_hyperlinks()`
- Returns: List of hyperlink dicts with coordinates
- Evidence: Log shows "Extracted 0 images, 16 hyperlinks"

### 2. Batch Processor (WORKING ✅)
File: `tools/batch_processor.py` lines 544-557
```python
# Store images and hyperlinks as metadata
if images:
    lesson_json["_images"] = images
if hyperlinks:
    print(f"🔍 BATCH_PROCESSOR DEBUG: Adding {len(hyperlinks)} hyperlinks to lesson_json")
    lesson_json["_hyperlinks"] = hyperlinks
else:
    print(f"⚠️ BATCH_PROCESSOR DEBUG: No hyperlinks extracted!")

# Set schema version for coordinate-based placement
if images or hyperlinks:
    lesson_json["_media_schema_version"] = "2.0"

return lesson_json
```

### 3. JSON Merger (SUSPECTED BUG 🔴)
File: `tools/json_merger.py` lines 83-113

**FIXED CODE:**
```python
# Collect all hyperlinks and images from all lessons
all_hyperlinks = []
all_images = []
media_schema_version = None

for lesson in lessons:
    lesson_json = lesson['lesson_json']
    
    # Collect hyperlinks
    if '_hyperlinks' in lesson_json:
        all_hyperlinks.extend(lesson_json['_hyperlinks'])
    
    # Collect images
    if '_images' in lesson_json:
        all_images.extend(lesson_json['_images'])
    
    # Get schema version (use the highest version found)
    if '_media_schema_version' in lesson_json:
        if media_schema_version is None or lesson_json['_media_schema_version'] > media_schema_version:
            media_schema_version = lesson_json['_media_schema_version']

# Add collected media to merged JSON
if all_hyperlinks:
    print(f"🔍 JSON_MERGER DEBUG: Adding {len(all_hyperlinks)} hyperlinks to merged JSON")
    merged['_hyperlinks'] = all_hyperlinks
else:
    print(f"⚠️ JSON_MERGER DEBUG: No hyperlinks found in lessons!")
if all_images:
    merged['_images'] = all_images
if media_schema_version:
    merged['_media_schema_version'] = media_schema_version
```

**Issue:** The fix was applied but hyperlinks still don't appear. Possible causes:
- Python module caching (we cleared __pycache__ but still failing)
- Backend not reloading the module
- Fix is correct but there's another bug downstream

### 4. Renderer (SHOULD WORK ✅)
File: `tools/docx_renderer.py` lines 183-190
```python
if "_hyperlinks" in json_data and json_data["_hyperlinks"]:
    if plan_id:
        with tracker.track_operation(plan_id, "render_restore_hyperlinks"):
            self._restore_hyperlinks(doc, json_data["_hyperlinks"])
            logger.info("hyperlinks_restored", extra={"count": len(json_data["_hyperlinks"])})
    else:
        self._restore_hyperlinks(doc, json_data["_hyperlinks"])
        logger.info("hyperlinks_restored", extra={"count": len(json_data["_hyperlinks"])})
```

**Evidence:** The log message "hyperlinks_restored" NEVER appears, which means:
- Either `json_data` doesn't have `"_hyperlinks"` key
- Or `json_data["_hyperlinks"]` is empty

## Debug Logging Added

We added print statements to track the flow:
1. `🔍 BATCH_PROCESSOR DEBUG: Adding X hyperlinks to lesson_json`
2. `🔍 JSON_MERGER DEBUG: Adding X hyperlinks to merged JSON`

**Expected:** Both messages should appear in backend logs
**Actual:** Need to check if these messages appear

## Test Results

### Unit Test (PASSES ✅)
File: `test_json_merger_fix.py`
```
✅ JSON MERGER FIX IS WORKING!
```
The merger correctly preserves hyperlinks when tested in isolation.

### Integration Test (FAILS ❌)
Real-world generation: 0 hyperlinks in output

## Questions for Diagnostic AI

1. **Why doesn't the backend reload the fixed code?**
   - We killed Python processes
   - We cleared __pycache__
   - We restarted the app
   - Unit test shows fix works, but production doesn't use it

2. **Is there another code path bypassing json_merger?**
   - Single-slot vs multi-slot processing
   - Check if renderer is called differently

3. **Are hyperlinks in lesson_json before merging?**
   - Need to verify batch_processor actually adds them
   - Check if LLM transform strips them

4. **Is merged_json passed correctly to renderer?**
   - Check the render() call in batch_processor
   - Verify json_data parameter

## Requested Diagnostic Scripts

Please create Python scripts to:

1. **Intercept and log lesson_json** before it goes to merger
2. **Intercept and log merged_json** after merger, before renderer
3. **Dump the actual JSON** being passed to renderer
4. **Check if backend is using old .pyc files** despite clearing cache
5. **Verify the fix is actually in the loaded module** at runtime

## Files to Analyze

All files are in `d:\LP\`:
- `tools/docx_parser.py`
- `tools/batch_processor.py`
- `tools/json_merger.py`
- `tools/docx_renderer.py`
- `backend/api.py` (API endpoints)

## Expected Behavior

Input: Morais file with 16 hyperlinks
Output: DOCX with 16 hyperlinks (100% preservation rate)

## Actual Behavior

Input: Morais file with 16 hyperlinks
Output: DOCX with 0 hyperlinks (0% preservation rate)

## System Info

- OS: Windows
- Python: 3.11
- Framework: FastAPI + Tauri
- DOCX library: python-docx

## Priority

CRITICAL - This is a production bug affecting all lesson plans with hyperlinks.
