# Next Steps: Frontend Testing

## ✅ Backend Status: All Tests Passing!

All API endpoints are working correctly:
- ✅ Health check
- ✅ List users (4 users found)
- ✅ Get user by ID
- ✅ Create user
- ✅ Delete user
- ✅ Authorization headers

## 🎯 Frontend Testing Checklist

### Step 1: Start Frontend
```powershell
cd frontend
npm run dev
```

Open browser to: `http://localhost:1420/` (or the port shown)

### Step 2: Test User Management

#### 2.1 Verify User List
- [ ] Open the app
- [ ] Verify all 4 users are visible in the dropdown
- [ ] Select a user
- [ ] Verify user data loads (slots, plans)

#### 2.2 Create New User
- [ ] Click "Add User" button
- [ ] Fill in:
  - First Name: "Test"
  - Last Name: "Frontend"
  - Email: "test.frontend@example.com"
- [ ] Click "Create User"
- [ ] Verify:
  - Success message appears
  - User appears in dropdown
  - User is automatically selected
  - Form closes

#### 2.3 Test User Selection
- [ ] Select different users from dropdown
- [ ] Verify user data changes
- [ ] Verify slots and plans update

### Step 3: Test Class Slots (Plans Page)

#### 3.1 Navigate to Plans
- [ ] Click "Plans" in navigation
- [ ] Verify "Class Slots Configuration" page appears

#### 3.2 View Existing Slots
- [ ] Check if any slots exist for selected user
- [ ] Verify slot display (subject, grade, teacher)

#### 3.3 Create New Slot
- [ ] Click "Add Slot" button
- [ ] Fill in slot form:
  - Slot Number: 1
  - Subject: "Math"
  - Grade: "5th Grade"
  - Teacher First Name: "John"
  - Teacher Last Name: "Doe"
- [ ] Submit form
- [ ] Verify slot appears in list

#### 3.4 Edit Slot
- [ ] Click edit on a slot
- [ ] Change some fields
- [ ] Save changes
- [ ] Verify changes persist

#### 3.5 Delete Slot
- [ ] Delete a slot
- [ ] Verify slot removed from list

### Step 4: Test Weekly Plans Processing (Home Page)

#### 4.1 Navigate to Home
- [ ] Click "Home" in navigation
- [ ] Verify "Batch Processor" appears

#### 4.2 Select Week
- [ ] Select a user with `base_path_override` set
- [ ] Verify recent weeks are detected
- [ ] Select a week

#### 4.3 Process Week
- [ ] Select slots to process
- [ ] Click "Process Week"
- [ ] Verify:
  - Progress indicator appears
  - Progress updates
  - Completion message
  - Output file location shown

### Step 5: Test Plan History

#### 5.1 Navigate to History
- [ ] Click "History" in navigation
- [ ] Verify past plans are listed

#### 5.2 View Plan Details
- [ ] Click on a plan
- [ ] Verify plan details shown
- [ ] Test download if available

### Step 6: Test Analytics

#### 6.1 Navigate to Analytics
- [ ] Click "Analytics" in navigation
- [ ] Verify analytics dashboard appears

#### 6.2 View Metrics
- [ ] Check summary metrics
- [ ] Check daily analytics chart
- [ ] Test date range selection

## 🐛 What to Look For

### Common Issues
1. **API Connection Errors**
   - Check browser console for errors
   - Verify backend is running on port 8000
   - Check CORS settings

2. **User Creation Fails**
   - Check form validation
   - Check error messages
   - Verify API response

3. **Slots Not Loading**
   - Check authorization header
   - Verify user ID is correct
   - Check API response

4. **Processing Fails**
   - Check progress indicators
   - Verify error messages
   - Check backend logs

## 📝 Test Results Template

After testing, document results:

```markdown
### Test Results - [Date]

#### User Management
- List Users: ✅ / ❌
- Create User: ✅ / ❌
- Select User: ✅ / ❌
- Notes: ...

#### Class Slots
- View Slots: ✅ / ❌
- Create Slot: ✅ / ❌
- Edit Slot: ✅ / ❌
- Delete Slot: ✅ / ❌
- Notes: ...

#### Weekly Plans
- Process Week: ✅ / ❌
- View History: ✅ / ❌
- Notes: ...

#### Issues Found
1. [Issue description]
2. [Issue description]
```

## 🚀 Quick Start Commands

```powershell
# Terminal 1: Backend
cd D:\LP
$env:USE_SUPABASE = "False"
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd D:\LP\frontend
npm run dev

# Terminal 3: Run API Tests (optional)
cd D:\LP
python scripts/test_api_basic.py
```

## ✅ Success Criteria

All tests pass when:
- ✅ Users can be created from frontend
- ✅ Users can be selected and data loads
- ✅ Slots can be created, edited, deleted
- ✅ Weekly plans can be processed
- ✅ History shows past plans
- ✅ Analytics displays correctly
- ✅ No console errors
- ✅ Error messages are clear and helpful

---

**Ready to test!** Start with Step 1 and work through each section systematically.

