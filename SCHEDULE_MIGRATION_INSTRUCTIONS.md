# Schedule Table Migration Instructions

## Overview
The `schedules` table needs to be created in each Supabase project that will use schedule functionality.

## Migration Steps

### For Project 1 (Wilson Rodrigues)
1. Open Supabase Dashboard for Project 1
2. Navigate to **SQL Editor**
3. Run the SQL from `sql/create_schedules_table_supabase.sql`
4. Verify the table was created by checking the **Table Editor**

### For Project 2 (Daniela)
1. Open Supabase Dashboard for Project 2
2. Navigate to **SQL Editor**
3. Run the same SQL from `sql/create_schedules_table_supabase.sql`
4. Verify the table was created by checking the **Table Editor**

## SQL Migration File
The complete SQL is located at: `sql/create_schedules_table_supabase.sql`

## Quick Copy-Paste SQL

```sql
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    subject TEXT NOT NULL,
    homeroom TEXT,
    grade TEXT,
    slot_number INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_schedules_user_day ON schedules(user_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_user_time ON schedules(user_id, day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_schedules_current ON schedules(user_id, is_active, day_of_week, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_schedules_homeroom ON schedules(user_id, homeroom, day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_grade ON schedules(user_id, grade, day_of_week);
```

## Verification

After running the migration in both projects, you can verify by:

1. **In Supabase Dashboard:**
   - Go to Table Editor
   - You should see the `schedules` table listed

2. **Via API Test:**
   ```batch
   test-schedule.bat
   ```
   This will test creating schedule entries and should work for whichever project is currently active.

## Notes

- Each project maintains its own `schedules` table
- Users in Project 1 can only see schedules in Project 1
- Users in Project 2 can only see schedules in Project 2
- The `user_id` foreign key ensures data integrity within each project

## Row Level Security (RLS)

If you're using Row Level Security in Supabase, you may want to add RLS policies. Uncomment and adjust the RLS policies in the SQL file if needed.

