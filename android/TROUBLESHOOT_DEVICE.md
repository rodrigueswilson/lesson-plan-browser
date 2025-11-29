# Troubleshooting Device Connection

## Device Not Detected?

If `adb devices` shows no devices, try these steps:

### Step 1: Enable USB Debugging on Device

1. **Enable Developer Options**:
   - Go to **Settings** > **About Phone/Tablet**
   - Find **Build Number** (or **Software Information** > **Build Number**)
   - Tap it **7 times** until you see "You are now a developer!"

2. **Enable USB Debugging**:
   - Go back to **Settings**
   - Find **Developer Options** (usually under System or Advanced)
   - Enable **USB Debugging**
   - Enable **Install via USB** (if available)
   - Enable **USB Debugging (Security settings)** (if available)

### Step 2: Authorize Computer

When you connect the device:
1. A popup should appear on your device: **"Allow USB debugging?"**
2. Check **"Always allow from this computer"**
3. Tap **"Allow"** or **"OK"**

### Step 3: Check USB Connection Mode

On your device:
1. Pull down the notification shade
2. Look for USB connection notification
3. Tap it and select **"File Transfer"** or **"MTP"** mode
4. Some devices need **"PTP"** mode instead

### Step 4: Restart ADB

Run these commands:

```powershell
cd android
$env:PATH = "$env:LOCALAPPDATA\Android\Sdk\platform-tools;$env:PATH"
adb kill-server
adb start-server
adb devices
```

### Step 5: Try Different USB Port/Cable

- Try a different USB port on your computer
- Try a different USB cable (some cables are charge-only)
- Use a USB 2.0 port if available (not USB 3.0)

### Step 6: Install USB Drivers (Windows)

If on Windows and device still not detected:

1. **For Samsung**: Install Samsung USB drivers
2. **For Google Pixel**: Install Google USB drivers
3. **For other brands**: Check manufacturer's website for USB drivers
4. **Generic**: Try installing "Universal ADB Driver"

### Step 7: Check Device Manager (Windows)

1. Open **Device Manager** (Win + X > Device Manager)
2. Look for your device under:
   - **Android Phone** or
   - **Portable Devices** or
   - **Other devices** (with yellow warning)
3. If you see a yellow warning:
   - Right-click > **Update driver**
   - Choose **"Browse my computer"**
   - Select **"Let me pick from a list"**
   - Choose **"Android Device"** or **"Android Composite ADB Interface"**

### Step 8: Verify Device is Detected

After completing the steps above, run:

```powershell
cd android
$env:PATH = "$env:LOCALAPPDATA\Android\Sdk\platform-tools;$env:PATH"
adb devices
```

**Expected Output** (if working):
```
List of devices attached
ABC123XYZ    device
```

The word **"device"** means it's authorized and ready.

If you see **"unauthorized"**, you need to authorize on the device (Step 2).

### Step 9: Install the App

Once device shows as **"device"**, run:

```powershell
cd android
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:PATH = "$env:LOCALAPPDATA\Android\Sdk\platform-tools;$env:PATH"
.\gradlew.bat installDebug
```

## Alternative: Manual APK Installation

If ADB still doesn't work, you can install manually:

1. **Locate the APK**:
   ```
   android/app/build/outputs/apk/debug/app-debug.apk
   ```

2. **Copy to Device**:
   - Connect device via USB
   - Copy APK file to device's Downloads folder
   - Or use cloud storage (Google Drive, etc.)

3. **Install on Device**:
   - On device, open **Files** or **File Manager**
   - Navigate to **Downloads**
   - Tap the **app-debug.apk** file
   - If prompted, enable **"Install from Unknown Sources"**
   - Tap **Install**
   - Tap **Open** when done

## Still Having Issues?

- Check device manufacturer's website for specific USB driver instructions
- Try using Android Studio's Device Manager to see if it detects the device
- Check if your device model requires special drivers
- Verify your device supports USB debugging (most Android 4.0+ devices do)

## Quick Checklist

- [ ] Developer Options enabled
- [ ] USB Debugging enabled
- [ ] Device authorized computer (popup accepted)
- [ ] USB connection mode set to File Transfer/MTP
- [ ] ADB server restarted
- [ ] Device shows as "device" in `adb devices`
- [ ] USB drivers installed (if needed)

Good luck! 🚀

