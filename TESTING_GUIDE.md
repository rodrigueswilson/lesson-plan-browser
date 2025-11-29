# Supabase Integration Testing Guide

This guide helps you test the Supabase integration with automatic project selection.

## Prerequisites

1. **Backend running**: Start the FastAPI backend
   ```bash
   python -m uvicorn backend.api:app --reload
   ```
   Or use the batch file:
   ```bash
   start-backend.bat
   ```

2. **Supabase configured**: Ensure your `.env` file has:
   ```env
   USE_SUPABASE=True
   SUPABASE_URL_PROJECT1=https://your-project1.supabase.co
   SUPABASE_KEY_PROJECT1=your-project1-key
   SUPABASE_URL_PROJECT2=https://your-project2.supabase.co
   SUPABASE_KEY_PROJECT2=your-project2-key
   ```

3. **Users exist**: Make sure Wilson and Daniela users exist in their respective Supabase projects

## Quick Test

Run the comprehensive test script:

```bash
python test_supabase_integration.py
```

This will test:
- ✅ Backend connectivity
- ✅ User CRUD operations
- ✅ Slot operations
- ✅ Plan operations
- ✅ Recent weeks detection
- ✅ Project isolation (automatic project selection)

## Manual Testing Steps

### 1. Test User Switching

**Test Wilson (Project 1):**
```bash
# Get Wilson's user ID
curl http://127.0.0.1:8000/api/users

# Get Wilson's slots (should use project1 automatically)
curl http://127.0.0.1:8000/api/users/{wilson_user_id}/slots

# Get Wilson's plans
curl http://127.0.0.1:8000/api/users/{wilson_user_id}/plans
```

**Test Daniela (Project 2):**
```bash
# Get Daniela's slots (should use project2 automatically)
curl http://127.0.0.1:8000/api/users/{daniela_user_id}/slots

# Get Daniela's plans
curl http://127.0.0.1:8000/api/users/{daniela_user_id}/plans
```

### 2. Test Data Isolation

Verify that:
- Wilson's data is stored in Project 1
- Daniela's data is stored in Project 2
- Switching between users automatically selects the correct project

### 3. Test Lesson Plan Generation

**Generate a plan for Wilson:**
```bash
curl -X POST http://127.0.0.1:8000/api/process-week \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{wilson_user_id}",
    "week_of": "2025-01-20",
    "provider": "openai"
  }'
```

**Check the plan was created in Project 1:**
```bash
curl http://127.0.0.1:8000/api/users/{wilson_user_id}/plans
```

**Generate a plan for Daniela:**
```bash
curl -X POST http://127.0.0.1:8000/api/process-week \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{daniela_user_id}",
    "week_of": "2025-01-20",
    "provider": "openai"
  }'
```

**Verify it's in Project 2:**
```bash
curl http://127.0.0.1:8000/api/users/{daniela_user_id}/plans
```

### 4. Test Frontend Integration

1. **Start the frontend:**
   ```bash
   cd frontend
   npm run tauri dev
   ```

2. **Switch users in the app:**
   - Select Wilson from user dropdown
   - Create a slot or generate a plan
   - Switch to Daniela
   - Verify data is separate

3. **Verify automatic project selection:**
   - Check browser console/network tab
   - API calls should include `user_id` parameter
   - Backend should automatically select correct project

## Expected Results

### ✅ Success Indicators

- Both users can be accessed without manual project switching
- Data is isolated per user/project
- API endpoints work correctly with `user_id` parameter
- No errors in backend logs about project selection
- Frontend can switch between users seamlessly

### ❌ Failure Indicators

- "User not found" errors when user exists
- Data from one user appearing for another user
- Backend errors about project configuration
- API calls failing with 500 errors
- Frontend unable to load user data

## Troubleshooting

### Backend Not Running
```
Error: Cannot connect to backend
Solution: Start backend with `python -m uvicorn backend.api:app --reload`
```

### User Not Found
```
Error: User not found in either project
Solution: 
1. Check user exists in Supabase dashboard
2. Verify user_id is correct
3. Check SUPABASE_URL_PROJECT1/2 are set correctly
```

### Wrong Project Selected
```
Error: Data appears in wrong project
Solution:
1. Check _find_user_project() function
2. Verify user_project_cache is working
3. Check SUPABASE_PROJECT environment variable
```

### API Errors
```
Error: 500 Internal Server Error
Solution:
1. Check backend logs for detailed error
2. Verify Supabase credentials are correct
3. Check database schema matches expected structure
```

## Next Steps After Testing

Once testing passes:

1. ✅ **Test API endpoints with Supabase backend** - DONE
2. ✅ **Test creating users, slots, and plans** - DONE
3. ✅ **Verify data syncs correctly** - DONE
4. ⏭️ **Configure Android app to use Supabase REST API**
5. ⏭️ **Set up automated backups**
6. ⏭️ **Monitor performance and costs**

## Additional Resources

- Supabase Dashboard: https://app.supabase.com
- API Documentation: http://127.0.0.1:8000/api/docs
- Supabase Setup Guide: `docs/supabase_setup.md`
- Cross-Platform Plan: `CROSS_PLATFORM_PLAN.md`

