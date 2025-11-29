# Browser App Data Flow Test

This test suite validates that the backend API endpoints used by the lesson-plan-browser app are working correctly before running the Tauri app.

## Quick Start

1. **Start the backend** (if not already running):
   ```powershell
   python -m uvicorn backend.api:app --reload --port 8000
   ```

2. **Run the test**:
   ```powershell
   cd lesson-plan-browser
   python test_browser_data_flow.py
   ```

## What It Tests

The test suite validates the complete data flow from database/JSON files to API endpoints:

### Core Endpoints

1. **Health Check** (`/api/health`)
   - Verifies backend is running
   - Checks API version

2. **Users** (`/api/users`, `/api/users/{id}`)
   - Lists all users
   - Gets user details
   - Required for user selector in app

3. **Recent Weeks** (`/api/recent-weeks`)
   - Detects JSON lesson plan files from file system
   - Returns available weeks for week selector
   - **Critical for JSON file support**

4. **Lesson Plans** (`/api/users/{id}/plans`, `/api/plans/{id}`)
   - Lists plans from database
   - Gets plan detail with `lesson_json` field
   - **Core data for browser views**

5. **Schedule** (`/api/schedules/{id}`, `/api/schedules/{id}/current`)
   - Gets schedule entries
   - Gets schedule for specific day
   - Gets current lesson (for Lesson Mode auto-detection)

6. **Class Slots** (`/api/users/{id}/slots`)
   - Lists class slots
   - Used for plan matching and enrichment

### Lesson Mode Endpoints

7. **Lesson Steps** (`/api/lesson-steps/{plan_id}/{day}/{slot}`)
   - Gets lesson steps for a specific day/slot
   - Required for Lesson Mode functionality

8. **Active Session** (`/api/lesson-mode/session/active`)
   - Gets active lesson mode session
   - Used for session persistence

### Integration Test

9. **Full Data Flow**
   - Tests complete flow: Plans → Detail → Schedule → Steps
   - Validates data structure and connectivity

## Expected Results

### ✅ All Tests Pass
```
✅ Health Check
✅ List Users
✅ Get User
✅ Recent Weeks
✅ List Plans
✅ Plan Detail
✅ Get Schedule
✅ List Slots
✅ Data Flow Integration

✅ ALL TESTS PASSED - Backend is ready for browser app!
```

### ⚠️ Warnings (OK)
- **No users found**: Database is empty. App will show empty user selector.
- **No plans found**: Database has no lesson plans. Browser will be empty.
- **No JSON files found**: No lesson plan JSON files detected. Only database plans will show.
- **No current lesson**: Outside class hours (expected).

### ❌ Failures (Fix Required)
- **Backend not running**: Start backend first
- **Connection errors**: Check backend URL/port
- **Missing fields**: Backend response format issue
- **HTTP errors**: Backend endpoint issue

## Troubleshooting

### Backend Not Running
```
❌ Health Check: Backend not running on http://localhost:8000
```
**Fix**: Start backend:
```powershell
python -m uvicorn backend.api:app --reload --port 8000
```

### Connection Errors
```
❌ List Users: Connection refused
```
**Fix**: 
- Check if backend is running on port 8000
- Check firewall settings
- Verify backend is accessible

### Missing Data
```
⚠️ No Users: Database is empty
⚠️ No Plans: Database has no lesson plans
```
**Fix**: These are warnings, not errors. The app will work but show empty views. Create test data if needed.

## Test Output Format

The test provides:
- ✅ **Passed tests** - Endpoint working correctly
- ❌ **Failed tests** - Endpoint not working (must fix)
- ⚠️ **Warnings** - Missing data but endpoint works (OK)

## Exit Codes

- `0` - All tests passed (backend ready)
- `1` - Some tests failed (fix backend issues)

## Integration with Development

This test should be run:
- Before starting Tauri app for first time
- After backend configuration changes
- After database migrations
- To verify JSON file detection works

## Next Steps

After tests pass:
1. Start backend (if not running)
2. Run `npm run tauri:dev` in `lesson-plan-browser/frontend`
3. App should connect to backend and load data

