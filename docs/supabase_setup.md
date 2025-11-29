# Supabase Setup Guide

This guide explains how to set up Supabase for the Bilingual Lesson Plan Builder application.

## Overview

Supabase provides a PostgreSQL database with REST API access, enabling:
- Cross-platform data sync
- Cloud database access
- Android app connectivity
- Free hosting for 2 users (on free tier)

## Prerequisites

1. A Supabase account (sign up at https://supabase.com)
2. Python environment with dependencies installed (`pip install -r requirements.txt`)

## Setup Steps

### 1. Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in project details:
   - **Name**: Your project name (e.g., "Lesson Planner User 1")
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest region
   - **Pricing Plan**: Free tier is sufficient for 2 users
4. Wait for project to be created (2-3 minutes)

### 2. Get Project Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (for client-side access)
   - **service_role key** (for server-side admin operations, optional)

### 3. Create Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Open the file `docs/supabase_schema.sql`
3. Copy and paste the SQL into the SQL Editor
4. Click "Run" to execute
5. Verify tables were created in **Table Editor**

### 4. Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# Enable Supabase
USE_SUPABASE=True

# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key-here

# Optional: Service role key for admin operations
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### 5. Migrate Existing Data (Optional)

If you have existing SQLite data to migrate:

```bash
python tools/migrate_to_supabase.py [--sqlite-path PATH] [--dry-run]
```

- Use `--dry-run` to preview what will be migrated
- Remove `--dry-run` to perform actual migration
- The script will validate data integrity after migration

## Configuration Options

### Single Project vs. Multiple Projects

**Option 1: One Project Per User** (Recommended for isolation)
- Create separate Supabase projects for each user
- Each user has their own database
- No need for Row Level Security (RLS)
- Update `SUPABASE_URL` and `SUPABASE_KEY` per user

**Option 2: Single Project with RLS** (For shared infrastructure)
- Create one Supabase project
- Enable Row Level Security (RLS) policies
- Uncomment RLS policies in `docs/supabase_schema.sql`
- Configure authentication (see Supabase Auth docs)

### Environment-Specific Configuration

For different environments (dev, staging, production):

```env
# Development
USE_SUPABASE=False  # Use SQLite locally

# Production
USE_SUPABASE=True
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-anon-key
```

## Verification

Test the connection:

```python
from backend.database import get_db

db = get_db()
users = db.list_users()
print(f"Found {len(users)} users")
```

## Troubleshooting

### Connection Errors

- **Error**: "SUPABASE_URL and SUPABASE_KEY must be set"
  - **Solution**: Check that environment variables are set correctly

- **Error**: "Table does not exist"
  - **Solution**: Run the schema SQL in Supabase SQL Editor

### Data Migration Issues

- **Error**: Foreign key constraint violations
  - **Solution**: Ensure users are imported before class_slots and weekly_plans

- **Error**: Duplicate key violations
  - **Solution**: Clear Supabase tables and re-run migration

### Performance Issues

- **Issue**: Slow queries
  - **Solution**: Check that indexes were created (see schema SQL)
  - Consider using Supabase connection pooling

## Security Best Practices

1. **Never commit API keys** to version control
2. Use **environment variables** for all sensitive data
3. Use **anon key** for client-side operations (respects RLS)
4. Use **service_role key** only for server-side admin operations
5. Enable **Row Level Security** if using single project for multiple users

## Backup and Recovery

Supabase provides automatic backups on paid plans. For free tier:
- Export data regularly using migration script
- Keep SQLite backups as fallback
- Use Supabase dashboard to export data manually

## Cost Considerations

- **Free Tier**: 500MB database, 2GB bandwidth/month
- **Pro Tier**: $25/month for larger databases and more bandwidth
- Monitor usage in Supabase dashboard under **Settings** → **Usage**

## Next Steps

1. Test API endpoints with Supabase backend
2. Configure Android app to use Supabase REST API
3. Set up automated backups
4. Monitor performance and costs

## Support

- Supabase Documentation: https://supabase.com/docs
- Supabase Discord: https://discord.supabase.com
- Project Issues: Check project repository

