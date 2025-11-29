-- Add plan_slot_group_id column to existing schedules table
ALTER TABLE public.schedules
ADD COLUMN IF NOT EXISTS plan_slot_group_id TEXT;

CREATE INDEX IF NOT EXISTS idx_schedules_plan_group
ON public.schedules(plan_slot_group_id);

