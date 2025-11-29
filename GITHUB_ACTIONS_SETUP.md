# GitHub Actions Setup Guide

## Prerequisites
- GitHub account
- Git repository initialized (✅ Done)

## Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click "New repository"
3. Repository name: `bilingual-lesson-planner`
4. Description: `Bilingual Lesson Planner with Tauri Android app`
5. Make it **Public** (free Actions minutes)
6. **DO NOT** initialize with README (we already have files)
7. Click "Create repository"

## Step 2: Connect Local Repository

```bash
# Add remote repository (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/bilingual-lesson-planner.git

# Push to GitHub
git push -u origin main
```

## Step 3: Run Android Build

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Find "Android Build" workflow
4. Click **Run workflow**
5. Select branch: `main`
6. Click **Run workflow**

## Step 4: Download APK

1. Wait for build to complete (~5-10 minutes)
2. Go to Actions → Android Build → Latest run
3. Download **app-arm64-debug-apk** artifact
4. Extract the APK file
5. Install on device: `adb install app-arm64-debug.apk`

## Workflow Features

The GitHub Actions workflow includes:
- ✅ Clean Ubuntu environment (no caching issues)
- ✅ Automatic Node.js, Rust, Python setup
- ✅ Android SDK and NDK installation
- ✅ Frontend build with latest `index-TiTynWQK.js`
- ✅ APK generation and artifact upload
- ✅ Build triggered manually or on code changes

## Expected Results

After successful build:
- APK size: ~25MB
- Contains: `index-TiTynWQK.js` (new file)
- Version: 1.0.1
- Package: `com.lessonplanner.bilingual`

## Troubleshooting

### Build fails with "npm not found"
- Node.js setup failed - check Actions logs

### Build fails with "cargo not found"  
- Rust setup failed - check Actions logs

### Build fails with Android SDK errors
- Android setup failed - check Actions logs

### APK doesn't install
- Check if APK is corrupted
- Try enabling "Unknown sources" on device

## Next Steps

1. **Test the APK** - Should load new JavaScript file
2. **Verify cache fix** - No more old `index-cOgOR3pL.js`
3. **Automate builds** - Can trigger on every push if needed

## Cost

- **Public repository**: Free (2000 minutes/month)
- **Private repository**: $0.008/minute (~$0.50 per build)
- **Current usage**: One build = ~10 minutes

---

**Ready to start!** Create the GitHub repository and run the workflow.
