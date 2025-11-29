# Android Setup Guide

This guide will help you set up and test the Android version of the Bilingual Lesson Planner app.

## Prerequisites

1. **Android Studio** - Download from https://developer.android.com/studio
2. **Java JDK** - Usually included with Android Studio
3. **Android device** (phone or tablet) with USB debugging enabled
4. **Backend running** - FastAPI backend must be accessible from your Android device

## Step 1: Configure Backend URL

The Android app needs to connect to your backend API. You have two options:

### Option A: Local Network (Recommended for Testing)

1. **Find your PC's IP address:**
   - Run `find-pc-ip.ps1` (PowerShell) or `find-pc-ip.bat` (Command Prompt)
   - Or manually: Open PowerShell and run `ipconfig | findstr IPv4`
   - Look for an IP like `192.168.1.100` or `10.0.0.5`

2. **Update capacitor.config.ts:**
   ```typescript
   server: {
     url: 'http://YOUR_PC_IP:8000',  // Replace with your IP
     cleartext: true
   }
   ```

3. **Start backend with network access:**
   ```powershell
   cd backend
   python -m uvicorn api:app --host 0.0.0.0 --port 8000
   ```
   The `--host 0.0.0.0` allows connections from other devices.

4. **Test connectivity:**
   - On your Android device, open a browser
   - Visit: `http://YOUR_PC_IP:8000/api/health`
   - You should see: `{"status":"healthy","version":"1.0.0"}`

5. **Windows Firewall:**
   - If connection fails, Windows may ask to allow Python through firewall
   - Click "Allow access" when prompted

### Option B: Cloud Backend

If you've deployed your backend to Railway/Render/Fly.io:

1. Update `capacitor.config.ts`:
   ```typescript
   server: {
     url: 'https://your-backend.railway.app',
     cleartext: false  // HTTPS
   }
   ```

## Step 2: Build the React App

```powershell
cd frontend
npm run build
```

This creates the `dist` folder with the compiled React app.

## Step 3: Sync to Android

```powershell
npx cap sync android
```

This copies your web app to the Android project and updates native dependencies.

## Step 4: Enable USB Debugging on Android Device

1. **Enable Developer Options:**
   - Settings → About Phone
   - Tap "Build Number" 7 times
   - You'll see "You are now a developer!"

2. **Enable USB Debugging:**
   - Settings → Developer Options
   - Enable "USB Debugging"
   - Enable "Install via USB" (if available)

3. **Connect device via USB:**
   - Connect your Android device to your PC
   - On device, tap "Allow USB debugging" when prompted

## Step 5: Verify Device Connection

```powershell
# Check if Android SDK platform-tools is in your PATH
# If not, use full path: C:\Users\YourName\AppData\Local\Android\Sdk\platform-tools\adb.exe
adb devices
```

You should see your device listed. If not:
- Check USB cable
- Try different USB port
- Make sure USB debugging is enabled
- Install device drivers if needed

## Step 6: Build and Install

### Option A: Using Capacitor CLI (Easiest)

```powershell
npx cap run android
```

This will:
1. Open Android Studio
2. Build the app
3. Install it on your connected device

### Option B: Using Android Studio

1. **Open Android Studio:**
   ```powershell
   npx cap open android
   ```

2. **Wait for Gradle sync** (first time may take a few minutes)

3. **Select your device:**
   - In the device dropdown (top toolbar), select your connected device

4. **Run the app:**
   - Click the green "Run" button (▶️) or press `Shift+F10`
   - App will build and install on your device

## Step 7: Testing

Once the app is installed on your device:

1. **Test core functionality:**
   - User selection
   - Slot configuration
   - Plan generation
   - Plan history
   - Analytics

2. **Test mobile features:**
   - Bottom navigation
   - Touch interactions
   - Android back button
   - Responsive layout

3. **Test connectivity:**
   - Make sure backend is accessible
   - Test API calls
   - Verify data sync

## Troubleshooting

### App won't connect to backend

- **Check IP address:** Make sure PC and Android device are on same Wi-Fi network
- **Check backend:** Verify backend is running with `--host 0.0.0.0`
- **Check firewall:** Allow Python through Windows Firewall
- **Test in browser:** Try accessing backend URL from Android device's browser

### Build errors in Android Studio

- **Gradle sync failed:** Check internet connection, Gradle may need to download dependencies
- **SDK not found:** Install Android SDK via Android Studio → SDK Manager
- **Java version:** Make sure Java JDK is installed (Android Studio usually includes it)

### Device not detected

- **USB debugging:** Make sure it's enabled in Developer Options
- **USB drivers:** Install device-specific USB drivers if needed
- **Different cable/port:** Try different USB cable or port
- **ADB restart:** Run `adb kill-server` then `adb start-server`

### App crashes on launch

- **Check logs:** In Android Studio, check Logcat for error messages
- **Permissions:** Make sure app has required permissions in AndroidManifest.xml
- **Backend connection:** Verify backend URL is correct in capacitor.config.ts

## Development Workflow

### Making Changes

1. **Edit React code** in `frontend/src/`
2. **Build:** `npm run build`
3. **Sync:** `npx cap sync android`
4. **Run:** `npx cap run android` or use Android Studio

### Hot Reload (Limited)

Capacitor doesn't support hot reload like web development. You need to rebuild and sync after changes.

For faster iteration:
- Use `npm run dev` in browser for initial development
- Test on device after major changes

## Next Steps

- [ ] Test all features on Android device
- [ ] Optimize for tablet screen sizes
- [ ] Create app icon and splash screen
- [ ] Build release APK for distribution
- [ ] Test on Android tablet when available

## Additional Resources

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [Android Studio Guide](https://developer.android.com/studio/intro)
- [ADB Commands](https://developer.android.com/studio/command-line/adb)

