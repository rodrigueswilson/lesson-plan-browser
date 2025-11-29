-- Run manually inside Supabase SQL editor whenever deploying lesson-step updates.
CREATE TABLE IF NOT EXISTS lesson_steps (
    id TEXT PRIMARY KEY,
    lesson_plan_id TEXT NOT NULL REFERENCES weekly_plans(id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    start_time_offset INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    display_content TEXT NOT NULL,
    hidden_content JSONB,
    sentence_frames JSONB,
    materials_needed JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lesson_plan_id, day_of_week, slot_number, step_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_day_slot 
ON lesson_steps(lesson_plan_id, day_of_week, slot_number);

CREATE INDEX IF NOT EXISTS idx_lesson_steps_plan_id 
ON lesson_steps(lesson_plan_id);

