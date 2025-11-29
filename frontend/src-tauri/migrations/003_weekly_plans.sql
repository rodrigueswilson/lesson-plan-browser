CREATE TABLE IF NOT EXISTS weekly_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    output_file TEXT,
    week_folder_path TEXT,
    consolidated INTEGER NOT NULL DEFAULT 0,
    total_slots INTEGER NOT NULL DEFAULT 1,
    generated_at TEXT NOT NULL,
    processing_time_ms REAL,
    total_tokens INTEGER,
    total_cost_usd REAL,
    llm_model TEXT,
    error_message TEXT,
    lesson_json TEXT,
    sync_status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON weekly_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_week_of ON weekly_plans(week_of);

