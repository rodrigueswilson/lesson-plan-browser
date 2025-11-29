# Frontend Testing Guide

## Prerequisites

✅ **Backend Running:**
```powershell
cd D:\LP
$env:USE_SUPABASE = "False"
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

✅ **Frontend Running:**
```powershell
cd D:\LP\frontend
npm run dev
```

Open browser: `http://localhost:1420/` (or port shown in terminal)

## Testing Checklist

### ✅ Phase 1: User Management

#### Test 1.1: User List Loading
**Steps:**
1. Open the app
2. Wait for users to load

**Expected:**
- ✅ All 4 users appear in dropdown
- ✅ No console errors
- ✅ Loading state shows briefly

**Check Console:**
- Look for: `[UserSelector] Users loaded: 4 users`
- No red errors

---

#### Test 1.2: User Selection
**Steps:**
1. Click user dropdown
2. Select "Daniela Silva"

**Expected:**
- ✅ User selected
- ✅ User name appears in selector
- ✅ Slots and plans load (may be empty)

**Check Console:**
- Look for: `[UserSelector] Selecting user: ...`
- Look for: `[UserSelector] User data loaded: ...`

---

#### Test 1.3: Create New User
**Steps:**
1. Click "Add User" button
2. Fill form:
   - First Name: "Test"
   - Last Name: "User"
   - Email: "test.user@example.com"
3. Click "Create User"

**Expected:**
- ✅ Success message appears
- ✅ User appears in dropdown
- ✅ User is automatically selected
- ✅ Form closes
- ✅ New user data loads

**Check Console:**
- Look for: `[UserSelector] Creating user: ...`
- Look for: `[UserSelector] User created successfully: ...`

**If Fails:**
- Check browser console for error
- Check backend terminal for error
- Verify backend is running

---

#### Test 1.4: User Settings (Base Path)
**Steps:**
1. Select a user
2. Click settings icon (gear)
3. Enter a path: `F:\test\lesson-plans`
4. Click "Save"

**Expected:**
- ✅ Success message
- ✅ Path saved
- ✅ Settings dialog closes

---

### ✅ Phase 2: Class Slots (Plans Page)

#### Test 2.1: Navigate to Plans
**Steps:**
1. Click "Plans" in navigation

**Expected:**
- ✅ "Class Slots Configuration" page appears
- ✅ Shows existing slots (if any)
- ✅ Shows "Add Slot" button

---

#### Test 2.2: View Existing Slots
**Steps:**
1. Select a user who has slots (or create one)
2. Go to Plans page

**Expected:**
- ✅ Slots displayed in list
- ✅ Each slot shows: Subject, Grade, Teacher name
- ✅ Can drag to reorder (if multiple slots)

---

#### Test 2.3: Create New Slot
**Steps:**
1. Click "Add Slot" button
2. Fill form:
   - Slot Number: 1
   - Subject: "Math"
   - Grade: "5th Grade"
   - Teacher First Name: "John"
   - Teacher Last Name: "Doe"
   - Teacher File Pattern: "John_Doe_*.docx"
3. Click "Save" or press Enter

**Expected:**
- ✅ Slot appears in list immediately
- ✅ Form resets
- ✅ Slot persists after page refresh

**Check Console:**
- Look for: `[SlotConfigurator] Creating slot: ...`
- Look for: `[SlotConfigurator] Slot created successfully: ...`

**If Slot Doesn't Save:**
- Check if changes are auto-saved or need explicit save
- Check console for errors
- Verify API call succeeded

---

#### Test 2.4: Edit Slot ✅ VERIFIED
**Steps:**
1. Click on a slot's fields
2. Change Subject to "Science"
3. Change Grade to "6th Grade"

**Expected:**
- ✅ Changes save automatically (or after clicking save)
- ✅ Changes persist after refresh

**Status:** ✅ **VERIFIED WORKING** - Auto-save functional, changes persist correctly
**Note:** SlotConfigurator uses auto-save (optimistic updates with API sync)

---

#### Test 2.5: Delete Slot
**Steps:**
1. Click trash icon on a slot
2. Confirm deletion

**Expected:**
- ✅ Slot removed from list
- ✅ Slot deleted from database
- ✅ Slot doesn't reappear after refresh

---

#### Test 2.6: Reorder Slots (Drag & Drop) ✅ VERIFIED
**Steps:**
1. Create multiple slots (2-3)
2. Drag slot by grip icon
3. Drop in new position

**Expected:**
- ✅ Slots reorder visually
- ✅ Order persists after refresh
- ✅ Display order updates

**Status:** ✅ **VERIFIED WORKING** - Drag & drop functional, order persists, consistent across both tabs

---

### ✅ Phase 3: Weekly Plans Processing (Home Page)

#### Test 3.1: Navigate to Home ✅ VERIFIED
**Steps:**
1. Click "Home" in navigation

**Expected:**
- ✅ "Batch Processor" section appears
- ✅ Week selector visible
- ✅ Slot selection visible

**Status:** ✅ **VERIFIED WORKING** - Home page loads correctly with all components

---

#### Test 3.2: Select Week ✅ VERIFIED
**Steps:**
1. Select a user with `base_path_override` set
2. Wait for recent weeks to load

**Expected:**
- ✅ Recent weeks appear in dropdown
- ✅ Can select a week
- ✅ Week date displays correctly

**Status:** ✅ **VERIFIED WORKING** - Week selection functional

