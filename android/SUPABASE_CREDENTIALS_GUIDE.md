# Supabase Credentials Setup Guide

## Quick Setup

I've created `local.properties` for you. Now you need to fill in your actual Supabase credentials.

## Step 1: Get Your Supabase Credentials

### For Project 1 (Wilson Rodrigues):
1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select the project for Wilson
3. Navigate to **Settings** → **API**
4. Copy:
   - **Project URL** → This goes in `SUPABASE_URL_PROJECT1`
   - **anon public** key → This goes in `SUPABASE_KEY_PROJECT1`

### For Project 2 (Daniela Silva):
1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select the project for Daniela
3. Navigate to **Settings** → **API**
4. Copy:
   - **Project URL** → This goes in `SUPABASE_URL_PROJECT2`
   - **anon public** key → This goes in `SUPABASE_KEY_PROJECT2`

## Step 2: Edit local.properties

Open `android/local.properties` and replace the placeholder values:

```properties
# Project 1 (Wilson Rodrigues)
SUPABASE_URL_PROJECT1=https://your-actual-project1-id.supabase.co
SUPABASE_KEY_PROJECT1=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-key-here

# Project 2 (Daniela Silva)
SUPABASE_URL_PROJECT2=https://your-actual-project2-id.supabase.co
SUPABASE_KEY_PROJECT2=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-key-here
```

**Important Notes:**
- Use the **anon/public** key (NOT the service_role key)
- The URL should end with `.supabase.co`
- Don't add quotes around the values
- Don't add extra spaces

## Step 3: Verify Configuration

After editing `local.properties`, rebuild the project:

```bash
cd android
./gradlew clean build
```

The app will validate the configuration on startup and show errors if anything is missing or incorrect.

## Step 4: Test the App

1. Run the app on a device or emulator
2. Check the logs for configuration validation messages
3. The app will show configuration errors in the UI if credentials are missing

## Troubleshooting

### "Empty Supabase configuration" error
- Make sure `local.properties` exists in the `android/` directory
- Check that all 4 values are filled in (2 URLs and 2 keys)
- Verify there are no extra quotes or spaces
- Rebuild the project after editing

### Connection errors
- Verify URLs are correct (should end with `.supabase.co`)
- Verify you're using the **anon/public** key (not service_role)
- Check network connectivity
- Verify Row Level Security (RLS) policies allow access in Supabase

### Build errors
- Make sure `buildConfig = true` is set in `buildFeatures` (already done)
- Clean and rebuild: `./gradlew clean build`

## Security Reminder

✅ `local.properties` is already in `.gitignore` and won't be committed
✅ Use **anon/public keys** (not service role keys)
✅ Never commit credentials to version control
✅ The app validates configuration on startup

## Need Help?

See `SUPABASE_SETUP.md` for more detailed information.

