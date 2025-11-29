-- Row-Level Security (RLS) Policies for Supabase
-- 
-- IMPORTANT: These policies are prepared for future use when Supabase Auth is integrated.
-- They will NOT work until:
-- 1. Supabase Auth is enabled and users authenticate via JWT tokens
-- 2. The backend uses anon key (not service_role key) for client requests
-- 3. Requests include valid JWT tokens with auth.uid()
--
-- Current Status: RLS is DISABLED because:
-- - Backend uses service_role key (bypasses RLS)
-- - No Supabase Auth integration yet
-- - Desktop app architecture doesn't require RLS at this time
--
-- When to enable:
-- - When migrating to web/multi-user cloud architecture
-- - When implementing Supabase Auth
-- - When removing service_role key from client-side code

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================================================

-- Uncomment these lines when ready to enable RLS:
-- ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.weekly_plans ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- USERS TABLE POLICIES
-- ============================================================================

-- Users can read their own profile
-- Note: id column is TEXT, auth.uid() returns UUID, so we cast both to text for comparison
-- CREATE POLICY "users_select_own" ON public.users
--     FOR SELECT
--     TO authenticated
--     USING (auth.uid()::text = id);

-- Users can update their own profile
-- CREATE POLICY "users_update_own" ON public.users
--     FOR UPDATE
--     TO authenticated
--     USING (auth.uid()::text = id)
--     WITH CHECK (auth.uid()::text = id);

-- Users can delete their own profile
-- CREATE POLICY "users_delete_own" ON public.users
--     FOR DELETE
--     TO authenticated
--     USING (auth.uid()::text = id);

-- Note: User creation might be handled by Supabase Auth, so INSERT policy may not be needed
-- If you need to allow users to create profiles after auth signup:
-- CREATE POLICY "users_insert_own" ON public.users
--     FOR INSERT
--     TO authenticated
--     WITH CHECK (auth.uid()::text = id);

-- ============================================================================
-- CLASS_SLOTS TABLE POLICIES
-- ============================================================================

-- Users can read their own class slots
-- CREATE POLICY "class_slots_select_own" ON public.class_slots
--     FOR SELECT
--     TO authenticated
--     USING (auth.uid()::text = user_id);

-- Users can create slots for themselves
-- CREATE POLICY "class_slots_insert_own" ON public.class_slots
--     FOR INSERT
--     TO authenticated
--     WITH CHECK (auth.uid()::text = user_id);

-- Users can update their own slots
-- CREATE POLICY "class_slots_update_own" ON public.class_slots
--     FOR UPDATE
--     TO authenticated
--     USING (auth.uid()::text = user_id)
--     WITH CHECK (auth.uid()::text = user_id);

-- Users can delete their own slots
-- CREATE POLICY "class_slots_delete_own" ON public.class_slots
--     FOR DELETE
--     TO authenticated
--     USING (auth.uid()::text = user_id);

-- ============================================================================
-- WEEKLY_PLANS TABLE POLICIES
-- ============================================================================

-- Users can read their own weekly plans
-- CREATE POLICY "weekly_plans_select_own" ON public.weekly_plans
--     FOR SELECT
--     TO authenticated
--     USING (auth.uid()::text = user_id);

-- Users can create plans for themselves
-- CREATE POLICY "weekly_plans_insert_own" ON public.weekly_plans
--     FOR INSERT
--     TO authenticated
--     WITH CHECK (auth.uid()::text = user_id);

-- Users can update their own plans
-- CREATE POLICY "weekly_plans_update_own" ON public.weekly_plans
--     FOR UPDATE
--     TO authenticated
--     USING (auth.uid()::text = user_id)
--     WITH CHECK (auth.uid()::text = user_id);

-- Users can delete their own plans
-- CREATE POLICY "weekly_plans_delete_own" ON public.weekly_plans
--     FOR DELETE
--     TO authenticated
--     USING (auth.uid()::text = user_id);

-- ============================================================================
-- PERFORMANCE_METRICS TABLE POLICIES
-- ============================================================================

-- Users can read metrics for their own plans
-- CREATE POLICY "performance_metrics_select_own" ON public.performance_metrics
--     FOR SELECT
--     TO authenticated
--     USING (
--         EXISTS (
--             SELECT 1 FROM public.weekly_plans wp
--             WHERE wp.id = performance_metrics.plan_id
--             AND wp.user_id = auth.uid()::text
--         )
--     );

-- Users can insert metrics for their own plans
-- CREATE POLICY "performance_metrics_insert_own" ON public.performance_metrics
--     FOR INSERT
--     TO authenticated
--     WITH CHECK (
--         EXISTS (
--             SELECT 1 FROM public.weekly_plans wp
--             WHERE wp.id = performance_metrics.plan_id
--             AND wp.user_id = auth.uid()::text
--         )
--     );

-- Note: UPDATE and DELETE policies for metrics are typically not needed
-- as metrics are usually append-only. Add them if your use case requires it.

-- ============================================================================
-- INDEXES FOR POLICY PERFORMANCE
-- ============================================================================

-- These indexes help RLS policies perform efficiently
-- They should already exist from your schema, but verify:

-- CREATE INDEX IF NOT EXISTS idx_class_slots_user_id ON public.class_slots(user_id);
-- CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON public.weekly_plans(user_id);
-- CREATE INDEX IF NOT EXISTS idx_performance_metrics_plan_id ON public.performance_metrics(plan_id);

-- ============================================================================
-- TESTING POLICIES
-- ============================================================================

-- After enabling RLS and creating policies, test with:

-- 1. As authenticated user (replace USER_UUID with actual user ID):
--    SET ROLE authenticated;
--    SET request.jwt.claim.sub = 'USER_UUID';
--    SELECT * FROM public.class_slots;  -- Should only see own slots
--    
-- 2. As anonymous user:
--    SET ROLE anon;
--    SELECT * FROM public.class_slots;  -- Should see nothing (no policies for anon)

-- ============================================================================
-- MIGRATION CHECKLIST
-- ============================================================================

-- Before enabling RLS:
-- [ ] Supabase Auth is configured and working
-- [ ] Backend uses anon key for client requests (not service_role)
-- [ ] Frontend sends JWT tokens in Authorization header
-- [ ] Backend extracts auth.uid() from JWT for user identification
-- [ ] All policies are tested with real user accounts
-- [ ] Service role key is removed from client-side code
-- [ ] Service role key is only used for admin/server operations

-- After enabling RLS:
-- [ ] Verify users can only access their own data
-- [ ] Verify users cannot access other users' data
-- [ ] Monitor for any authorization errors
-- [ ] Update backend authorization checks to work with RLS
-- [ ] Document the new authentication flow

