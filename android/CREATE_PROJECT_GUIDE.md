# Creating Your First Android Project

## Step 1: Install Required API Levels First ⚠️

**Before creating the project**, install the required SDK components:

### In Android Studio Welcome Screen:

1. **Click "More Actions"** (bottom of welcome screen)
2. **Select "SDK Manager"**

   OR

   If you don't see "More Actions":
   - Click **"Customize"** → **"All Settings"** → **"Appearance & Behavior"** → **"System Settings"** → **"Android SDK"**

### In SDK Manager:

#### SDK Platforms Tab:
- ✅ Check **"Android 8.0 (Oreo)"** - API Level 26 (Minimum SDK)
- ✅ Check **"Android 14"** - API Level 34 (Target SDK)
- Optionally check others (28, 29, 30, 31, 33) for testing
- Click **"Apply"** → **"OK"**
- Wait for installation (5-10 minutes)

#### SDK Tools Tab:
- ✅ Check **"Android SDK Command-line Tools (latest)"**
- ✅ Verify these are checked:
  - Android SDK Build-Tools
  - Android SDK Platform-Tools
  - Android Emulator
- Click **"Apply"** → **"OK"**

---

## Step 2: Create New Project

After API levels are installed:

### From Welcome Screen:

1. **Click "New Project"** (or "Create New Project")

2. **Select Template**:
   - Choose **"Empty Activity"**
   - Click **"Next"**

3. **Configure Your Project**:
   
   **Name**: `Bilingual Lesson Planner`
   - Or: `LessonPlanner` (no spaces recommended)
   
   **Package name**: `com.bilingual.lessonplanner` ✅
   - This is already filled in, verify it's correct
   
   **Save location**: 
   - Default: `C:\Users\rodri\AndroidStudioProjects\BilingualLessonPlanner`
   - Or choose: `D:\LP\android\app` (to keep it with your project)
   
   **Language**: **Kotlin** ✅
   - Should be selected by default
   
   **Minimum SDK**: **API 26: Android 8.0 (Oreo)** ✅
   - Select from dropdown
   - This is your minimum SDK requirement
   
   **Build configuration language**: **Kotlin DSL** ✅
   - Select "Kotlin DSL" (not Groovy)
   
   Click **"Finish"**

4. **Wait for Gradle Sync**:
   - Android Studio will download Gradle
   - Sync project dependencies
   - This takes 5-10 minutes on first run
   - You'll see progress in bottom status bar

---

## Step 3: Verify Project Setup

After project is created:

1. **Check Project Structure**:
   - Left panel: `app/src/main/java/com/bilingual/lessonplanner/`
   - Should see `MainActivity.kt`

2. **Check Build Files**:
   - `build.gradle.kts` (project level)
   - `app/build.gradle.kts` (app level)
   - Both should exist

3. **Verify Settings**:
   - Open `app/build.gradle.kts`
   - Check `minSdk = 26`
   - Check `targetSdk = 34` (or latest available)
   - Check `namespace = "com.bilingual.lessonplanner"`

4. **Try Building**:
   - Click **Build** → **Make Project** (or `Ctrl+F9`)
   - Should build successfully without errors

---

## Recommended Project Location

**Option 1: Default Location** (Recommended for first project)
- `C:\Users\rodri\AndroidStudioProjects\BilingualLessonPlanner`
- Pros: Standard Android Studio location, easy to find
- Cons: Separate from your main project

**Option 2: With Your Project** (Better for organization)
- `D:\LP\android\app`
- Pros: Keeps everything together
- Cons: Need to create `android\app` folder first

**My Recommendation**: Use Option 1 for now, you can move it later if needed.

---

## What Happens After Project Creation

1. **Gradle Sync** (5-10 minutes)
   - Downloads Gradle wrapper
   - Downloads dependencies
   - Syncs project

2. **Indexing** (2-5 minutes)
   - Android Studio indexes files
   - Enables code completion

3. **Ready to Code** ✅
   - Project structure is ready
   - Can start adding dependencies
   - Can start implementing features

---

## Next Steps After Project Creation

1. ✅ **Add Dependencies** (in `app/build.gradle.kts`):
   - Room database
   - Jetpack Compose
   - Hilt (DI)
   - Supabase Android SDK
   - WorkManager
   - See `ARCHITECTURE.md` for complete list

2. ✅ **Set Up Project Structure**:
   - Create folders: `data/`, `domain/`, `ui/`, `di/`
   - See `ARCHITECTURE.md` for structure

3. ✅ **Configure Supabase**:
   - Add Supabase URLs and keys
   - Set up connection

4. ✅ **Start Implementation**:
   - Begin with data layer
   - Then repository layer
   - Then ViewModels
   - Finally UI (Compose)

---

## Troubleshooting

### "SDK not found" Error
- **Problem**: Android Studio can't find SDK
- **Solution**: Go to **File** → **Settings** → **Android SDK** and set SDK location to `C:\Users\rodri\AppData\Local\Android\Sdk`

### "API 26 not found" Error
- **Problem**: Minimum SDK not installed
- **Solution**: Install API 26 via SDK Manager (Step 1 above)

### Gradle Sync Fails
- **Problem**: Gradle can't sync dependencies
- **Solution**: 
  1. Check internet connection
  2. Try **File** → **Invalidate Caches** → **Invalidate and Restart**
  3. Check firewall isn't blocking

### Project Creation Hangs
- **Problem**: Stuck on "Creating project"
- **Solution**: 
  1. Wait 5-10 minutes (first time is slow)
  2. Check internet connection
  3. Try again if it fails

---

## Quick Checklist

**Before Creating Project**:
- [ ] Install API 26 via SDK Manager
- [ ] Install API 34 via SDK Manager
- [ ] Install Command-line Tools via SDK Manager

**Creating Project**:
- [ ] Click "New Project"
- [ ] Select "Empty Activity"
- [ ] Set package: `com.bilingual.lessonplanner`
- [ ] Set min SDK: API 26
- [ ] Set language: Kotlin
- [ ] Set build config: Kotlin DSL
- [ ] Click "Finish"
- [ ] Wait for Gradle sync

**After Project Created**:
- [ ] Verify project structure
- [ ] Verify build.gradle.kts settings
- [ ] Try building project
- [ ] Ready to add dependencies!

---

## Summary

**Recommended Order**:
1. ⚠️ **First**: Install API 26 and 34 via SDK Manager
2. ✅ **Then**: Create new project with correct settings
3. ✅ **Finally**: Wait for Gradle sync and start coding

This ensures your project is created with all required components from the start!

