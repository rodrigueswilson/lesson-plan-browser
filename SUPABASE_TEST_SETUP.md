# Supabase Testing Setup Guide

This guide will help you test the Supabase integration with automatic project selection.

## Prerequisites

1. **Two Supabase Projects Created**
   - Project 1: For Wilson Rodrigues
   - Project 2: For Daniela Silva

2. **Database Schema Applied**
   - Run the SQL schema in each Supabase project's SQL Editor
   - Schema file: `docs/supabase_schema.sql`

## Step 1: Get Your Supabase Credentials

For each project, you need:

1. **Project URL**: Found in Settings → API → Project URL
   - Example: `https://xxxxx.supabase.co`

2. **Anon Key**: Found in Settings → API → Project API keys → `anon` `public`
   - This is the public key for client-side access

3. **Service Role Key** (Optional): Found in Settings → API → Project API keys → `service_role` `secret`
   - Only needed for admin operations
   - Keep this secret!

## Step 2: Create .env File

Create a `.env` file in the project root (`D:\LP\.env`) with the following:

```env
# Enable Supabase
USE_SUPABASE=True

# Project 1 (Wilson Rodrigues)
SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
SUPABASE_KEY_PROJECT1=your-project1-anon-key-here
SUPABASE_SERVICE_ROLE_KEY_PROJECT1=your-project1-service-role-key-here

# Project 2 (Daniela Silva)
SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
SUPABASE_KEY_PROJECT2=your-project2-anon-key-here
SUPABASE_SERVICE_ROLE_KEY_PROJECT2=your-project2-service-role-key-here

# Default project (used when user_id not found)
SUPABASE_PROJECT=project1
```

## Step 3: Verify Database Schema

In each Supabase project's SQL Editor, run the schema from `docs/supabase_schema.sql`.

Verify tables exist:
- `users`
- `class_slots`
- `weekly_plans`
- `performance_metrics`

## Step 4: Create Test Users

You can either:

**Option A: Create users via API** (recommended)
```bash
# Create Wilson in Project 1
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Wilson", "last_name": "Rodrigues", "email": "wilson@test.com"}'

# Create Daniela in Project 2
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Daniela", "last_name": "Silva", "email": "daniela@test.com"}'
```

**Option B: Create users in Supabase Dashboard**
- Go to Table Editor → `users` table
- Insert rows manually
- Make sure to use UUIDs for IDs

## Step 5: Run Tests

1. **Restart Backend** (to load new .env settings)
   ```bash
   # Stop current backend, then restart
   python -m uvicorn backend.api:app --reload
   ```

2. **Run Test Script**
   ```bash
   python test_supabase_integration.py
   ```

3. **Expected Results**
   - All tests should pass
   - Project isolation test should verify users are in different projects
   - Automatic project selection should work

## Step 6: Test in Frontend

1. **Refresh Frontend** (or restart if needed)

2. **Test User Switching**
   - Select Wilson → should use Project 1
   - Select Daniela → should use Project 2
   - Create slots/plans for each user
   - Verify data is isolated

3. **Check Browser Console**
   - Look for any errors
   - Verify API calls include `user_id` parameter

## Troubleshooting

### "User not found in either project"
- Verify users exist in Supabase dashboard
- Check user IDs match between SQLite and Supabase
- Verify SUPABASE_URL_PROJECT1/2 are correct

### "Table does not exist"
- Run the schema SQL in Supabase SQL Editor
- Check table names match exactly

### "Connection refused" or "Invalid API key"
- Verify SUPABASE_URL_PROJECT1/2 are correct (no trailing slash)
- Verify SUPABASE_KEY_PROJECT1/2 are the `anon` keys (not service_role)
- Check Supabase project is active (not paused)

### Backend still using SQLite
- Verify `.env` file exists in project root
- Check `USE_SUPABASE=True` (not `true` or `True` with quotes)
- Restart backend after changing .env

## Verification Checklist

- [ ] Two Supabase projects created
- [ ] Database schema applied to both projects
- [ ] `.env` file created with correct credentials
- [ ] Backend restarted with new settings
- [ ] Test users created (Wilson & Daniela)
- [ ] Test script passes all tests
- [ ] Frontend can switch between users
- [ ] Data is isolated per project
- [ ] Automatic project selection works

## Next Steps After Testing

Once testing passes:
1. Migrate existing SQLite data (if needed)
2. Configure Android app to use Supabase REST API
3. Set up automated backups
4. Monitor performance and costs

