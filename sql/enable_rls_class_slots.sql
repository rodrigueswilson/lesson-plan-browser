-- Enable Row Level Security (RLS) for class_slots table
-- Run this in Supabase SQL Editor

-- Step 1: Enable RLS
ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;

-- Step 2: Drop existing policies if they exist (to recreate with optimized version)
DROP POLICY IF EXISTS "Users can view their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can create their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can update their own class slots" ON public.class_slots;
DROP POLICY IF EXISTS "Users can delete their own class slots" ON public.class_slots;

-- Step 3: Create optimized SELECT policy (using SELECT to evaluate auth.uid() once per query)
CREATE POLICY "Users can view their own class slots"
ON public.class_slots
FOR SELECT
USING ((select auth.uid())::text = user_id);

-- Step 4: Create optimized INSERT policy
CREATE POLICY "Users can create their own class slots"
ON public.class_slots
FOR INSERT
WITH CHECK ((select auth.uid())::text = user_id);

-- Step 5: Create optimized UPDATE policy
CREATE POLICY "Users can update their own class slots"
ON public.class_slots
FOR UPDATE
USING ((select auth.uid())::text = user_id)
WITH CHECK ((select auth.uid())::text = user_id);

-- Step 6: Create optimized DELETE policy
CREATE POLICY "Users can delete their own class slots"
ON public.class_slots
FOR DELETE
USING ((select auth.uid())::text = user_id);

-- Verification queries (run separately to verify):

-- Check RLS is enabled:
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public' AND tablename = 'class_slots';

-- List all policies:
-- SELECT schemaname, tablename, policyname, cmd
-- FROM pg_policies
-- WHERE schemaname = 'public' AND tablename = 'class_slots';

