# RLS Testing Guide

## Overview

This guide helps you verify that Row Level Security (RLS) is working correctly and users can only access their own data.

---

## Prerequisites

1. ✅ RLS is enabled on all tables
2. ✅ All policies are created
3. ✅ Backend is running
4. ✅ Frontend is running (or use API directly)

---

## Test Scenarios

### Test 1: Verify Backend Authorization

The backend uses `verify_user_access` which works alongside RLS. Test that the API properly validates user access:

**Test Endpoint:**
```bash
# Get user's own class slots (should work)
curl -X GET "http://127.0.0.1:8000/api/users/{user_id}/slots" \
  -H "X-Current-User-Id: {user_id}"

# Try to access another user's slots (should fail)
curl -X GET "http://127.0.0.1:8000/api/users/{other_user_id}/slots" \
  -H "X-Current-User-Id: {user_id}"
```

**Expected:**
- ✅ Own data: Returns 200 OK with data
- ✅ Other user's data: Returns 403 Forbidden or empty result

---

### Test 2: Direct Database Access (PostgREST)

If using Supabase PostgREST directly, test that RLS blocks unauthorized access:

**As Authenticated User:**
```sql
-- Should only see own class slots
SELECT * FROM public.class_slots;
-- Should only return rows where user_id = auth.uid()

-- Should only see own weekly plans
SELECT * FROM public.weekly_plans;
-- Should only return rows where user_id = auth.uid()

-- Should only see own performance metrics
SELECT * FROM public.performance_metrics;
-- Should only return rows where plan_id belongs to user's weekly_plans
```

**Expected:**
- ✅ Only own data is visible
- ✅ Other users' data is filtered out by RLS

---

### Test 3: Frontend Application

1. **Login as User A**
   - Navigate to http://localhost:1420
   - Login/create account
   - Create some class slots
   - Create some weekly plans

2. **Verify User A sees only their data**
   - Check class slots list - should only show User A's slots
   - Check weekly plans - should only show User A's plans

3. **Login as User B** (different account)
   - Create different class slots and plans

4. **Verify User B sees only their data**
   - User B should NOT see User A's slots/plans
   - User B should only see their own data

---

### Test 4: API Endpoints

**Test with Swagger UI (http://127.0.0.1:8000/api/docs):**

1. **GET /api/users**
   - Should only return the current user (based on `X-Current-User-Id` header)

2. **GET /api/users/{user_id}/slots**
   - With correct `X-Current-User-Id`: Should return slots
   - With wrong `X-Current-User-Id`: Should return 403 or empty

3. **POST /api/users/{user_id}/slots**
   - Should only allow creating slots for the authenticated user

4. **PUT /api/users/{user_id}/slots/{slot_id}**
   - Should only allow updating own slots

5. **DELETE /api/users/{user_id}/slots/{slot_id}**
   - Should only allow deleting own slots

---

## Verification Checklist

- [ ] Backend is running
- [ ] Frontend is running (or using API directly)
- [ ] Can access own data via API
- [ ] Cannot access other users' data via API
- [ ] Database RLS policies are active
- [ ] No Supabase security warnings
- [ ] Application functions normally

---

## Troubleshooting

### Issue: Can't access any data

**Possible causes:**
1. RLS policies too restrictive
2. `auth.uid()` not set correctly
3. User ID format mismatch

**Check:**
```sql
-- Verify current user
SELECT auth.uid();

-- Check if policies are too restrictive
SELECT * FROM pg_policies 
WHERE tablename = 'class_slots';
```

### Issue: Can access other users' data

**Possible causes:**
1. RLS not enabled
2. Policies not created
3. Using service role key (bypasses RLS)

**Check:**
```sql
-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'class_slots';

-- Verify policies exist
SELECT * FROM pg_policies 
WHERE tablename = 'class_slots';
```

### Issue: Service role key bypasses RLS

**This is expected!** Service role key bypasses RLS by design. This is safe as long as:
- Service role key is NEVER exposed to frontend
- Backend properly validates access (which it does via `verify_user_access`)

---

## Expected Behavior

### ✅ Correct Behavior

- Users can only see their own data
- Users can only create/update/delete their own data
- API returns 403 Forbidden for unauthorized access
- Database filters rows automatically via RLS

### ❌ Incorrect Behavior

- Users can see other users' data
- Users can modify other users' data
- No errors when accessing unauthorized data
- RLS warnings in Supabase dashboard

---

## Summary

After testing, you should confirm:
- ✅ RLS is working at database level
- ✅ Backend authorization is working
- ✅ Users can only access their own data
- ✅ Application functions normally
- ✅ No security warnings

Your database is now properly secured!

