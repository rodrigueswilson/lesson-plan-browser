# Android SDK Setup Guide

## Understanding Android Studio and SDK

**Android Studio** = IDE (Integrated Development Environment)
- The application you installed
- Includes code editor, debugger, emulator manager, etc.

**Android SDK** = Software Development Kit
- The actual tools and libraries needed to build Android apps
- Included with Android Studio, but must be installed separately
- Contains: platform tools, build tools, API levels, emulator images

## Installation Status

✅ **Android Studio** - Installed
⏳ **Android SDK** - Needs to be installed via Android Studio

---

## Step-by-Step: Install Android SDK

### Method 1: First Launch Setup (Recommended)

1. **Open Android Studio**
   - Launch Android Studio from Start Menu

2. **Welcome Screen**
   - If you see "Welcome to Android Studio", click **"More Actions"** → **"SDK Manager"**
   - OR if you see setup wizard, it will guide you through SDK installation

3. **SDK Manager**
   - Go to: **Tools** → **SDK Manager** (or click SDK Manager icon in toolbar)

4. **SDK Platforms Tab**
   - Check these API levels:
     - ✅ **Android 8.0 (Oreo)** - API Level 26 (Required - Minimum SDK)
     - ✅ **Android 9.0 (Pie)** - API Level 28
     - ✅ **Android 10** - API Level 29
     - ✅ **Android 11** - API Level 30
     - ✅ **Android 12** - API Level 31
     - ✅ **Android 13** - API Level 33
     - ✅ **Android 14** - API Level 34 (Required - Target SDK)
   
   - **Note**: You can install just API 26 and 34 for now, but having more gives you better testing options

5. **SDK Tools Tab**
   - Make sure these are checked:
     - ✅ Android SDK Build-Tools
     - ✅ Android SDK Command-line Tools
     - ✅ Android SDK Platform-Tools
     - ✅ Android Emulator
     - ✅ Intel x86 Emulator Accelerator (HAXM installer) - if on Windows/Intel

6. **Click "Apply" or "OK"**
   - Android Studio will download and install everything
   - This may take 10-30 minutes depending on your internet speed

---

## Verify Installation

### Check SDK Location

The SDK is typically installed at:
- **Windows**: `C:\Users\YourName\AppData\Local\Android\Sdk`
- **macOS**: `~/Library/Android/sdk`
- **Linux**: `~/Android/Sdk`

### Verify via Command Line

After installation, verify it works:

```powershell
# Check if ADB is available
adb version

# Check installed platforms
adb devices
```

If these commands don't work, you need to add SDK to PATH (see below).

---

## Set Environment Variables

### Windows

1. **Find SDK Path**
   - Open Android Studio
   - Go to: **File** → **Settings** → **Appearance & Behavior** → **System Settings** → **Android SDK**
   - Copy the "Android SDK Location" path (usually `C:\Users\YourName\AppData\Local\Android\Sdk`)

2. **Set ANDROID_HOME**
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click **"Advanced"** tab → **"Environment Variables"**
   - Under **"User variables"**, click **"New"**
   - Variable name: `ANDROID_HOME`
   - Variable value: `C:\Users\YourName\AppData\Local\Android\Sdk` (your actual path)
   - Click **"OK"**

3. **Add to PATH**
   - In Environment Variables, find **"Path"** in User variables
   - Click **"Edit"**
   - Click **"New"** and add: `%ANDROID_HOME%\platform-tools`
   - Click **"New"** and add: `%ANDROID_HOME%\cmdline-tools\latest\bin`
   - Click **"OK"** on all dialogs

4. **Restart Terminal/VS Code**
   - Close and reopen your terminal/VS Code for changes to take effect

### Verify Environment Variables

Open a **new** PowerShell window and run:

```powershell
# Check ANDROID_HOME
echo $env:ANDROID_HOME

# Check ADB
adb version

# Check installed platforms
adb devices
```

---

## Quick Setup Checklist

- [ ] Open Android Studio
- [ ] Go to SDK Manager (Tools → SDK Manager)
- [ ] Install API 26 (Android 8.0) - Minimum SDK
- [ ] Install API 34 (Android 14) - Target SDK
- [ ] Install SDK Tools (Build Tools, Platform Tools, Emulator)
- [ ] Set ANDROID_HOME environment variable
- [ ] Add platform-tools to PATH
- [ ] Verify: `adb version` works in terminal
- [ ] Restart VS Code/Cursor

---

## Alternative: Command Line Installation

If you prefer command line, you can use `sdkmanager`:

```powershell
# Navigate to SDK location
cd $env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin

# Install specific API levels
.\sdkmanager "platforms;android-26" "platforms;android-34"
.\sdkmanager "build-tools;34.0.0"
.\sdkmanager "platform-tools"
.\sdkmanager "emulator"
```

---

## Troubleshooting

### SDK Not Found
- **Problem**: Android Studio can't find SDK
- **Solution**: In Android Studio, go to **File** → **Settings** → **Android SDK** and set the SDK location

### ADB Not Recognized
- **Problem**: `adb` command not found in terminal
- **Solution**: 
  1. Verify ANDROID_HOME is set correctly
  2. Verify platform-tools is in PATH
  3. Restart terminal/VS Code

### Installation Fails
- **Problem**: SDK installation fails or hangs
- **Solution**:
  1. Check internet connection
  2. Try installing one API level at a time
  3. Check firewall/antivirus isn't blocking
  4. Try using Android Studio's built-in installer instead

---

## Next Steps

Once SDK is installed and verified:

1. ✅ Create Android project in Android Studio
2. ✅ Configure project settings (package name, min SDK, etc.)
3. ✅ Set up project structure
4. ✅ Start coding in VS Code/Cursor

---

## Summary

- **Android Studio** = The IDE (already installed ✅)
- **Android SDK** = The development kit (needs installation via Android Studio)
- **Installation**: Use Android Studio's SDK Manager to install API levels 26-34
- **Configuration**: Set ANDROID_HOME and add platform-tools to PATH
- **Verification**: Run `adb version` to confirm it works

