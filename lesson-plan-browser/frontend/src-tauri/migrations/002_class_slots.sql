CREATE TABLE IF NOT EXISTS class_slots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    homeroom TEXT,
    plan_group_label TEXT,
    proficiency_levels TEXT,
    primary_teacher_file TEXT,
    primary_teacher_name TEXT,
    primary_teacher_first_name TEXT,
    primary_teacher_last_name TEXT,
    primary_teacher_file_pattern TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sync_status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_class_slots_user_id ON class_slots(user_id);

