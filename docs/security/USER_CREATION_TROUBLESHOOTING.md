# User Creation Troubleshooting

## Issue

The API returns `[]` because there are no users in the database. When trying to create a user, you get a 500 error.

## Check FastAPI Logs

**The most important step:** Check your FastAPI terminal for the full error message. It will show exactly what's failing.

Look for lines like:
```
ERROR: user_create_failed
Traceback (most recent call last):
...
```

## Common Issues

### 1. Database Connection Issue

If using Supabase, verify:
- `USE_SUPABASE=True` is set (if using Supabase)
- Supabase credentials are correct
- Database is accessible

If using SQLite, verify:
- Database file exists or can be created
- Write permissions on the data directory

### 2. UserResponse Model Mismatch

The `UserResponse` model expects certain fields. Check if the database returns all required fields:
- `id`
- `name` (computed from first_name + last_name)
- `first_name`
- `last_name`
- `email` (optional)
- `created_at`
- `updated_at`

### 3. RLS Blocking Creation

If using Supabase with RLS enabled, verify:
- Service role key is being used (bypasses RLS)
- Or INSERT policy allows user creation

## Quick Test via Swagger UI

1. Open http://127.0.0.1:8000/api/docs
2. Find **POST /api/users**
3. Click **"Try it out"**
4. Enter:
   ```json
   {
     "first_name": "Test",
     "last_name": "User",
     "email": "test@example.com"
   }
   ```
5. Click **"Execute"**
6. Check the **Response** section for detailed error

## Manual Database Check

If you have direct database access, verify the users table exists:

**SQLite:**
```sql
SELECT * FROM users;
```

**Supabase:**
```sql
SELECT * FROM public.users;
```

## Next Steps

1. **Check FastAPI terminal logs** - This will show the exact error
2. **Test via Swagger UI** - Get detailed error response
3. **Verify database connection** - Ensure database is accessible
4. **Check RLS policies** - If using Supabase, ensure INSERT is allowed

Share the error message from FastAPI logs and I can help fix it!

