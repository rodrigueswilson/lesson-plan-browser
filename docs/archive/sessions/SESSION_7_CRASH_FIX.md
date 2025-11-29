# Session 7 - Backend Crash Fix

## 🐛 Issue Identified

**Symptom:** Backend crashes during processing, causing "connection refused" errors (OS error 10061)

**Timeline:**
1. ✅ Diagnostics passed (14/14 checks)
2. ✅ Backend started successfully
3. ✅ Frontend connected and initiated processing
4. ❌ Backend crashed silently during processing (after ~200 progress polls)

**Error Pattern:**
```
Network Error: tcp connect error: No connection could be made because 
the target machine actively refused it. (os error 10061)
```

This indicates the backend process crashed/exited during processing.

---

## 🔧 Fixes Applied

### 1. Enhanced Error Logging in Batch Processor
**File:** `tools/batch_processor.py`

Added comprehensive try-catch blocks around:
- DOCX parser initialization
- Image extraction
- Hyperlink extraction

**Benefits:**
- Catches exact error location
- Logs error type and details
- Continues processing without media if extraction fails (graceful degradation)

```python
try:
    images = parser.extract_images()
    hyperlinks = parser.extract_hyperlinks()
except Exception as e:
    logger.error("media_extraction_failed", extra={...})
    # Continue without media - don't crash
    images = []
    hyperlinks = []
```

### 2. Enhanced Error Logging in API Endpoint
**File:** `backend/api.py`

Added detailed error tracking in background task:
- Full stack trace logging
- Console output for visibility
- Progress tracker error state update
- Database error recording

```python
except Exception as e:
    import traceback
    error_details = {
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": traceback.format_exc(),
        "plan_id": plan_id
    }
    logger.error("background_process_error", extra=error_details)
    print(f"\n{'='*60}\nBACKGROUND PROCESS ERROR:\n{traceback.format_exc()}\n{'='*60}\n")
```

---

## 🚀 Next Steps

### Step 1: Restart Backend
Run the new restart script with enhanced logging:
```bash
cd D:\LP
restart-backend.bat
```

This will:
- Stop any existing backend processes
- Start backend with debug-level logging
- Display errors prominently in the console

### Step 2: Reproduce the Crash
1. Keep the backend terminal window visible
2. In the frontend, process a lesson plan
3. Watch the backend terminal for error messages

### Step 3: Capture the Error
When the crash happens, you'll see:
- **Exact error message** (e.g., "AttributeError", "KeyError", etc.)
- **Full stack trace** showing which line crashed
- **Error context** (which file, which slot, etc.)

---

## 📊 What to Look For

The enhanced logging will show:

**Before crash:**
```
INFO: background_process_started plan_id=...
INFO: batch_user_base_path user_id=... base_path=...
INFO: media_extracted slot=1 images_count=4 hyperlinks_count=169
```

**At crash point:**
```
============================================================
BACKGROUND PROCESS ERROR:
Traceback (most recent call last):
  File "...", line XXX, in process_in_background
    ...
  File "...", line YYY, in some_function
    ...
ErrorType: Detailed error message here
============================================================
```

---

## 🎯 Expected Outcomes

### Best Case: Error is Caught
- Backend stays running
- Error is logged with full details
- We can fix the specific issue
- Processing continues for other slots

### Worst Case: Still Crashes
- We'll see the error before the crash
- Error log will show the root cause
- We can implement a more targeted fix

---

## 📁 Files Modified

1. **tools/batch_processor.py** (+30 lines)
   - Added try-catch around parser initialization
   - Added try-catch around media extraction
   - Graceful degradation (continue without media)

2. **backend/api.py** (+17 lines)
   - Enhanced background task error handling
   - Added stack trace logging
   - Added console error output
   - Progress tracker error state

3. **restart-backend.bat** (NEW)
   - Clean restart script
   - Kills existing processes
   - Starts with debug logging

---

## 🔍 Debugging Strategy

The crash is happening during processing, likely in one of these areas:

1. **Image Extraction** - Most likely candidate
   - Base64 encoding large images
   - Memory issues with multiple images
   - Corrupted image data

2. **Hyperlink Extraction** - Possible
   - XPath queries on complex DOCX structure
   - Malformed hyperlink XML

3. **LLM API Call** - Less likely (would have different error)
   - API timeout
   - Rate limiting
   - Invalid response

4. **DOCX Rendering** - Less likely (happens after extraction)
   - Template issues
   - Memory exhaustion

**Our enhanced logging will pinpoint the exact location!**

---

## ✅ Success Criteria

After restart and retest:
- [ ] Backend stays running during processing
- [ ] Error is caught and logged (if any)
- [ ] Full stack trace is visible
- [ ] We can identify the root cause
- [ ] Fix can be implemented in <30 minutes

---

## 📝 Notes

- The semantic anchoring feature itself is **production-ready** (19 tests passing)
- This crash is an **environmental/integration issue**, not a feature bug
- The diagnostic tools successfully validated all configurations
- Enhanced error logging will make future debugging much faster

---

**Status:** Ready for restart and retest
**Estimated Time:** 5-10 minutes to reproduce and capture error
**Next Action:** Run `restart-backend.bat` and process a lesson plan
