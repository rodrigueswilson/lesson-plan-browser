-- Migration: Add lesson_json JSONB column to weekly_plans table
-- This enables storing the full lesson plan JSON in the database for browser viewing

-- Add the lesson_json column
ALTER TABLE weekly_plans 
ADD COLUMN IF NOT EXISTS lesson_json JSONB;

-- Add index for fast JSON queries on metadata
CREATE INDEX IF NOT EXISTS idx_weekly_plans_lesson_json_metadata 
ON weekly_plans 
USING GIN ((lesson_json->'metadata'));

-- Add index for day-level queries
CREATE INDEX IF NOT EXISTS idx_weekly_plans_lesson_json_days 
ON weekly_plans 
USING GIN ((lesson_json->'days'));

-- Optional: Add sync tracking columns (for future P2P sync feature)
-- Uncomment these if you want to enable sync tracking:
-- ALTER TABLE weekly_plans 
-- ADD COLUMN IF NOT EXISTS sync_status TEXT DEFAULT 'pending',
-- ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP,
-- ADD COLUMN IF NOT EXISTS sync_device_id TEXT;

-- Add index for sync operations (if sync columns are added)
-- CREATE INDEX IF NOT EXISTS idx_weekly_plans_sync 
-- ON weekly_plans (user_id, updated_at);

