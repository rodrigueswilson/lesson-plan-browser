-- Verification queries for RLS setup
-- Run these to confirm everything is configured correctly

-- ============================================================================
-- 1. Check RLS is enabled on all tables
-- ============================================================================
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
ORDER BY tablename;

-- Expected result: All tables should show rls_enabled = true

-- ============================================================================
-- 2. List all RLS policies
-- ============================================================================
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd as operation,
    permissive
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
ORDER BY tablename, cmd;

-- Expected result: Should see policies for SELECT, INSERT, UPDATE, DELETE on each table

-- ============================================================================
-- 3. Check function search_path is set
-- ============================================================================
SELECT 
    n.nspname as schema,
    p.proname as function_name,
    CASE 
        WHEN p.proconfig IS NULL THEN 'search_path not set'
        ELSE array_to_string(p.proconfig, ', ')
    END as config
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' 
  AND p.proname = 'set_updated_at_timestamp';

-- Expected result: Should show search_path = public in config

-- ============================================================================
-- 4. Count policies per table
-- ============================================================================
SELECT 
    tablename,
    COUNT(*) as policy_count,
    STRING_AGG(cmd::text, ', ' ORDER BY cmd) as operations
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
GROUP BY tablename
ORDER BY tablename;

-- Expected result:
-- class_slots: 4 policies (SELECT, INSERT, UPDATE, DELETE)
-- users: 2 policies (SELECT, UPDATE)
-- weekly_plans: 4 policies (SELECT, INSERT, UPDATE, DELETE)
-- performance_metrics: 3 policies (SELECT, INSERT, UPDATE)

