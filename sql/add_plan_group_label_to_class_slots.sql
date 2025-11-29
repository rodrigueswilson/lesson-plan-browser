-- Add plan_group_label column to class_slots for linked lesson guidance
ALTER TABLE public.class_slots
ADD COLUMN IF NOT EXISTS plan_group_label TEXT;

