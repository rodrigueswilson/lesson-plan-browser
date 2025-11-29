# Enable Row Level Security (RLS) for class_slots Table

## Issue

Supabase is warning that `public.class_slots` table is exposed to PostgREST but RLS is not enabled. This is a security risk as it allows unauthorized access to the table.

## Solution

Enable RLS and create appropriate policies for the `class_slots` table.

---

## Step 1: Enable RLS on class_slots

Run this SQL in your Supabase SQL Editor:

```sql
-- Enable Row Level Security on class_slots table
ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;
```

---

## Step 2: Create RLS Policies

Based on the table structure, create policies that allow users to:
- **SELECT**: View only their own class slots
- **INSERT**: Create class slots for themselves
- **UPDATE**: Update only their own class slots
- **DELETE**: Delete only their own class slots

### Policy 1: SELECT (Read Own Slots)

```sql
-- Users can only view their own class slots
CREATE POLICY "Users can view their own class slots"
ON public.class_slots
FOR SELECT
USING (auth.uid()::text = user_id);
```

### Policy 2: INSERT (Create Own Slots)

```sql
-- Users can only create class slots for themselves
CREATE POLICY "Users can create their own class slots"
ON public.class_slots
FOR INSERT
WITH CHECK (auth.uid()::text = user_id);
```

### Policy 3: UPDATE (Update Own Slots)

```sql
-- Users can only update their own class slots
CREATE POLICY "Users can update their own class slots"
ON public.class_slots
FOR UPDATE
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);
```

### Policy 4: DELETE (Delete Own Slots)

```sql
-- Users can only delete their own class slots
CREATE POLICY "Users can delete their own class slots"
ON public.class_slots
FOR DELETE
USING (auth.uid()::text = user_id);
```

---

## Step 3: Verify RLS is Enabled

Run this query to verify:

```sql
-- Check if RLS is enabled
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename = 'class_slots';
```

Expected result: `rowsecurity = true`

---

## Step 4: Verify Policies

```sql
-- List all policies on class_slots
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename = 'class_slots';
```

You should see 4 policies (SELECT, INSERT, UPDATE, DELETE).

---

## Alternative: If Using Service Role Key

If your application uses the service role key (server-side only), you may need different policies or to allow service role bypass:

```sql
-- Allow service role to bypass RLS (server-side operations)
-- This is safe if service role key is only used server-side
-- DO NOT expose service role key to client-side code!

-- Service role automatically bypasses RLS, so no policy needed
-- But ensure service role key is NEVER exposed to frontend
```

---

## Testing RLS Policies

### Test 1: User Can View Own Slots

```sql
-- As authenticated user, should see only their slots
SELECT * FROM public.class_slots;
-- Should only return rows where user_id = auth.uid()::text
```

### Test 2: User Cannot View Other Users' Slots

```sql
-- As authenticated user, try to access another user's slot
SELECT * FROM public.class_slots WHERE user_id != auth.uid()::text;
-- Should return empty result set
```

### Test 3: User Can Create Own Slot

```sql
-- As authenticated user, create a slot
INSERT INTO public.class_slots (id, user_id, ...)
VALUES ('test-id', auth.uid()::text, ...);
-- Should succeed
```

### Test 4: User Cannot Create Slot for Another User

```sql
-- As authenticated user, try to create slot for another user
INSERT INTO public.class_slots (id, user_id, ...)
VALUES ('test-id', 'other-user-id', ...);
-- Should fail with permission denied
```

---

## Other Tables to Check

You should also enable RLS on other public tables:

- `public.users` - User data
- `public.weekly_plans` - Weekly lesson plans
- `public.performance_metrics` - Performance tracking

---

## Complete RLS Setup Script

Here's a complete script to enable RLS on all tables:

```sql
-- Enable RLS on all public tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- Create policies for class_slots (see above)

-- Create policies for users table
CREATE POLICY "Users can view their own data"
ON public.users FOR SELECT
USING (auth.uid()::text = id);

CREATE POLICY "Users can update their own data"
ON public.users FOR UPDATE
USING (auth.uid()::text = id)
WITH CHECK (auth.uid()::text = id);

-- Create policies for weekly_plans table
CREATE POLICY "Users can view their own weekly plans"
ON public.weekly_plans FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can create their own weekly plans"
ON public.weekly_plans FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own weekly plans"
ON public.weekly_plans FOR UPDATE
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);

-- Create policies for performance_metrics table
CREATE POLICY "Users can view their own metrics"
ON public.performance_metrics FOR SELECT
USING (auth.uid()::text = user_id);
```

---

## Important Notes

1. **Service Role Key**: If your backend uses the service role key, it bypasses RLS. This is safe as long as:
   - Service role key is NEVER exposed to frontend
   - Service role key is only used server-side
   - Your backend properly validates user access (which it does via `verify_user_access`)

2. **Migration**: After enabling RLS, test thoroughly in staging before production.

3. **Backup**: Always backup your database before making RLS changes.

4. **Rollback**: If needed, you can disable RLS:
   ```sql
   ALTER TABLE public.class_slots DISABLE ROW LEVEL SECURITY;
   ```

---

## Next Steps

1. ✅ Run the SQL to enable RLS on `class_slots`
2. ✅ Create the 4 policies (SELECT, INSERT, UPDATE, DELETE)
3. ✅ Verify RLS is enabled
4. ✅ Test policies in staging
5. ✅ Enable RLS on other tables (`users`, `weekly_plans`, `performance_metrics`)
6. ✅ Update production after staging validation

---

## References

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

