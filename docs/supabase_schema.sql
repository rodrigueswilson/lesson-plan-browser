-- Supabase PostgreSQL Schema for Bilingual Lesson Plan Builder
-- Converted from SQLite schema with PostgreSQL-specific types and features

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    base_path_override TEXT,
    template_path TEXT,
    signature_image_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Class slots table
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
    display_order INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, slot_number)
);

-- Weekly plans table
CREATE TABLE IF NOT EXISTS weekly_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    week_folder_path TEXT,
    generated_at TIMESTAMP DEFAULT NOW(),
    output_file TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    consolidated INTEGER DEFAULT 0,
    total_slots INTEGER DEFAULT 1,
    processing_time_ms REAL,
    total_tokens INTEGER,
    total_cost_usd REAL,
    llm_model TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    slot_number INTEGER,
    day_number INTEGER,
    operation_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms REAL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    llm_provider TEXT,
    llm_model TEXT,
    cost_usd REAL,
    error_message TEXT,
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_class_slots_user_id ON class_slots(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON weekly_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_plan_id ON performance_metrics(plan_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_started_at ON performance_metrics(started_at);

-- Row Level Security (RLS) Policies (optional, for multi-user isolation)
-- Uncomment and customize if using a single Supabase project for multiple users

-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE class_slots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weekly_plans ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (adjust based on your authentication strategy):
-- CREATE POLICY "Users can only see their own data" ON users
--     FOR ALL USING (auth.uid()::text = id);
-- 
-- CREATE POLICY "Users can only see their own class slots" ON class_slots
--     FOR ALL USING (auth.uid()::text = user_id);
-- 
-- CREATE POLICY "Users can only see their own weekly plans" ON weekly_plans
--     FOR ALL USING (auth.uid()::text = user_id);
-- 
-- CREATE POLICY "Users can only see their own performance metrics" ON performance_metrics
--     FOR ALL USING (
--         EXISTS (
--             SELECT 1 FROM weekly_plans wp
--             WHERE wp.id = performance_metrics.plan_id
--             AND wp.user_id = auth.uid()::text
--         )
--     );

