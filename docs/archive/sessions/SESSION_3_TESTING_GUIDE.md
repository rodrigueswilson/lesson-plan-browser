# Session 3: Testing Guide

Quick guide to test all 4 new frontend UX features.

---

## Prerequisites

1. Backend running: `python -m backend.api`
2. Frontend running: `npm run tauri dev` (in frontend folder)
3. At least one user with configured slots

---

## Test Sequence

### 1. Test Slot Checkboxes (2 minutes)

**Steps**:
1. Navigate to the "Generate Weekly Plan" section
2. Verify all slots are checked by default
3. Click "Deselect All" button
   - All checkboxes should uncheck
   - Header should show "0 of X slots selected"
4. Click "Select All" button
   - All checkboxes should check
   - Header should show "X of X slots selected"
5. Click individual checkboxes
   - Each click should toggle the checkbox
   - Selected slots should have blue border
   - Count should update in header
6. Try clicking on the slot card itself (not checkbox)
   - Should toggle selection

**Expected Result**: Checkboxes work smoothly, count updates correctly

---

### 2. Test Button States (1 minute)

**Steps**:
1. Select at least one slot
2. Enter a week (e.g., "10-06-10-10")
3. Click "Generate" button
4. Observe button changes:
   - Should show confirmation dialog first
5. Click "Proceed" in dialog
6. Watch button state:
   - Should show "Processing..." with spinner
   - Should be disabled
7. Wait for completion
8. Button should show either:
   - "Done!" with green background (success)
   - "Failed" with red background (error)
9. Wait 3 seconds
   - Button should reset to "Generate"

**Expected Result**: Button states transition smoothly, auto-reset works

---

### 3. Test Folder Confirmation (1 minute)

**Steps**:
1. Select slots and enter week
2. Click "Generate" button
3. Verify dialog appears with:
   - Title: "Confirm Processing"
   - Source folder path
   - Week date
   - Slot count
4. Click "Cancel"
   - Dialog should close
   - No processing should start
5. Click "Generate" again
6. Click "Proceed"
   - Dialog should close
   - Processing should start

**Expected Result**: Dialog shows correct info, Cancel/Proceed work

---

### 4. Test Progress Updates (2 minutes)

**Steps**:
1. Start processing (follow steps above)
2. Watch the progress bar
   - Should update during processing
   - Message should change
   - Percentage should increase
3. Check browser console (F12)
   - Should see polling logs
   - No errors
4. Wait for completion
   - Progress should reach 100%
   - Success/error message should appear

**Expected Result**: Progress updates in real-time, no console errors

---

## Integration Test (5 minutes)

**Full Workflow**:
1. Select 2-3 specific slots (not all)
2. Enter week date
3. Click "Generate"
4. Verify confirmation dialog shows correct count
5. Click "Proceed"
6. Watch button change to "Processing..."
7. Watch progress bar update
8. Wait for completion
9. Verify "Done!" appears
10. Wait for auto-reset
11. Check that output file was created

**Expected Result**: Entire workflow works smoothly end-to-end

---

## Common Issues & Solutions

### Issue: Checkboxes don't appear
**Solution**: Refresh the page, ensure slots are loaded

### Issue: Button doesn't change state
**Solution**: Check console for errors, verify backend is running

### Issue: Dialog doesn't appear
**Solution**: Check that Dialog.tsx was created correctly

### Issue: Progress doesn't update
**Solution**: 
- Check backend has `/api/progress/{task_id}/poll` endpoint
- Verify polling is working in console
- Ensure backend progress tracker is updating

### Issue: "Failed" state appears immediately
**Solution**: 
- Check backend logs for errors
- Verify source folder path is correct
- Ensure input files exist

---

## Quick Verification Commands

### Check backend is running:
```bash
curl http://localhost:8000/api/health
```

### Check progress endpoint:
```bash
curl http://localhost:8000/api/progress/test-id/poll
```

### View backend logs:
Look for progress updates and slot filtering messages

---

## Success Criteria

All tests pass if:
- Checkboxes work and update count
- Button shows all 4 states correctly
- Dialog appears and functions properly
- Progress updates during processing
- No console errors
- Processing completes successfully

---

## Next Steps After Testing

1. Document any bugs found
2. Fix critical issues
3. Proceed to Session 4 (Analytics & History)

---

**Estimated Testing Time**: 10-15 minutes
