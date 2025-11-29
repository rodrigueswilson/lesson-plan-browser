CREATE TABLE IF NOT EXISTS lesson_mode_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    lesson_plan_id TEXT NOT NULL,
    schedule_entry_id TEXT,
    day_of_week TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    current_step_index INTEGER NOT NULL DEFAULT 0,
    remaining_time INTEGER NOT NULL DEFAULT 0,
    is_running INTEGER NOT NULL DEFAULT 0,
    is_paused INTEGER NOT NULL DEFAULT 0,
    is_synced INTEGER NOT NULL DEFAULT 0,
    timer_start_time TEXT,
    paused_at INTEGER,
    adjusted_durations TEXT,
    session_start_time TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    ended_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_entry_id) REFERENCES schedules(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_user_id 
ON lesson_mode_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_plan_id 
ON lesson_mode_sessions(lesson_plan_id);

CREATE INDEX IF NOT EXISTS idx_lesson_mode_sessions_active 
ON lesson_mode_sessions(user_id, ended_at)
WHERE ended_at IS NULL;

