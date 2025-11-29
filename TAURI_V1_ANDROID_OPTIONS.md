# Tauri v1.5 Android Support - Options

## Issue

Tauri CLI v1.6.3 (npm) doesn't have `android` subcommand. Android support was added in Tauri v2.0.

## Current Situation

- **Project Tauri Version**: v1.5.4
- **Tauri CLI**: v1.6.3 (via npm)
- **Android Support**: Not available in v1.5

## Options

### Option 1: Upgrade to Tauri v2.0 (Recommended for Android)

**Pros:**
- Native Android support
- `tauri android init` command works
- Better Android integration
- Active development

**Cons:**
- May require code changes
- Need to test all functionality
- Breaking changes from v1.5

**Steps:**
1. Update `Cargo.toml`: `tauri = { version = "2.0", ... }`
2. Update `package.json`: `@tauri-apps/cli` to v2.0
3. Update `tauri.conf.json` to v2 format
4. Test desktop functionality
5. Then proceed with Android

### Option 2: Manual Android Project Setup

**Pros:**
- Stay on Tauri v1.5.4
- No code changes needed
- Desktop continues working

**Cons:**
- More complex setup
- Manual configuration
- Less documentation

**Steps:**
1. Create Android project structure manually
2. Configure Gradle files
3. Set up Tauri integration
4. Configure Python runtime bundling
5. Build APK manually

### Option 3: Use Capacitor (Alternative)

The project already has Capacitor dependencies in `package.json`:
- `@capacitor/android`
- `@capacitor/cli`

**Pros:**
- Already in project
- Works with current setup
- Good Android support

**Cons:**
- Different architecture (not Tauri)
- Would need to adapt IPC bridge
- More significant changes

## Recommendation

**Option 1: Upgrade to Tauri v2.0**

Since we're building for Android, upgrading to v2.0 makes sense:
- Native Android support
- Better long-term solution
- Active development
- More documentation

The upgrade should be manageable since:
- We're using standard Tauri features
- IPC bridge is custom (not Tauri-specific)
- Database code is independent

## Next Steps

1. **Decide on approach** (upgrade vs manual)
2. **If upgrading**: Update dependencies and test
3. **If manual**: Create Android project structure
4. **Configure Python runtime bundling**
5. **Build and test**

## Current Status

- ✅ NDK installed (v29.0.14206865)
- ✅ ANDROID_NDK_HOME set
- ✅ Environment ready
- ⏸️ Waiting for Tauri Android support decision

