# Supabase Configuration Guide

This guide explains how to configure Supabase credentials for the Android app.

## Configuration Methods

The app supports multiple ways to configure Supabase credentials, in priority order:

1. **BuildConfig** (from `local.properties` or `app/local.properties`)
2. **local.properties file** (recommended for development)
3. **Environment variables** (for CI/CD)

## Setup Instructions

### Method 1: Using local.properties (Recommended)

1. **Copy the example file:**
   ```bash
   cd android
   cp local.properties.example local.properties
   ```

2. **Edit `local.properties`** and add your Supabase credentials:
   ```properties
   # Project 1 (Wilson Rodrigues)
   SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
   SUPABASE_KEY_PROJECT1=your-project1-anon-key

   # Project 2 (Daniela Silva)
   SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
   SUPABASE_KEY_PROJECT2=your-project2-anon-key
   ```

3. **Or create `app/local.properties`** with the same content (app-level override)

4. **Rebuild the project:**
   ```bash
   ./gradlew clean
   ./gradlew build
   ```

### Method 2: Using BuildConfig (Alternative)

If you prefer to set credentials directly in `build.gradle.kts`:

1. Edit `app/build.gradle.kts`
2. Find the `buildConfigField` entries in `defaultConfig`
3. Replace the empty strings with your actual values:
   ```kotlin
   buildConfigField(
       "String",
       "SUPABASE_URL_PROJECT1",
       "\"https://your-project1-id.supabase.co\""
   )
   ```

**Note:** This method is less secure as credentials will be in source code. Use `local.properties` instead.

## Getting Your Supabase Credentials

### For Project 1 (Wilson):
1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL_PROJECT1`
   - **anon/public key** → `SUPABASE_KEY_PROJECT1`

### For Project 2 (Daniela):
1. Go to your second Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL_PROJECT2`
   - **anon/public key** → `SUPABASE_KEY_PROJECT2`

## Security Notes

- ✅ `local.properties` is gitignored and won't be committed
- ✅ Use **anon/public keys** (not service role keys) for the Android app
- ✅ Never commit credentials to version control
- ✅ Use different keys for development and production if needed

## Verification

After configuration, verify the setup:

1. Build the app:
   ```bash
   ./gradlew build
   ```

2. Check for configuration errors in the build output

3. Run the app and check logs for Supabase connection status

## Troubleshooting

### "Empty Supabase configuration" error
- Ensure `local.properties` exists and contains all 4 values
- Check that values don't have extra quotes or spaces
- Rebuild the project after editing `local.properties`

### Connection errors
- Verify URLs are correct (should end with `.supabase.co`)
- Verify keys are the anon/public keys (not service role)
- Check network connectivity
- Verify Row Level Security (RLS) policies allow access

### Build errors
- Ensure `buildConfig = true` is set in `buildFeatures`
- Clean and rebuild: `./gradlew clean build`

## Example local.properties

```properties
# Supabase Configuration
# Project 1 (Wilson Rodrigues)
SUPABASE_URL_PROJECT1=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY_PROJECT1=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.example

# Project 2 (Daniela Silva)
SUPABASE_URL_PROJECT2=https://qrstuvwxyz123456.supabase.co
SUPABASE_KEY_PROJECT2=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFyc3R1dnd4eXoxMjM0NTYiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.example
```

## User-to-Project Mapping

The app automatically maps users to projects:
- Users with "wilson" in their ID → Project 1
- Users with "daniela" in their ID → Project 2
- Default → Project 1

This mapping can be customized in `SupabaseConfigProvider.getUserProjectMapping()`.

