-- Enable Row Level Security (RLS) for ALL tables
-- Optimized policies with (select auth.uid()) for better performance
-- Run this in Supabase SQL Editor

-- ============================================================================
-- CLASS_SLOTS TABLE
-- ============================================================================

-- Enable RLS
ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to recreate with optimized version)
DROP POLICY IF EXISTS "Users can view their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can create their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can update their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can delete their own class slots" ON public.class_slots;

-- Create optimized policies (using SELECT to evaluate auth.uid() once per query)
CREATE POLICY "Users can view their own class slots"
ON public.class_slots
FOR SELECT
USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can create their own class slots"
ON public.class_slots
FOR INSERT
WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update their own class slots"
ON public.class_slots
FOR UPDATE
USING ((select auth.uid())::text = user_id)
WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete their own class slots"
ON public.class_slots
FOR DELETE
USING ((select auth.uid())::text = user_id);

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own data"
ON public.users
FOR SELECT
USING ((select auth.uid())::text = id);

CREATE POLICY "Users can update their own data"
ON public.users
FOR UPDATE
USING ((select auth.uid())::text = id)
WITH CHECK ((select auth.uid())::text = id);

-- Note: INSERT policy may not be needed if users are created server-side only
-- Uncomment if users can self-register:
-- CREATE POLICY "Users can create their own account"
-- ON public.users
-- FOR INSERT
-- WITH CHECK ((select auth.uid())::text = id);

-- ============================================================================
-- WEEKLY_PLANS TABLE
-- ============================================================================

-- Enable RLS
ALTER TABLE public.weekly_plans ENABLE ROW LEVEL SECURITY;

-- Create policies for weekly_plans table
CREATE POLICY "Users can view their own weekly plans"
ON public.weekly_plans
FOR SELECT
USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can create their own weekly plans"
ON public.weekly_plans
FOR INSERT
WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update their own weekly plans"
ON public.weekly_plans
FOR UPDATE
USING ((select auth.uid())::text = user_id)
WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete their own weekly plans"
ON public.weekly_plans
FOR DELETE
USING ((select auth.uid())::text = user_id);

-- ============================================================================
-- PERFORMANCE_METRICS TABLE
-- ============================================================================
-- Note: performance_metrics doesn't have user_id directly
-- It references weekly_plans via plan_id, so we check through that relationship

-- Enable RLS
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- Create policies for performance_metrics table
-- Check user_id through the weekly_plans relationship
CREATE POLICY "Users can view their own metrics"
ON public.performance_metrics
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.weekly_plans
        WHERE weekly_plans.id = performance_metrics.plan_id
        AND weekly_plans.user_id = (select auth.uid())::text
    )
);

CREATE POLICY "Users can create their own metrics"
ON public.performance_metrics
FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.weekly_plans
        WHERE weekly_plans.id = performance_metrics.plan_id
        AND weekly_plans.user_id = (select auth.uid())::text
    )
);

CREATE POLICY "Users can update their own metrics"
ON public.performance_metrics
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM public.weekly_plans
        WHERE weekly_plans.id = performance_metrics.plan_id
        AND weekly_plans.user_id = (select auth.uid())::text
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.weekly_plans
        WHERE weekly_plans.id = performance_metrics.plan_id
        AND weekly_plans.user_id = (select auth.uid())::text
    )
);

-- Note: DELETE policy may not be needed for metrics (usually append-only)
-- Uncomment if users should be able to delete their metrics:
-- CREATE POLICY "Users can delete their own metrics"
-- ON public.performance_metrics
-- FOR DELETE
-- USING (
--     EXISTS (
--         SELECT 1 FROM public.weekly_plans
--         WHERE weekly_plans.id = performance_metrics.plan_id
--         AND weekly_plans.user_id = (select auth.uid())::text
--     )
-- );

-- ============================================================================
-- FUNCTION SECURITY FIX
-- ============================================================================

-- Fix search_path for set_updated_at_timestamp function
-- This prevents search_path injection attacks
ALTER FUNCTION public.set_updated_at_timestamp()
SET search_path = public;

-- ============================================================================
-- VERIFICATION QUERIES (run separately to verify)
-- ============================================================================

-- Check RLS is enabled on all tables:
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public' 
--   AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
-- ORDER BY tablename;

-- List all policies:
-- SELECT schemaname, tablename, policyname, cmd
-- FROM pg_policies
-- WHERE schemaname = 'public' 
--   AND tablename IN ('class_slots', 'users', 'weekly_plans', 'performance_metrics')
-- ORDER BY tablename, cmd;

-- Check function search_path:
-- SELECT 
--     n.nspname as schema,
--     p.proname as function_name,
--     pg_get_functiondef(p.oid) as definition
-- FROM pg_proc p
-- JOIN pg_namespace n ON p.pronamespace = n.oid
-- WHERE n.nspname = 'public' 
--   AND p.proname = 'set_updated_at_timestamp';

