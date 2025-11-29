# Migration: Add lesson_json Column to Supabase

## Problem
The browser cannot display lesson plans because the `lesson_json` column doesn't exist in the `weekly_plans` table in Supabase. This column is needed to store the full lesson plan JSON data for browser viewing.

## Solution
Run the SQL migration to add the `lesson_json` column.

## Steps

### Option 1: Using Supabase Dashboard (Recommended)

1. Open your Supabase project dashboard
2. Go to **SQL Editor**
3. Copy and paste the contents of `sql/add_lesson_json_column.sql`
4. Click **Run** to execute the migration

### Option 2: Using Supabase CLI

```bash
# If you have Supabase CLI installed
supabase db push sql/add_lesson_json_column.sql
```

### Option 3: Using psql

```bash
# Connect to your Supabase database
psql -h <your-supabase-host> -U postgres -d postgres

# Then run the SQL file
\i sql/add_lesson_json_column.sql
```

## Verification

After running the migration, verify the column was added:

```sql
-- Check if column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'weekly_plans' 
AND column_name = 'lesson_json';
```

You should see:
```
 column_name  | data_type
--------------+-----------
 lesson_json  | jsonb
```

## After Migration

1. **Existing plans**: Plans created before this migration will have `NULL` in `lesson_json`. You'll need to regenerate them or backfill from JSON files if they exist.

2. **New plans**: All newly generated lesson plans will automatically save their `lesson_json` to the database and will be viewable in the browser.

3. **Test**: Generate a new lesson plan and verify it appears in the browser.

## Notes

- The migration uses `IF NOT EXISTS` so it's safe to run multiple times
- The indexes will improve query performance when filtering/searching lesson plans
- The sync columns are optional and commented out (for future P2P sync feature)

