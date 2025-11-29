# End-to-End Testing Guide

**Date:** October 26, 2025  
**Purpose:** Verify complete structured names implementation

---

## Prerequisites

### 1. Start Backend
```bash
cd d:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

**Expected:** Server starts on http://localhost:8000

### 2. Start Frontend (Optional - if using Tauri)
```bash
cd d:\LP\frontend
npm run tauri dev
```

**Or test via API directly with curl/Postman**

---

## Test Suite

### Test 1: Database Migration Verification ✅

**Purpose:** Verify schema and data migration

```bash
python verify_migration.py
```

**Expected Output:**
```
Users table columns: id, name, email, created_at, updated_at, 
                     base_path_override, first_name, last_name
  ✓ first_name: YES
  ✓ last_name: YES

Class slots table columns: ..., primary_teacher_first_name, 
                           primary_teacher_last_name
  ✓ primary_teacher_first_name: YES
  ✓ primary_teacher_last_name: YES

Found 3 users:
  - Analytics Test User
      first_name: 'Analytics'
      last_name: 'Test User'
      Status: ✓ Complete
  - Daniela Silva
      first_name: 'Daniela'
      last_name: 'Silva'
      Status: ✓ Complete
  - Wilson Rodrigues
      first_name: 'Wilson'
      last_name: 'Rodrigues'
      Status: ✓ Complete
```

**Status:** ✅ PASS / ❌ FAIL

---

### Test 2: Database CRUD Operations ✅

**Purpose:** Verify database methods work with structured names

```bash
python test_database_crud.py
```

**Expected Output:**
```
1. Testing create_user with first_name/last_name...
  Created user: Test User
    first_name: 'Test'
    last_name: 'User'
  ✓ PASS

2. Testing create_user with name only (backward compat)...
  ✓ PASS

3. Testing update_user with first_name/last_name...
  ✓ PASS

4. Testing update_user with name only (backward compat)...
  ✓ PASS

5. Testing update_class_slot with teacher names...
  ✓ PASS

6. Testing partial update (only first_name)...
  ✓ PASS

7. Cleaning up test users...
  ✓ Cleanup complete

✅ ALL CRUD TESTS PASSED
```

**Status:** ✅ PASS / ❌ FAIL

---

### Test 3: API Endpoints ✅

**Purpose:** Verify API accepts and returns structured names

**Start backend first, then:**

```bash
python test_api_endpoints.py
```

**Expected Output:**
```
1. Testing POST /api/users with first_name/last_name...
  ✓ Created user: API Test
    first_name: 'API'
    last_name: 'Test'
  ✓ PASS

2. Testing GET /api/users/{id}...
  ✓ PASS

3. Testing PUT /api/users/{id}...
  ✓ PASS

4. Testing POST /api/users/{id}/slots with teacher names...
  ✓ PASS

5. Testing PUT /api/slots/{id} with teacher names...
  ✓ PASS

6. Testing GET /api/users (list)...
  ✓ PASS

7. Cleaning up...
  ✓ Cleanup complete

✅ ALL API TESTS PASSED
```

**Status:** ✅ PASS / ❌ FAIL

---

### Test 4: Frontend User Creation 🖥️

**Purpose:** Verify UI captures structured names

**Steps:**
1. Open frontend (http://localhost:1420 or Tauri app)
2. Click "Add User"
3. **Verify:** See two separate fields: "First Name *" and "Last Name *"
4. Try submitting with only first name
5. **Expected:** Error "Please enter a last name"
6. Try submitting with only last name
7. **Expected:** Error "Please enter a first name"
8. Fill both fields: First="Test", Last="User"
9. Click "Create User"
10. **Expected:** Success message, user appears in list

**Status:** ✅ PASS / ❌ FAIL

**Screenshot:** (Optional)

---

### Test 5: Frontend Slot Configuration 🖥️

**Purpose:** Verify UI captures teacher structured names

**Steps:**
1. Select a user
2. Open slot configurator
3. **Verify:** See two fields: "Teacher First Name" and "Teacher Last Name"
4. Enter: First="Sarah", Last="Lang"
5. Fill other required fields (Subject, Grade)
6. Save slot
7. **Expected:** Slot saved successfully
8. Refresh page
9. **Verify:** Teacher names persist

**Status:** ✅ PASS / ❌ FAIL

**Screenshot:** (Optional)

---

### Test 6: Migration Warning Banner 🖥️

**Purpose:** Verify warning shows for incomplete profiles

**Steps:**
1. Select user "Daniela Silva" (has first/last name)
2. **Verify:** No warning banner
3. Use database to clear first_name:
   ```sql
   UPDATE users SET first_name = NULL WHERE name = 'Daniela Silva';
   ```
4. Refresh frontend
5. Select "Daniela Silva" again
6. **Expected:** Yellow warning banner appears
7. **Message:** "Profile Update Required"
8. Click "Update Profile" button
9. **Expected:** Settings dialog opens

**Status:** ✅ PASS / ❌ FAIL

**Screenshot:** (Optional)

---

### Test 7: Base Path Update 🖥️

**Purpose:** Verify base path endpoint works after fix

**Steps:**
1. Select a user
2. Click "Settings"
3. Enter base path: `F:\rodri\Documents\OneDrive\AS\Lesson Plan`
4. Click "Save Path"
5. **Expected:** Success message, no 422 error
6. Refresh page
7. **Verify:** Base path persists

**Status:** ✅ PASS / ❌ FAIL

---

### Test 8: Week Date Formatting 🧪

**Purpose:** Verify week dates are normalized

**Test via Python:**
```python
from backend.utils.date_formatter import format_week_dates

