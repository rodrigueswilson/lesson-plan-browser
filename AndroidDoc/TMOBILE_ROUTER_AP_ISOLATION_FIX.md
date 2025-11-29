# T-Mobile Home Internet Router - AP Isolation Fix

**Date:** November 25, 2025  
**Router:** T-Mobile Home Internet Gateway  
**Issue:** Tablet cannot reach PC backend due to AP Isolation

## T-Mobile Router Access

### Step 1: Access Router Admin Panel

1. **Connect to T-Mobile WiFi** (on your PC or tablet)
2. **Open a web browser** (Chrome, Edge, Firefox, etc.)
3. **Enter the gateway IP address:**
   ```
   http://192.168.12.1
   ```
   ⚠️ **Note:** T-Mobile routers use `192.168.12.1` (not the standard `192.168.1.1`)

4. **Login credentials:**
   - **Username:** `admin` (default)
   - **Password:** Check the sticker on your T-Mobile gateway/router
     - Usually found on the bottom or back of the device
     - Format: Usually a combination of letters and numbers

### Step 2: Navigate to Wireless Settings

Once logged in, look for:
- **"Wi-Fi"** or **"Wireless"** section
- **"Network Settings"** or **"Advanced Settings"**
- **"Security"** or **"Wireless Security"**

### Step 3: Look for AP Isolation Setting

Search for any of these options:
- "AP Isolation"
- "Client Isolation"
- "Wireless Isolation"
- "Station Isolation"
- "Access Point Isolation"

**Location:** Usually under:
- Wi-Fi → Advanced Settings
- Network → Wireless Settings
- Security → Wireless Security

### Step 4: Disable AP Isolation (If Available)

If you find the setting:
1. **Toggle it to "Disabled" or "Off"**
2. **Click "Save" or "Apply"**
3. **Wait for router to restart** (1-2 minutes)

## Important: T-Mobile Router Limitations

⚠️ **T-Mobile routers often have limited settings** and may not expose AP Isolation directly in the web interface. This is common with ISP-provided routers.

### Alternative Solution 1: Change WPA Security Mode

Some users have reported that changing the WPA version can help:

1. In router settings, find **"Wi-Fi Security"** or **"WPA Settings"**
2. Change from **"WPA2"** to **"WPA/WPA2"** (mixed mode)
3. Save and restart router
4. Test the app again

### Alternative Solution 2: Use a Personal Router (Recommended)

If AP Isolation cannot be disabled on the T-Mobile router:

1. **Purchase a compatible router** (any standard WiFi router)
2. **Connect it to T-Mobile gateway:**
   - Use an Ethernet cable
   - Connect from T-Mobile gateway's LAN port to your router's WAN port
3. **Disable WiFi on T-Mobile gateway** (to prevent interference)
4. **Configure your personal router:**
   - Set up WiFi network
   - **Disable AP Isolation** (most routers allow this)
   - Connect both PC and tablet to your personal router's WiFi
5. **Update API URL if needed:**
   - Your PC will get a new IP address from your personal router
   - Update `frontend/src/lib/api.ts` with the new IP

### Alternative Solution 3: Contact T-Mobile Support

If you cannot find the settings:

1. **Call T-Mobile Support:** 1-844-275-9310
2. **Ask them to:**
   - Disable AP Isolation on your gateway
   - Or confirm if it's possible on your specific model
3. **Mention:** You need device-to-device communication for a local application

## Testing After Changes

1. **Restart both devices** (PC and tablet)
2. **Verify backend is running:**
   ```powershell
   # On PC
   netstat -ano | Select-String ":8000.*LISTENING"
   ```
3. **Test the app on tablet:**
   - Open the app
   - Users should load successfully
   - No "Failed to fetch" error

## Current Configuration

- **PC IP:** `192.168.12.153`
- **Backend URL:** `http://192.168.12.153:8000/api`
- **Router IP:** `192.168.12.1` (T-Mobile gateway)
- **Status:** Waiting for AP Isolation to be disabled

## Router Models

T-Mobile Home Internet uses various gateway models:
- **Nokia 5G21**
- **Arcadyan KVD21**
- **Sagemcom Fast 5688W**
- Others

Settings may vary by model. If you can't find the option, try:
1. Contacting T-Mobile support
2. Using a personal router (most reliable solution)

## Quick Test: Verify Router IP

If `192.168.12.1` doesn't work, find your router's IP:

**On Windows (PC):**
```powershell
ipconfig | Select-String "Default Gateway"
```

**On Android (Tablet):**
- Settings → WiFi → Tap your network → Advanced → Gateway IP

The gateway IP is your router's admin address.

