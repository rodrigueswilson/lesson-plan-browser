# Session 7 - End-to-End Testing Guide

## ✅ System Status

**Backend:** Running on http://127.0.0.1:8000
**Frontend:** Tauri app launching
**All Diagnostics:** PASSED (14/14 checks)

---

## 🧪 Testing Checklist

### Test 1: Basic Processing (5 min)
**Goal:** Verify the app processes a lesson plan without crashing

1. **Select a user** from the dropdown
2. **Choose week dates** (or use auto-detect)
3. **Browse** to `input/` folder with lesson plans
4. **Click "Process All"**
5. **Watch progress bar** - should show real-time updates
6. **Check output** folder for generated DOCX

**Expected Result:**
- ✅ Progress bar updates smoothly
- ✅ No crashes or errors
- ✅ Output file created in `output/` folder

---

### Test 2: Semantic Anchoring - Hyperlinks (10 min)
**Goal:** Verify hyperlinks are preserved in correct locations

**Test File:** Use a lesson plan with hyperlinks (e.g., `input/9_15-9_19 Davies Lesson Plans.docx`)

1. **Open the input file** - note where hyperlinks appear
2. **Process the file** through the app
3. **Open the output file** from `output/` folder
4. **Verify hyperlinks:**
   - ✅ All hyperlinks present
   - ✅ Hyperlinks in semantically correct locations (near related content)
   - ✅ Hyperlinks are clickable and styled (blue, underlined)

**What to Look For:**
- Hyperlinks should be near the same text/context as in the input
- If exact text match isn't found, should be in the same section
- Should NOT all be dumped at the end of the document

---

### Test 3: Structure-Based Placement - Images (10 min)
**Goal:** Verify images are placed in exact locations

**Test File:** Use a lesson plan with images (if available in `input/`)

1. **Open the input file** - note:
   - Which day/cell contains the image
   - Which section (e.g., "Anticipatory Set:", "Guided Practice:")
2. **Process the file** through the app
3. **Open the output file**
4. **Verify images:**
   - ✅ Image appears in the SAME day column
   - ✅ Image appears in the SAME section row
   - ✅ Image quality preserved

**What to Look For:**
- Image should be in the exact same table cell (row + column)
- If cell is empty, image should still be placed there
- Should NOT be at the end of the document

---

### Test 4: Slot-Level Reprocessing (5 min)
**Goal:** Verify selective reprocessing works

1. **Process a full week** (all 5 days)
2. **Go to History tab** - find the processed week
3. **Uncheck some days** (e.g., only select Monday and Wednesday)
4. **Click "Reprocess Selected"**
5. **Verify:**
   - ✅ Only selected days are reprocessed
   - ✅ Progress bar shows correct count (2/5 instead of 5/5)
   - ✅ Output file updates with only those days changed

---

### Test 5: Analytics Dashboard (5 min)
**Goal:** Verify analytics are tracking

1. **After processing** several lesson plans, go to **Analytics tab**
2. **Check summary cards:**
   - ✅ Total plans processed (should match your tests)
   - ✅ Total cost (should show dollar amount)
   - ✅ Average time per plan
   - ✅ Total tokens used
3. **Check charts:**
   - ✅ Model distribution pie chart
   - ✅ Operation breakdown bar chart
   - ✅ Daily activity line chart
4. **Try time range selector** (7/30/90 days)
5. **Try CSV export** - should download a file

---

## 🐛 If You Encounter Errors

### Backend Errors
**Symptom:** Error messages in the backend terminal window

**Action:**
1. Copy the full error stack trace
2. Share it with me
3. Note what action triggered it (e.g., "clicked Process All")

### Frontend Errors
**Symptom:** App freezes, crashes, or shows error dialog

**Action:**
1. Open browser DevTools (if using web version)
2. Check Console tab for errors
3. Share error messages
4. Note what you were doing when it happened

### Processing Errors
**Symptom:** Progress bar stops, or output file is corrupted

**Action:**
1. Check backend terminal for errors
2. Check `logs/` folder for error logs
3. Try with a different input file
4. Share the specific file that caused the issue

---

## 📊 Success Criteria

**Minimum for "Working":**
- ✅ Can process a lesson plan end-to-end
- ✅ Output file is created and readable
- ✅ No crashes or unhandled errors

**Full Feature Validation:**
- ✅ Hyperlinks preserved (Test 2)
- ✅ Images preserved (Test 3)
- ✅ Slot reprocessing works (Test 4)
- ✅ Analytics tracking works (Test 5)
- ✅ Progress bar updates in real-time

---

## 🎯 What to Report Back

After testing, share:

1. **Which tests passed?** (1-5)
2. **Any error messages?** (full stack traces)
3. **Any unexpected behavior?** (describe what happened)
4. **Screenshots?** (if helpful, especially for hyperlink/image placement)

---

## 💡 Quick Fixes

### If backend crashes during processing:
```bash
# Restart backend
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

### If frontend becomes unresponsive:
```bash
# Restart frontend
cd D:\LP\frontend
npm run tauri:dev
```

### If database seems corrupted:
```bash
# Check database
python check_db_schema.py
python check_users.py
```

---

## 📁 Key Files to Check

**Input:** `d:\LP\input\*.docx` - Your source lesson plans
**Output:** `d:\LP\output\*.docx` - Generated lesson plans
**Logs:** `d:\LP\logs\*.txt` - Error logs (if any)
**Database:** `d:\LP\data\lesson_planner.db` - Processing history

---

**Status:** Ready for testing! 🚀
**Estimated Time:** 30-40 minutes for full validation
**Priority:** Test 1 (basic processing) first, then Tests 2-3 (semantic anchoring)
