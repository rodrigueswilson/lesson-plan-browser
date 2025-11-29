# CRITICAL: Backend Not Loading Fixed Code

## Problem
The backend is using **cached/old version** of `json_merger.py` even after restart.

## Root Cause
Python module caching - the backend loaded the old bytecode (.pyc) files.

## Solution

### Step 1: Kill ALL Python processes
```powershell
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

### Step 2: Delete Python cache
```powershell
Get-ChildItem -Path "d:\LP" -Include "__pycache__","*.pyc" -Recurse -Force | Remove-Item -Recurse -Force
```

### Step 3: Restart the app
```powershell
.\start-app.bat
```

### Step 4: Regenerate Morais slot

### Step 5: Verify
Run: `python check_single_slot_output.py`

Expected: **16 hyperlinks** in output

---

## What the Fix Does

The fix in `tools/json_merger.py` (lines 83-110) collects all `_hyperlinks`, `_images`, and `_media_schema_version` from individual lesson JSONs and adds them to the merged JSON so the renderer can insert them.

**Before fix:** Hyperlinks extracted but discarded during merge
**After fix:** Hyperlinks preserved and passed to renderer

---

## Alternative: Add Debug Logging

If the above doesn't work, we can add temporary logging to confirm the backend is using the new code:

Edit `tools/json_merger.py` line 106:
```python
if all_hyperlinks:
    print(f"DEBUG MERGER: Adding {len(all_hyperlinks)} hyperlinks to merged JSON")  # ADD THIS
    merged['_hyperlinks'] = all_hyperlinks
```

Then check backend logs for "DEBUG MERGER" message.
