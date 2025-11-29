# USB Debugging Blocked by Auto Blocker - Solutions

## Issue
USB debugging is blocked by Auto Blocker (likely a security/antivirus feature).

## Solutions

### Option 1: Temporarily Disable Auto Blocker

1. **Find Auto Blocker Settings**:
   - Check your antivirus/security software settings
   - Look for "USB Protection", "Device Control", or "Auto Blocker" features
   - Temporarily disable it for USB debugging

2. **Common Security Software**:
   - **Windows Defender**: Settings > Virus & threat protection > Manage settings
   - **Norton/McAfee/Kaspersky**: Check device control/USB protection settings
   - **Corporate/School**: May require IT admin to whitelist

3. **Whitelist ADB** (if possible):
   - Add `adb.exe` to exceptions/whitelist
   - Add Android SDK platform-tools folder to exceptions
   - Path: `%LOCALAPPDATA%\Android\Sdk\platform-tools`

### Option 2: Use Manual APK Installation (Recommended)

Since USB debugging is blocked, install the APK manually:

#### Step 1: Locate the APK
The APK is already built and located at:
```
D:\LP\android\app\build\outputs\apk\debug\app-debug.apk
```

#### Step 2: Transfer APK to Device

**Method A: USB File Transfer (if allowed)**
1. Connect device via USB
2. On device, change USB mode to "File Transfer" or "MTP"
3. Copy `app-debug.apk` to device's Downloads folder
4. Disconnect USB

**Method B: Cloud Storage**
1. Upload `app-debug.apk` to Google Drive, Dropbox, or OneDrive
2. On device, download the APK from cloud storage

**Method C: Email**
1. Email the APK to yourself
2. Open email on device and download attachment

**Method D: Wireless Transfer**
1. Use apps like "Send Anywhere", "AirDroid", or "Portal"
2. Transfer APK wirelessly

#### Step 3: Install on Device

1. **Enable Unknown Sources**:
   - Go to **Settings** > **Security** (or **Apps** > **Special Access**)
   - Enable **"Install unknown apps"** or **"Unknown sources"**
   - Select the app you'll use to install (Files, Chrome, etc.)

2. **Install APK**:
   - Open **Files** or **File Manager** on device
   - Navigate to **Downloads** (or wherever you saved the APK)
   - Tap **app-debug.apk**
   - Tap **Install**
   - Tap **Open** when installation completes

### Option 3: Use Android Studio

If you have Android Studio installed:

1. **Open Project in Android Studio**:
   - File > Open > Select `D:\LP\android` folder

2. **Run from Android Studio**:
   - Connect device (even if ADB is blocked, Android Studio might work)
   - Click the green "Run" button
   - Select your device from the list
   - Android Studio will install and launch the app

### Option 4: Wireless ADB (If Device is on Same Network)

If you can enable USB debugging temporarily or use Android Studio once:

1. **Connect via USB first** (one time setup):
   ```powershell
   adb tcpip 5555
   ```

2. **Find device IP**:
   - Settings > About Phone > Status > IP Address
   - Or Settings > Wi-Fi > Tap connected network > View IP

3. **Connect wirelessly**:
   ```powershell
   adb connect <device-ip>:5555
   ```

4. **Now you can install wirelessly**:
   ```powershell
   .\gradlew.bat installDebug
   ```

### Option 5: Request IT Admin Help

If this is a corporate/school device:
- Contact IT administrator
- Request whitelisting of:
  - ADB (Android Debug Bridge)
  - Android SDK platform-tools
  - Your development machine's IP/MAC address

## Recommended Approach

**Use Manual APK Installation (Option 2)** - It's the simplest and doesn't require USB debugging.

## After Installation

Once the app is installed, you can:
1. Launch "Bilingual Lesson Planner" from app drawer
2. Test all features
3. View logs using Android Studio's Logcat (if available)

## Testing Without ADB

You can still test the app fully without ADB:
- All app features work normally
- You just can't use `adb logcat` for debugging
- Use in-app logging or Android Studio's Logcat instead

## Need Help?

If you need to view logs or debug:
- Use Android Studio's Logcat window
- Or check device logs: Settings > Developer Options > Take Bug Report

Good luck! 🚀

