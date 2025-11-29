CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    subject TEXT,
    grade TEXT,
    homeroom TEXT,
    plan_slot_group_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_plan_slot_group_id ON schedules(plan_slot_group_id);

