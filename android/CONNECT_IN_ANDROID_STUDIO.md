# Connect Device in Android Studio

## Step-by-Step Guide

### Step 1: Open the Project in Android Studio

1. **Launch Android Studio**
2. **Open Project**:
   - Click **File** > **Open**
   - Navigate to: `D:\LP\android`
   - Click **OK**
   - Wait for Gradle sync to complete

### Step 2: Connect Your Device

1. **Connect Device via USB**:
   - Plug your Android device into your computer with USB cable
   - On your device, when prompted, select **"File Transfer"** or **"MTP"** mode

2. **Enable USB Debugging** (if not already):
   - On device: **Settings** > **Developer Options** > Enable **USB Debugging**
   - If Developer Options not visible: **Settings** > **About Phone** > Tap **Build Number** 7 times

3. **Authorize Computer** (if prompted):
   - A popup will appear on device: **"Allow USB debugging?"**
   - Check **"Always allow from this computer"**
   - Tap **"Allow"**

### Step 3: Verify Device in Android Studio

1. **Check Device Manager**:
   - Look at the top toolbar in Android Studio
   - You should see a device dropdown (next to the Run button)
   - Or go to **Tools** > **Device Manager**

2. **Device Should Appear**:
   - Your device should show in the list
   - Status should be **"Online"** (green dot)
   - If it shows **"Offline"**, try disconnecting and reconnecting

### Step 4: Run the App

1. **Select Your Device**:
   - Click the device dropdown in the toolbar
   - Select your connected device

2. **Run the App**:
   - Click the green **▶️ Run** button (or press `Shift + F10`)
   - Or go to **Run** > **Run 'app'**

3. **Android Studio Will**:
   - Build the app (if needed)
   - Install the APK on your device
   - Launch the app automatically

### Step 5: View Logs (Optional)

1. **Open Logcat**:
   - Bottom panel in Android Studio
   - Click **Logcat** tab
   - If not visible: **View** > **Tool Windows** > **Logcat**

2. **Filter Logs**:
   - In Logcat search box, type: `BilingualLessonPlanner`
   - Or select your app from the dropdown

## Troubleshooting

### Device Not Showing in Android Studio

**Solution 1: Restart ADB**
- In Android Studio: **Tools** > **SDK Manager**
- Or use terminal: `adb kill-server` then `adb start-server`

**Solution 2: Check USB Connection**
- Try different USB port
- Try different USB cable
- Make sure USB mode is "File Transfer" or "MTP"

**Solution 3: Install USB Drivers**
- Android Studio may prompt to install drivers
- Or download from device manufacturer's website

**Solution 4: Enable Developer Options**
- Make sure Developer Options is enabled on device
- Make sure USB Debugging is enabled

### Device Shows as "Offline"

1. **Disconnect and Reconnect**:
   - Unplug USB cable
   - Wait 5 seconds
   - Plug back in

2. **Revoke USB Debugging Authorization**:
   - On device: **Settings** > **Developer Options**
   - Tap **"Revoke USB debugging authorizations"**
   - Reconnect and authorize again

3. **Restart ADB**:
   - In Android Studio terminal: `adb kill-server`
   - Then: `adb start-server`

### "Installation failed" Error

1. **Check Device Storage**:
   - Make sure device has enough space

2. **Uninstall Existing App**:
   - If app is already installed, uninstall it first
   - Settings > Apps > Bilingual Lesson Planner > Uninstall

3. **Enable Install via USB**:
   - Settings > Developer Options > Enable "Install via USB"

### Android Studio Can't Find Device

1. **Check ADB Path**:
   - **File** > **Settings** (or **Preferences** on Mac)
   - **Appearance & Behavior** > **System Settings** > **Android SDK**
   - Check **"Android SDK Location"** is correct
   - Usually: `C:\Users\<YourName>\AppData\Local\Android\Sdk`

2. **Update Platform Tools**:
   - **Tools** > **SDK Manager**
   - **SDK Tools** tab
   - Check **"Android SDK Platform-Tools"**
   - Click **Apply** to update

## Alternative: Use Wireless Debugging

If USB is still blocked, you can use wireless debugging (Android 11+):

1. **Connect via USB once** (to set up):
   - Connect device
   - In Android Studio terminal: `adb tcpip 5555`

2. **Find Device IP**:
   - On device: **Settings** > **About Phone** > **Status** > **IP Address**
   - Or: **Settings** > **Wi-Fi** > Tap connected network > View IP

3. **Connect Wirelessly**:
   - In Android Studio terminal: `adb connect <device-ip>:5555`
   - Example: `adb connect 192.168.1.100:5555`

4. **Device Should Appear**:
   - Your device should now show in Android Studio
   - You can disconnect USB and use wireless

## Quick Checklist

- [ ] Android Studio is open
- [ ] Project is loaded (`D:\LP\android`)
- [ ] Device is connected via USB
- [ ] USB mode is "File Transfer" or "MTP"
- [ ] Developer Options enabled on device
- [ ] USB Debugging enabled on device
- [ ] Computer is authorized (popup accepted)
- [ ] Device appears in Android Studio device list
- [ ] Device status is "Online" (green)

## After Connection

Once your device is connected and showing in Android Studio:

1. **Select device** from dropdown
2. **Click Run** (green play button)
3. **App will install and launch** automatically
4. **View logs** in Logcat window

That's it! Android Studio handles everything automatically. 🚀

