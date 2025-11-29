# How to Find SDK Manager in Android Studio

## ❌ NOT in Plugins

**SDK Manager is NOT a plugin** - it's a built-in tool in Android Studio. Don't search in Plugins!

---

## ✅ Correct Ways to Access SDK Manager

### Method 1: From Welcome Screen (Easiest)

1. **On the Welcome Screen**, look at the bottom
2. **Click "More Actions"** (or "Configure" in some versions)
3. **Select "SDK Manager"**
   - This opens the SDK Manager window

---

### Method 2: From Settings (If Project is Open)

1. **File** → **Settings** (or press `Ctrl+Alt+S`)
2. **Appearance & Behavior** → **System Settings** → **Android SDK**
   - This opens the SDK Manager

---

### Method 3: From Tools Menu (If Project is Open)

1. **Tools** → **SDK Manager**
   - Direct access to SDK Manager

---

### Method 4: From Toolbar (If Visible)

1. Look for **SDK Manager icon** in the toolbar
   - Usually looks like a briefcase or tools icon
   - Click it to open SDK Manager

---

## What SDK Manager Looks Like

When you open SDK Manager, you'll see:

### SDK Platforms Tab
- List of Android versions (API levels)
- Checkboxes to install/uninstall
- Shows: Android version, API level, status (installed/not installed)

### SDK Tools Tab
- List of development tools
- Checkboxes for: Build Tools, Platform Tools, Emulator, etc.

### SDK Update Sites Tab
- Update sources (usually don't need to change)

---

## What You Need to Install

### In SDK Platforms Tab:
- ✅ **Android 8.0 (Oreo)** - API Level 26
- ✅ **Android 14** - API Level 34

### In SDK Tools Tab:
- ✅ **Android SDK Command-line Tools (latest)**
- ✅ **Android SDK Build-Tools** (should already be checked)
- ✅ **Android SDK Platform-Tools** (should already be checked)
- ✅ **Android Emulator** (should already be checked)

---

## If You Can't Find "More Actions"

Some Android Studio versions have different layouts:

### Alternative on Welcome Screen:
1. Look for **"Configure"** button
2. Click it → **"SDK Manager"**

### Or:
1. Click **"Open"** or **"New Project"** to open/create a project
2. Then use **File** → **Settings** → **Android SDK**

---

## Visual Guide

**Welcome Screen Layout**:
```
┌─────────────────────────────────────┐
│   Welcome to Android Studio         │
│                                     │
│   [New Project]  [Open]             │
│                                     │
│   [More Actions ▼]  [Get Help]     │ ← Click here
│                                     │
└─────────────────────────────────────┘
```

**After Clicking "More Actions"**:
```
┌─────────────────────────────────────┐
│   More Actions                      │
│                                     │
│   • SDK Manager        ← Click this │
│   • Project Structure              │
│   • Settings                        │
│   • Plugins                         │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### "More Actions" Not Visible
- **Solution**: Click "Open" to open any project, then use **File** → **Settings** → **Android SDK**

### Can't Find SDK Manager
- **Solution**: Use **File** → **Settings** → **Appearance & Behavior** → **System Settings** → **Android SDK**

### SDK Manager Opens But Empty
- **Solution**: Check internet connection, Android Studio needs to download component list

---

## Summary

**DO NOT** search in Plugins - SDK Manager is a built-in tool!

**DO**:
- Click "More Actions" on Welcome Screen → "SDK Manager"
- OR File → Settings → Android SDK
- OR Tools → SDK Manager (if project is open)

Once you find it, you'll see the SDK Platforms and SDK Tools tabs where you can install API 26 and 34.

