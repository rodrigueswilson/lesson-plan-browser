# Original Lesson Plans Table Design

## Overview

Create a database table to store original lesson plan content from primary teachers. This enables:
1. **Parallel LLM processing** (no file locking issues)
2. **Single source of truth** for original content
3. **Combined DOCX generation** from database
4. **Better versioning and tracking**

## Proposed Schema

### Table: `original_lesson_plans`

```sql
CREATE TABLE original_lesson_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    homeroom TEXT,
    
    -- Source file information
    source_file_path TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    primary_teacher_name TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Extracted content (structured)
    content_json JSONB NOT NULL,  -- Full extracted content structure
    full_text TEXT,  -- Plain text version for LLM
    
    -- Per-day content breakdown
    monday_content JSONB,
    tuesday_content JSONB,
    wednesday_content JSONB,
    thursday_content JSONB,
    friday_content JSONB,
    
    -- Metadata
    available_days TEXT[],  -- Array of days with content: ['monday', 'tuesday', ...]
    has_no_school BOOLEAN DEFAULT FALSE,
    content_hash TEXT,  -- Hash of content for change detection
    
    -- Status
    status TEXT DEFAULT 'extracted',  -- 'extracted', 'processed', 'error'
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, week_of, slot_number)
);

CREATE INDEX idx_original_plans_user_week 
ON original_lesson_plans(user_id, week_of);

CREATE INDEX idx_original_plans_status 
ON original_lesson_plans(status);
```

## Content JSON Structure

```json
{
  "full_text": "Complete extracted text from DOCX",
  "table_content": {
    "monday": {
      "Unit/Lesson": "...",
      "Objective": "...",
      "Activities": "...",
      "Assessment": "..."
    },
    "tuesday": { ... },
    ...
  },
  "images": [
    {"path": "...", "description": "..."}
  ],
  "hyperlinks": [
    {"url": "...", "text": "..."}
  ],
  "metadata": {
    "extraction_method": "table_based|heading_based",
    "slot_number": 1,
    "subject": "ELA/SS"
  }
}
```

## New Workflow

### Phase 1: Extract and Store (Sequential - File Operations)
```
For each slot:
  1. Open DOCX file (with retry logic)
  2. Extract content (unit/lesson, objectives, activities, etc.)
  3. Store in original_lesson_plans table
  4. Close file (release lock)
```

### Phase 2: Generate Combined Original DOCX (Optional)
```
1. Query all original_lesson_plans for the week
2. Generate a combined DOCX showing all original content
3. Save to week folder as "Original_Lesson_Plans_{week}.docx"
```

### Phase 3: Parallel LLM Processing
```
1. Query all original_lesson_plans for the week
2. Process all slots in parallel:
   - Slot 1 → LLM API call (async)
   - Slot 2 → LLM API call (async)
   - Slot 3 → LLM API call (async)
   - Slot 4 → LLM API call (async)
3. Wait for all to complete
4. Store results in weekly_plans table
```

## Benefits

1. **No File Locking**: Files are read once, stored in DB
2. **Parallel Processing**: All LLM calls can run simultaneously
3. **Faster**: 4 slots × 2 min = 2 min (parallel) vs 8 min (sequential)
4. **Versioning**: Track changes to original content
5. **Audit Trail**: See what original content was used
6. **Combined View**: Generate DOCX of all originals for review

## Implementation Steps

1. Create migration for `original_lesson_plans` table
2. Modify batch processor to extract and store first
3. Add function to generate combined original DOCX
4. Modify LLM processing to read from database
5. Implement parallel processing with asyncio.gather()
