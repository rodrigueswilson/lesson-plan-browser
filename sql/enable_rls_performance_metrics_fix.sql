-- Fix RLS policies for performance_metrics table
-- This table doesn't have user_id directly - it references weekly_plans via plan_id
-- Run this AFTER running enable_rls_all_tables.sql (or if you get the user_id error)

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own metrics" ON public.performance_metrics;
DROP POLICY IF EXISTS "Users can create their own metrics" ON public.performance_metrics;
DROP POLICY IF EXISTS "Users can update their own metrics" ON public.performance_metrics;
DROP POLICY IF EXISTS "Users can delete their own metrics" ON public.performance_metrics;

-- Enable RLS (if not already enabled)
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- Create policies that check user_id through the weekly_plans relationship
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

-- Note: DELETE policy commented out (metrics are usually append-only)
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

