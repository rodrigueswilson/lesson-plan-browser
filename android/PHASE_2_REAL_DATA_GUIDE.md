# Phase 2: Real Data Access - Troubleshooting Guide

## Current Status
The app is currently using **sample/mock data** because no real users were found in Supabase. The diagnostic screen shows:
- User ID: `local-test-user` (mock user)
- Sample plans and schedule entries

## Step 1: Check Supabase Connection

### Option A: Check Logs
When you open the app and it syncs, check the logs for:
```
Fetched X users from Supabase
```

If you see:
- `Fetched 0 users from Supabase` → Tables are empty OR RLS is blocking
- `Failed to fetch users` → Connection issue OR RLS policy error
- `Error type: SupabaseApiException` → Check error message for details

### Option B: Use Diagnostic Screen
1. Click the Bug icon in the Browser screen
2. Check the "Summary" section:
   - If "Users: 0" → No users in local database (sync may have failed)
   - If "Users: 1" and it's "Test User (Local)" → Real users not found

## Step 2: Verify Supabase Tables Have Data

### Check Project 1 (Wilson)
1. Go to Supabase Dashboard → Project 1
2. Navigate to Table Editor → `users` table
3. Check if there are any rows
4. Note the `id` values (e.g., user IDs like "wilson-rodrigues-id")

### Check Project 2 (Daniela)
1. Go to Supabase Dashboard → Project 2
2. Navigate to Table Editor → `users` table
3. Check if there are any rows
4. Note the `id` values

### Expected Data
You should see users like:
- Wilson Rodrigues (in Project 1)
- Daniela Silva (in Project 2)

## Step 3: Check RLS (Row Level Security) Policies

### What is RLS?
RLS policies control who can read/write data in Supabase tables. If policies are too restrictive, the app won't be able to read data.

### Check RLS Status
1. Go to Supabase Dashboard → Authentication → Policies
2. Select the `users` table
3. Check if there are any policies

### Common RLS Issues

**Issue 1: No Policies (Default: All Blocked)**
- **Symptom**: `Fetched 0 users` even though table has data
- **Fix**: Create a policy to allow SELECT for anonymous users:
  ```sql
  CREATE POLICY "Allow anonymous read" ON users
  FOR SELECT
  TO anon
  USING (true);
  ```

**Issue 2: Policies Require Authentication**
- **Symptom**: `Error: permission denied` or `RLS policy violation`
- **Fix**: Either:
  - Add anonymous access policy (see above)
  - OR implement authentication in the app

**Issue 3: Policies Filter by User ID**
- **Symptom**: Some users visible, others not
- **Fix**: Adjust policy to allow reading all users (for user selection screen)

### Recommended RLS Policy for User Selection

For the `users` table, you need a policy that allows reading all users (so users can select themselves):

```sql
-- Allow anonymous users to read all users (for selection screen)
CREATE POLICY "Allow anonymous read users" ON users
FOR SELECT
TO anon
USING (true);
```

Repeat for other tables:
- `weekly_plans`
- `lesson_steps`
- `schedule_entries`

## Step 4: Test Connection

### Manual Test Script
You can test the connection using the Python script we created earlier:
```bash
python tools/diagnostics/check_users_in_supabase.py
```

This will:
1. Connect to both Project 1 and Project 2
2. Query the `users` table
3. Show what users are found
4. Show any errors (including RLS errors)

### Expected Output
If working correctly:
```
Fetched 1 users from Project 1
  - Wilson Rodrigues (id: ...)
Fetched 1 users from Project 2
  - Daniela Silva (id: ...)
```

If RLS is blocking:
```
Error: permission denied for table users
```

## Step 5: Fix Issues

### If Tables Are Empty
1. Check if data exists in Supabase Dashboard
2. If not, you may need to:
   - Import data from another source
   - Use the PC app to generate lesson plans (which populates data)
   - Manually insert test data

### If RLS Is Blocking
1. Go to Supabase Dashboard → Authentication → Policies
2. Create policies for each table (see SQL above)
3. Test again

### If Connection Is Failing
1. Verify `local.properties` has correct URLs and keys
2. Check network connectivity
3. Verify Supabase projects are active

## Step 6: Verify Fix

After fixing RLS or populating data:

1. **Clear app data** (to remove mock user):
   ```bash
   adb shell pm clear com.bilingual.lessonplanner
   ```

2. **Reopen app** and check:
   - User selector should show real users (not "Test User (Local)")
   - Diagnostic screen should show real user IDs
   - Browser should show real lesson plans

3. **Check logs** for:
   ```
   Fetched 2 users from Supabase
   User: id=wilson-..., name=Wilson Rodrigues
   User: id=daniela-..., name=Daniela Silva
   ```

## Next Steps After Real Data Works

Once real data is flowing:
- ✅ Phase 2 Complete
- → Move to Phase 3: Parse `lesson_json` field
- → Move to Phase 4: Verify sync flow

## Troubleshooting Commands

### Check Recent Sync Logs
```powershell
adb -s emulator-5556 logcat -d | Select-String -Pattern "syncUsers|Fetched.*users|Supabase" | Select-Object -Last 20
```

### Clear App Data (Remove Mock User)
```powershell
adb shell pm clear com.bilingual.lessonplanner
```

### Monitor Live Logs
```powershell
adb -s emulator-5556 logcat | Select-String -Pattern "syncUsers|Supabase|RLS"
```

