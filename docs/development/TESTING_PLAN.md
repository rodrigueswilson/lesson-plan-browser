# Development Testing Plan

## Application Overview

### Frontend Features
1. **UserSelector** - Select/create users (always visible)
2. **BatchProcessor** - Process weekly lesson plans (Home)
3. **SlotConfigurator** - Configure class slots (Plans)
4. **PlanHistory** - View past generated plans (History)
5. **Analytics** - Performance metrics dashboard (Analytics)

### Backend API Endpoints
- **Users:** `GET /api/users`, `POST /api/users`, `GET /api/users/{id}`, `PUT /api/users/{id}`, `DELETE /api/users/{id}`
- **Class Slots:** `GET /api/users/{id}/slots`, `POST /api/users/{id}/slots`, `PUT /api/slots/{id}`, `DELETE /api/slots/{id}`
- **Weekly Plans:** `GET /api/users/{id}/plans`, `POST /api/process-week`
- **Analytics:** `GET /api/analytics/summary`, `GET /api/analytics/daily`
- **Health:** `GET /api/health`

## Testing Checklist

### ✅ Phase 1: User Management (Priority: High)

#### 1.1 User Selection
- [ ] Load users list on app start
- [ ] Display all 4 users correctly
- [ ] Select user from dropdown
- [ ] Verify user selection persists
- [ ] Verify `X-Current-User-Id` header is sent with requests

#### 1.2 User Creation
- [ ] Click "Add User" button
- [ ] Fill form (first name, last name, email)
- [ ] Submit form
- [ ] Verify user appears in list
- [ ] Verify user can be selected
- [ ] Test with missing fields (validation)

#### 1.3 User Update
- [ ] Edit user profile
- [ ] Update base path override
- [ ] Verify changes persist
- [ ] Test authorization (can't edit other users)

#### 1.4 User Deletion
- [ ] Delete user
- [ ] Verify user removed from list
- [ ] Verify associated data handling

### ✅ Phase 2: Class Slots (Priority: High)

#### 2.1 View Slots
- [ ] Navigate to "Plans" page
- [ ] View existing slots for selected user
- [ ] Verify empty state if no slots
- [ ] Verify slot display (subject, grade, teacher info)

#### 2.2 Create Slot
- [ ] Click "Add Slot" button
- [ ] Fill slot form:
  - Slot number (1-10)
  - Subject
  - Grade
  - Homeroom (optional)
  - Proficiency levels (optional)
  - Teacher first/last name
  - Teacher file pattern
- [ ] Submit form
- [ ] Verify slot appears in list
- [ ] Test validation (required fields, slot number limits)

#### 2.3 Update Slot
- [ ] Edit existing slot
- [ ] Update fields
- [ ] Verify changes persist
- [ ] Test authorization

#### 2.4 Delete Slot
- [ ] Delete slot
- [ ] Verify slot removed
- [ ] Verify slot numbers reorder correctly

### ✅ Phase 3: Weekly Plans Processing (Priority: Medium)

#### 3.1 View Recent Weeks
- [ ] Select user with base_path_override
- [ ] Verify recent weeks detection
- [ ] Display week options

#### 3.2 Process Week
- [ ] Select week
- [ ] Select slots to process
- [ ] Click "Process Week"
- [ ] Verify progress indicator
- [ ] Verify completion
- [ ] Check output file location

#### 3.3 Batch Processing
- [ ] Process multiple slots
- [ ] Verify all slots processed
- [ ] Check error handling for failed slots

### ✅ Phase 4: Plan History (Priority: Medium)

#### 4.1 View History
- [ ] Navigate to "History" page
- [ ] View past plans
- [ ] Verify plan details (date, status, file)
- [ ] Test pagination/limit

#### 4.2 Plan Details
- [ ] View plan details
- [ ] Download output file
- [ ] View error messages for failed plans

### ✅ Phase 5: Analytics (Priority: Low)

#### 5.1 View Analytics
- [ ] Navigate to "Analytics" page
- [ ] View summary metrics
- [ ] View daily analytics
- [ ] Test date range selection
- [ ] Test user filtering

#### 5.2 Export Analytics
- [ ] Export CSV
- [ ] Verify file download
- [ ] Verify data format

### ✅ Phase 6: Error Handling & Edge Cases (Priority: High)

#### 6.1 Network Errors
- [ ] Test with backend offline
- [ ] Verify error messages
- [ ] Test retry logic

#### 6.2 Authorization Errors
- [ ] Test without `X-Current-User-Id` header
- [ ] Test with invalid user ID
- [ ] Test accessing other user's data
- [ ] Verify 403/401 handling

#### 6.3 Validation Errors
- [ ] Test invalid form inputs
- [ ] Test missing required fields
- [ ] Test invalid data types
- [ ] Verify error messages

#### 6.4 Empty States
- [ ] No users
- [ ] No slots
- [ ] No plans
- [ ] No analytics data

## Test Execution Order

1. **Start Here:** User Management (Phase 1)
2. **Then:** Class Slots (Phase 2)
3. **Then:** Weekly Plans (Phase 3)
4. **Then:** Plan History (Phase 4)
5. **Finally:** Analytics (Phase 5)
6. **Throughout:** Error Handling (Phase 6)

## Test Results Template

```markdown
### Test: [Feature Name]
- **Status:** ✅ Pass / ❌ Fail / ⚠️ Partial
- **Date:** YYYY-MM-DD
- **Notes:** 
- **Issues Found:**
- **Screenshots:** (if applicable)
```

## Quick Test Commands

### Backend Health Check
```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

### List Users
```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/users | ConvertFrom-Json
```

### Test User Creation
```powershell
$body = @{
    first_name = "Test"
    last_name = "User"
    email = "test@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://127.0.0.1:8000/api/users -Method POST -Body $body -ContentType "application/json"
```

### Test Authorization
```powershell
# Without header (should work with allow_if_none=True)
Invoke-WebRequest http://127.0.0.1:8000/api/users

# With header
$headers = @{ "X-Current-User-Id" = "29fa9ed7-3174-4999-86fd-40a542c28cff" }
Invoke-WebRequest http://127.0.0.1:8000/api/users/29fa9ed7-3174-4999-86fd-40a542c28cff -Headers $headers
```

