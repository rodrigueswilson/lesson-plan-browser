-- Create schedules table for Supabase
-- Run this SQL in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    subject TEXT NOT NULL,
    homeroom TEXT,
    grade TEXT,
    plan_slot_group_id TEXT,
    slot_number INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_schedules_user_day ON schedules(user_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_user_time ON schedules(user_id, day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_schedules_current ON schedules(user_id, is_active, day_of_week, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_schedules_homeroom ON schedules(user_id, homeroom, day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_grade ON schedules(user_id, grade, day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_plan_group ON schedules(plan_slot_group_id);

-- Enable Row Level Security (if using RLS)
-- ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (adjust based on your security requirements)
-- Policy: Users can only see their own schedules
-- CREATE POLICY "Users can view own schedules" ON schedules
--     FOR SELECT USING (auth.uid()::text = user_id);

-- Policy: Users can insert their own schedules
-- CREATE POLICY "Users can insert own schedules" ON schedules
--     FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- Policy: Users can update their own schedules
-- CREATE POLICY "Users can update own schedules" ON schedules
--     FOR UPDATE USING (auth.uid()::text = user_id);

-- Policy: Users can delete their own schedules
-- CREATE POLICY "Users can delete own schedules" ON schedules
--     FOR DELETE USING (auth.uid()::text = user_id);

