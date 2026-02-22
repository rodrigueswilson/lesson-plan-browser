# How to Run Supabase Table Creation Scripts

This guide explains how to create the missing `lesson_steps` and `lesson_mode_sessions` tables in your Supabase database.

## Method 1: Using Supabase Dashboard (Recommended)

### Steps:

1. **Open Supabase Dashboard**
   - Go to https://app.supabase.com
   - Sign in and select your project

2. **Open SQL Editor**
   - In the left sidebar, click on "SQL Editor"
   - Click "New query"

3. **Run the first migration** (`lesson_steps` table):
   - Open the file: `sql/create_lesson_steps_table_supabase.sql`
   - Copy all the SQL content
   - Paste it into the SQL Editor
   - Click "Run" (or press Ctrl+Enter)
   - You should see "Success. No rows returned"

4. **Run the second migration** (`lesson_mode_sessions` table):
   - Open the file: `sql/create_lesson_mode_sessions_table_supabase.sql`
   - Copy all the SQL content
   - Paste it into the SQL Editor (you can clear the previous query or create a new one)
   - Click "Run"
   - You should see "Success. No rows returned"

5. **Verify the tables were created**:
   - In the left sidebar, click on "Table Editor"
   - You should now see `lesson_steps` and `lesson_mode_sessions` in the list of tables

## Method 2: Using Supabase CLI (Advanced)

If you have the Supabase CLI installed, you can run:

```bash
# Set your Supabase project reference (if not already set)
supabase link --project-ref your-project-ref

# Run the migrations
supabase db execute -f sql/create_lesson_steps_table_supabase.sql
supabase db execute -f sql/create_lesson_mode_sessions_table_supabase.sql
```

## Method 3: Using psql (PostgreSQL client)

If you have `psql` installed and have your database connection string:

```bash
# Get your connection string from Supabase Dashboard > Settings > Database
# Format: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres

psql "your-connection-string" -f sql/create_lesson_steps_table_supabase.sql
psql "your-connection-string" -f sql/create_lesson_mode_sessions_table_supabase.sql
```

## Notes

- Both SQL files use `CREATE TABLE IF NOT EXISTS`, so it's safe to run them multiple times
- The tables will be created with proper indexes and foreign key constraints
- After creating the tables, restart your backend application to clear the warning flags
- The warnings will stop appearing once the tables exist

## Troubleshooting

If you get errors:
- Make sure you're connected to the correct Supabase project
- Verify that the `weekly_plans` and `users` tables exist (these are referenced as foreign keys)
- Check that you have the necessary permissions (you need to be a project owner or have database admin access)

