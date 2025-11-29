-- Run manually inside Supabase SQL editor whenever deploying lesson-mode-session updates.
CREATE TABLE IF NOT EXISTS lesson_mode_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_plan_id TEXT NOT NULL REFERENCES weekly_plans(id) ON DELETE CASCADE,
    schedule_entry_id TEXT REFERENCES schedules(id) ON DELETE SET NULL,
    day_of_week TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    current_step_index INTEGER NOT NULL DEFAULT 0,
    remaining_time INTEGER NOT NULL DEFAULT 0,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    is_paused BOOLEAN NOT NULL DEFAULT FALSE,
    is_synced BOOLEAN NOT NULL DEFAULT FALSE,
    timer_start_time TIMESTAMP WITH TIME ZONE,
    paused_at INTEGER,
    adjusted_durations JSONB,
    session_start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_user_id 
ON lesson_mode_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_plan_id 
ON lesson_mode_sessions(lesson_plan_id);

CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_active 
ON lesson_mode_sessions(user_id, ended_at)
WHERE ended_at IS NULL;

