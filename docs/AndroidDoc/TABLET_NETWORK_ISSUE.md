# Tablet Network Connectivity Issue

**Date:** November 25, 2025  
**Status:** Network connectivity issue between tablet and PC

## Problem

The app is installed and running on the tablet, but shows:
- **Error:** "Failed to load users. API request failed: Failed to fetch"
- **Root Cause:** Tablet cannot reach PC backend over network

## Diagnosis

1. ✅ **Backend is running** on PC (port 8000)
2. ✅ **Backend is accessible** from PC itself
3. ❌ **Tablet cannot ping PC** (100% packet loss)
4. ✅ **ADB port forwarding** is set up (localhost:8000)
5. ❌ **WebView may not support ADB port forwarding**

## Solution Options

### Option 1: Connect Tablet and PC to Same WiFi Network (Recommended)

**Steps:**
1. Ensure both tablet and PC are connected to the same WiFi network
2. Verify PC's IP address: `192.168.12.153` (or get current IP)
3. Update `frontend/src/lib/api.ts` with correct PC IP
4. Rebuild and reinstall APK

**Verify same network:**
```powershell
# On PC - get IP
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" }

# On tablet - check WiFi IP
adb -s <device> shell "ip addr show wlan0 | grep inet"
```

### Option 2: Use ADB Port Forwarding (Current Attempt)

**Status:** Set up but may not work with WebView

**Commands:**
```powershell
# Set up port forwarding
adb -s R52Y90L71YP reverse tcp:8000 tcp:8000

# Verify
adb -s R52Y90L71YP reverse --list
```

**Note:** Tauri's WebView may not support ADB reverse port forwarding. This works for native Android apps but may not work for WebView-based apps.

### Option 3: Use PC's Hotspot

If tablet and PC can't be on same WiFi:
1. Create WiFi hotspot on PC
2. Connect tablet to PC's hotspot
3. Use PC's hotspot IP address in API URL

## Current Configuration

- **API URL in code:** `http://localhost:8000/api` (for ADB forwarding)
- **PC IP:** `192.168.12.153`
- **Backend:** Running on `0.0.0.0:8000` (accessible from all interfaces)
- **CORS:** Allows all origins (`*`)
- **Network Security:** Allows localhost and cleartext HTTP

## Next Steps

1. **Verify WiFi networks match:**
   - Check tablet's WiFi network name
   - Check PC's WiFi network name
   - They must be the same

2. **If on same network but still can't connect:**
   - Check Windows Firewall (should allow port 8000)
   - Verify backend is listening on `0.0.0.0:8000` (not just `127.0.0.1:8000`)
   - Test with: `curl http://192.168.12.153:8000/api/users` from another device

3. **If ADB forwarding is the issue:**
   - Switch back to direct IP approach
   - Ensure tablet and PC are on same network
   - Update API URL to use PC's IP address

## Files Modified

- `frontend/src/lib/api.ts` - Updated to use localhost:8000 (for ADB forwarding)
- `frontend/src-tauri/gen/android/app/src/main/res/xml/network_security_config.xml` - Allows localhost