**If No Weeks:**
- Check user has `base_path_override` set
- Check folder exists and contains week folders
- Check console for warnings

---

#### Test 3.3: Select Slots for Processing ✅ VERIFIED
**Steps:**
1. Select a week
2. Check/uncheck slots

**Expected:**
- ✅ Slots can be selected/deselected
- ✅ "Select All" / "Deselect All" works
- ✅ Selected count updates

**Status:** ✅ **VERIFIED WORKING** - Slot selection functional

---

#### Test 3.4: Process Week ✅ VERIFIED
**Steps:**
1. Select a week
2. Select slots (or use all)
3. Click "Process Week"
4. Confirm in dialog

**Expected:**
- ✅ Progress indicator appears
- ✅ Progress updates (current/total)
- ✅ Status messages update
- ✅ Completion message appears
- ✅ Output file location shown

**Status:** ✅ **VERIFIED WORKING** - Weekly plan processing functional end-to-end

**Check Console:**
- Look for: `[BatchProcessor] Starting processing...`
- Look for progress updates
- Look for completion message

**If Processing Fails:**
- Check backend logs
- Check error message in UI
- Verify LLM service is configured
- Check file paths are correct

---

### ✅ Phase 4: Plan History

#### Test 4.1: Navigate to History
**Steps:**
1. Click "History" in navigation

**Expected:**
- ✅ "Plan History" page appears
- ✅ Past plans listed (if any)
- ✅ Shows: Date, Status, File location

---

#### Test 4.2: View Plan Details ✅ VERIFIED
**Steps:**
1. Click on a plan in history

**Expected:**
- ✅ Plan details shown
- ✅ Can download output file (if available)
- ✅ Error message shown (if plan failed)

**Status:** ✅ **VERIFIED WORKING** - Plan details display correctly, download works correctly using plan ID endpoint

---

### ✅ Phase 5: Analytics

#### Test 5.1: Navigate to Analytics ✅ VERIFIED
**Steps:**
1. Click "Analytics" in navigation

**Expected:**
- ✅ Analytics dashboard appears
- ✅ Summary metrics displayed
- ✅ Daily chart visible

**Status:** ✅ **VERIFIED WORKING** - Analytics dashboard loads correctly

---

#### Test 5.2: View Metrics ✅ VERIFIED WORKING
**Steps:**
1. Check summary cards
2. Check daily chart
3. Change date range (if available)

**Expected:**
- ✅ Metrics load correctly
- ✅ Chart displays data
- ✅ Date filtering works

**Status:** ✅ **VERIFIED WORKING** - Working perfectly well - All detailed operations (24+) are displaying correctly in analytics dashboard. Daily chart displays correctly (bug fixed).

---

## 🐛 Common Issues & Solutions

### Issue: Users Not Loading
**Symptoms:** Empty dropdown, error message

**Check:**
1. Backend running? `http://127.0.0.1:8000/api/health`
2. CORS enabled? Check backend logs
3. Browser console errors?
4. Network tab shows failed request?

**Fix:**
- Restart backend
- Check `backend/api.py` CORS settings
- Clear browser cache

---

### Issue: User Creation Fails
**Symptoms:** Error alert, user not created

**Check:**
1. Form validation (required fields?)
2. Backend logs show error?
3. Database accessible?

**Fix:**
- Check all required fields filled
- Verify backend is running
- Check database permissions

---

### Issue: Slots Not Saving
**Symptoms:** Changes don't persist

**Check:**
1. Auto-save or manual save?
2. API call succeeds?
3. Console errors?

**Fix:**
- Check SlotConfigurator save logic
- Verify API endpoint works
- Check authorization header

---

### Issue: Processing Fails
**Symptoms:** Error during processing

**Check:**
1. Backend logs
2. LLM service configured?
3. File paths correct?
4. User has base_path_override?

**Fix:**
- Check backend configuration
- Verify LLM API keys
- Check file system permissions

---

## 📝 Test Results Template

```markdown
### Test Results - [Date]

#### User Management
- [ ] List Users: ✅ / ❌
- [ ] Select User: ✅ / ❌
- [ ] Create User: ✅ / ❌
- [ ] Update Settings: ✅ / ❌
- **Issues:** ...

#### Class Slots
- [ ] View Slots: ✅ / ❌
- [ ] Create Slot: ✅ / ❌
- [ ] Edit Slot: ✅ / ❌
- [ ] Delete Slot: ✅ / ❌
- [ ] Reorder Slots: ✅ / ❌
- **Issues:** ...

#### Weekly Plans
- [ ] Select Week: ✅ / ❌
- [ ] Process Week: ✅ / ❌
- [ ] View Progress: ✅ / ❌
- **Issues:** ...

#### Plan History
- [ ] View History: ✅ / ❌
- [ ] View Details: ✅ / ❌
- **Issues:** ...

#### Analytics
- [ ] View Dashboard: ✅ / ❌
- [ ] View Metrics: ✅ / ❌
- **Issues:** ...

#### Overall
- **Bugs Found:** [count]
- **Critical Issues:** ...
- **Minor Issues:** ...
- **Suggestions:** ...
```

---

## 🚀 Quick Test Commands

### Check Backend
```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
Invoke-WebRequest http://127.0.0.1:8000/api/users
```

### Check Frontend
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests

### Run API Tests
```powershell
python scripts/test_api_basic.py
```

---

**Ready to test!** Start with Phase 1 and work through systematically. Document any issues you find.

