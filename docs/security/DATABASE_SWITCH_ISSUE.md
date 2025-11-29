# Database Switch Issue - Users Not Showing

## Problem

You had users before, but now the API returns `[]` (empty array).

## Root Cause

**The app switched from SQLite to Supabase!**

- **Current config:** `USE_SUPABASE: True` (using Supabase)
- **Previous data:** Likely stored in SQLite database
- **Result:** Users are in SQLite, but app is querying Supabase (which is empty)

## Solution Options

### Option 1: Switch Back to SQLite (to see existing users)

**Temporarily disable Supabase:**

1. Set environment variable:
   ```powershell
   $env:USE_SUPABASE = "False"
   ```

2. Or edit `.env` file:
   ```
   USE_SUPABASE=False
   ```

3. Restart FastAPI

**Then check:**
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/users
```

### Option 2: Migrate Users to Supabase

If you want to use Supabase, you need to migrate the users:

1. **Export from SQLite:**
   ```python
   # Run in Python
   import sqlite3
   conn = sqlite3.connect('./data/lesson_planner.db')
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM users')
   users = cursor.fetchall()
   # Export users data
   ```

2. **Import to Supabase:**
   - Use Supabase dashboard SQL editor
   - Or use the API to create users

### Option 3: Check Supabase Directly

Verify if users exist in Supabase:

1. Open Supabase dashboard
2. Go to Table Editor → `users` table
3. Check if users exist there

## Quick Check: Which Database Has Users?

**Check SQLite:**
```powershell
cd D:\LP
python -c "import sqlite3; conn = sqlite3.connect('./data/lesson_planner.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM users'); print('SQLite users:', cursor.fetchone()[0])"
```

**Check Supabase:**
- Use Supabase dashboard
- Or check via API (but RLS might block if not authenticated)

## Recommendation

**If you want to keep using Supabase:**
1. Migrate users from SQLite to Supabase
2. Ensure RLS policies allow SELECT (they should - we set them up)

**If you want to use SQLite:**
1. Set `USE_SUPABASE=False`
2. Restart FastAPI
3. Your existing users should appear

## Next Steps

1. Check which database has your users (SQLite vs Supabase)
2. Decide which database to use going forward
3. Migrate data if needed
4. Update configuration accordingly

