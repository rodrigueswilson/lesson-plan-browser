# Quick Supabase Configuration

## Fastest Setup Method

### Step 1: Create Configuration File

**Windows (PowerShell):**
```powershell
cd android
.\setup-supabase.ps1
```

**Linux/Mac:**
```bash
cd android
chmod +x setup-supabase.sh
./setup-supabase.sh
```

**Manual:**
```bash
cd android
cp local.properties.example local.properties
# Then edit local.properties with your credentials
```

### Step 2: Add Your Credentials

Edit `android/local.properties`:

```properties
SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
SUPABASE_KEY_PROJECT1=your-project1-anon-key
SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
SUPABASE_KEY_PROJECT2=your-project2-anon-key
```

### Step 3: Rebuild

```bash
./gradlew clean build
```

## Where to Find Your Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → Use for `SUPABASE_URL_PROJECT1` or `SUPABASE_URL_PROJECT2`
   - **anon public key** → Use for `SUPABASE_KEY_PROJECT1` or `SUPABASE_KEY_PROJECT2`

## Verification

After configuration, the app will:
- ✅ Load credentials from `local.properties`
- ✅ Generate BuildConfig fields automatically
- ✅ Connect to Supabase on app startup
- ✅ Show connection errors if credentials are invalid

## Troubleshooting

**"Credentials not configured" error:**
- Ensure `local.properties` exists in `android/` directory
- Check all 4 values are filled in
- Rebuild after editing: `./gradlew clean build`

**Connection errors:**
- Verify URLs end with `.supabase.co`
- Use anon/public keys (not service role keys)
- Check network connectivity

See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for detailed help.

