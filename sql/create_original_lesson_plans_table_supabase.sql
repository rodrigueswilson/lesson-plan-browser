-- Create original_lesson_plans table in Supabase
-- Run manually inside Supabase SQL editor

CREATE TABLE IF NOT EXISTS original_lesson_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_of TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    homeroom TEXT,
    
    -- Source file information
    source_file_path TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    primary_teacher_name TEXT,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Extracted content (structured)
    content_json JSONB NOT NULL,  -- Full extracted content structure
    full_text TEXT,  -- Plain text version for LLM
    
    -- Per-day content breakdown (optional, for easier querying)
    monday_content JSONB,
    tuesday_content JSONB,
    wednesday_content JSONB,
    thursday_content JSONB,
    friday_content JSONB,
    
    -- Metadata
    available_days TEXT[],  -- Array of days with content: ['monday', 'tuesday', ...]
    has_no_school BOOLEAN DEFAULT FALSE,
    content_hash TEXT,  -- Hash for change detection
    
    -- Status
    status TEXT DEFAULT 'extracted',  -- 'extracted', 'processed', 'error'
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, week_of, slot_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_original_plans_user_week 
ON original_lesson_plans(user_id, week_of);

CREATE INDEX IF NOT EXISTS idx_original_plans_status 
ON original_lesson_plans(status);

CREATE INDEX IF NOT EXISTS idx_original_plans_slot 
ON original_lesson_plans(user_id, week_of, slot_number);

-- Add comment
COMMENT ON TABLE original_lesson_plans IS 'Stores extracted content from primary teacher files before LLM transformation. Enables parallel processing and combined DOCX generation.';