# Test various formats
test_cases = [
    ("10-27-10-31", "10/27-10/31"),
    ("10/27-10/31", "10/27-10/31"),
    ("Week of 10/27-10/31", "10/27-10/31"),
    ("10-27 to 10-31", "10/27-10/31"),
]

for input_val, expected in test_cases:
    result = format_week_dates(input_val)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{input_val}' → '{result}' (expected '{expected}')")
```

**Expected:** All tests pass with ✓

**Status:** ✅ PASS / ❌ FAIL

---

### Test 9: Lesson Plan Processing 📄

**Purpose:** Verify structured names appear in output DOCX

**Steps:**
1. Ensure user has:
   - first_name: "Daniela"
   - last_name: "Silva"
2. Ensure slot has:
   - primary_teacher_first_name: "Sarah"
   - primary_teacher_last_name: "Lang"
   - Subject, Grade filled
3. Process a week (e.g., "10/27-10/31")
4. Wait for processing to complete
5. Open output DOCX file
6. Check metadata table at top
7. **Expected Name:** "Sarah Lang / Daniela Silva"
8. **Expected Week:** "Week of: 10/27-10/31"

**Status:** ✅ PASS / ❌ FAIL

**Screenshot:** (Optional - metadata table)

---

### Test 10: Fallback to Legacy Fields 📄

**Purpose:** Verify system works with unmigrated data

**Steps:**
1. Create slot with only `primary_teacher_name` = "Davies"
2. Leave `primary_teacher_first_name` and `primary_teacher_last_name` empty
3. Process week
4. Open output DOCX
5. Check metadata table
6. **Expected Name:** "Davies / Daniela Silva" (uses legacy field)

**Status:** ✅ PASS / ❌ FAIL

---

### Test 11: Multiple Slots (Consolidated) 📄

**Purpose:** Verify structured names work in multi-slot output

**Steps:**
1. Configure 2+ slots with different teachers
2. Each slot has structured teacher names
3. Process week (all slots)
4. Open consolidated output DOCX
5. Check each slot's section
6. **Verify:** Each shows correct "Primary / Bilingual" format

**Status:** ✅ PASS / ❌ FAIL

---

### Test 12: Backward Compatibility 🔄

**Purpose:** Verify old API calls still work

**Test with curl:**

```bash
# Old-style user creation (should fail - requires structured names now)
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Old Style", "email": "old@test.com"}'

# Expected: 422 error (validation requires first_name/last_name)

# New-style user creation
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"first_name": "New", "last_name": "Style", "email": "new@test.com"}'

# Expected: 200 OK with user data
```

**Status:** ✅ PASS / ❌ FAIL

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| 1. Database Migration | ⬜ | |
| 2. Database CRUD | ⬜ | |
| 3. API Endpoints | ⬜ | |
| 4. Frontend User Creation | ⬜ | |
| 5. Frontend Slot Config | ⬜ | |
| 6. Migration Warning | ⬜ | |
| 7. Base Path Update | ⬜ | |
| 8. Week Date Formatting | ⬜ | |
| 9. Lesson Plan Output | ⬜ | |
| 10. Legacy Fallback | ⬜ | |
| 11. Multiple Slots | ⬜ | |
| 12. Backward Compat | ⬜ | |

**Overall Status:** ⬜ NOT STARTED / 🔄 IN PROGRESS / ✅ PASSED / ❌ FAILED

---

## Common Issues & Solutions

### Issue: 422 Validation Error on User Creation
**Cause:** Frontend sending old format
**Solution:** Verify frontend uses `first_name`/`last_name` fields

### Issue: Migration Warning Doesn't Show
**Cause:** User has first_name/last_name populated
**Solution:** This is correct behavior - warning only for incomplete profiles

### Issue: Teacher Name Shows "Unknown"
**Cause:** Both structured and legacy fields are empty
**Solution:** Populate teacher names in slot configuration

### Issue: Week Date Not Formatted
**Cause:** `format_week_dates()` not called
**Solution:** Verify batch_processor imports and uses utility

### Issue: Base Path Update Fails
**Cause:** Using old endpoint
**Solution:** Verify frontend uses `/api/users/{id}/base-path`

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Document any edge cases found
2. Update user documentation
3. Deploy to production
4. Monitor for issues

### If Tests Fail ❌
1. Document failure details
2. Check error logs
3. Fix identified issues
4. Re-run failed tests
5. Repeat until all pass

---

## Testing Checklist

- [ ] Backend started successfully
- [ ] Frontend started (if testing UI)
- [ ] Database migration verified
- [ ] CRUD operations tested
- [ ] API endpoints tested
- [ ] Frontend user creation tested
- [ ] Frontend slot config tested
- [ ] Migration warning tested
- [ ] Base path update tested
- [ ] Week formatting tested
- [ ] Lesson plan output tested
- [ ] Legacy fallback tested
- [ ] Multiple slots tested
- [ ] Backward compatibility tested
- [ ] All issues documented
- [ ] All tests passing

---

## Ready to Start Testing?

Run tests in order:
1. Database tests (1-2) - No backend needed
2. API tests (3) - Backend needed
3. Frontend tests (4-7) - Backend + Frontend needed
4. Integration tests (8-12) - Full stack needed

Let's begin!
