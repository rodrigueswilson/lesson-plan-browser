# Complete RLS Setup - All Tables

## Overview

This guide enables Row Level Security (RLS) on all public tables and optimizes policies for better performance.

---

## Quick Fix - Run This SQL

Run `sql/enable_rls_all_tables.sql` in your Supabase SQL Editor. This will:

1. ✅ Enable RLS on all tables (`class_slots`, `users`, `weekly_plans`, `performance_metrics`)
2. ✅ Create optimized policies (using `(select auth.uid())` for better performance)
3. ✅ Fix function security (`set_updated_at_timestamp`)

---

## What Changed

### Performance Optimization

**Before (inefficient):**
```sql
USING (auth.uid()::text = user_id)  -- Evaluates for each row
```

**After (optimized):**
```sql
USING ((select auth.uid())::text = user_id)  -- Evaluates once per query
```

This prevents `auth.uid()` from being re-evaluated for every row, significantly improving query performance at scale.

---

## Tables Covered

### 1. `class_slots`
- ✅ RLS enabled
- ✅ Policies: SELECT, INSERT, UPDATE, DELETE
- ✅ Optimized with `(select auth.uid())`

### 2. `users`
- ✅ RLS enabled
- ✅ Policies: SELECT, UPDATE
- ✅ Optimized with `(select auth.uid())`

### 3. `weekly_plans`
- ✅ RLS enabled
- ✅ Policies: SELECT, INSERT, UPDATE, DELETE
- ✅ Optimized with `(select auth.uid())`

### 4. `performance_metrics`
- ✅ RLS enabled
- ✅ Policies: SELECT, INSERT, UPDATE
- ✅ Optimized with `(select auth.uid())`

---

## Function Security Fix

### `set_updated_at_timestamp`

Fixed the `search_path` security issue:

```sql
ALTER FUNCTION public.set_updated_at_timestamp()
SET search_path = public;
```

This prevents search_path injection attacks by explicitly setting the search path.

---

## Verification

After running the SQL, verify everything is set up correctly:

### Check RLS is Enabled

```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
ORDER BY tablename;
```

All should show `rowsecurity = true`.

### List All Policies

```sql
SELECT schemaname, tablename, policyname, cmd
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
ORDER BY tablename, cmd;
```

You should see policies for each table.

### Check Function Security

```sql
SELECT 
    n.nspname as schema,
    p.proname as function_name,
    p.proconfig as config
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' 
  AND p.proname = 'set_updated_at_timestamp';
```

Should show `search_path = public` in config.

---

## Testing

### Test 1: User Can Access Own Data

```sql
-- As authenticated user, should see only their data
SELECT * FROM public.class_slots;
SELECT * FROM public.users WHERE id = auth.uid()::text;
SELECT * FROM public.weekly_plans;
SELECT * FROM public.performance_metrics;
```

### Test 2: User Cannot Access Other Users' Data

```sql
-- Should return empty result sets
SELECT * FROM public.class_slots WHERE user_id != (select auth.uid())::text;
SELECT * FROM public.users WHERE id != (select auth.uid())::text;
```

### Test 3: User Can Create Own Records

```sql
-- Should succeed
INSERT INTO public.class_slots (id, user_id, ...)
VALUES ('test-id', (select auth.uid())::text, ...);
```

### Test 4: User Cannot Create Records for Others

```sql
-- Should fail with permission denied
INSERT INTO public.class_slots (id, user_id, ...)
VALUES ('test-id', 'other-user-id', ...);
```

---

## Important Notes

1. **Service Role Key**: If your backend uses the service role key, it bypasses RLS. This is safe as long as:
   - Service role key is NEVER exposed to frontend
   - Service role key is only used server-side
   - Your backend properly validates user access (which it does via `verify_user_access`)

2. **Performance**: The optimized policies using `(select auth.uid())` evaluate the user ID once per query instead of once per row, significantly improving performance.

3. **Migration**: After enabling RLS, test thoroughly in staging before production.

4. **Backup**: Always backup your database before making RLS changes.

---

## Rollback (if needed)

If you need to disable RLS:

```sql
ALTER TABLE public.class_slots DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics DISABLE ROW LEVEL SECURITY;
```

---

## Summary

✅ All tables have RLS enabled  
✅ All policies are optimized for performance  
✅ Function security is fixed  
✅ Ready for production  

All Supabase security warnings should now be resolved!

