# Router AP Isolation Fix

**Date:** November 25, 2025  
**Issue:** Tablet cannot reach PC backend despite being on same WiFi network

## Problem

The app shows "Failed to fetch" error when trying to connect to the PC backend, even though:
- ✅ Both devices are on the same WiFi network
- ✅ Backend is running and accessible from PC
- ✅ Windows Firewall allows port 8000
- ✅ Network security config allows cleartext HTTP

## Root Cause: Router AP Isolation

**AP Isolation** (Access Point Isolation) is a router feature that prevents devices on the same WiFi network from communicating with each other. This is a security feature, but it blocks device-to-device communication needed for the tablet to reach the PC backend.

## Solution: Disable AP Isolation

### Step 1: Access Router Settings

1. Find your router's IP address (usually `192.168.1.1` or `192.168.0.1`)
2. Open a web browser and go to: `http://192.168.1.1` (or your router's IP)
3. Log in with your router admin credentials

### Step 2: Find AP Isolation Setting

The setting name varies by router manufacturer:

**Common Names:**
- "AP Isolation"
- "Client Isolation"
- "Wireless Isolation"
- "Station Isolation"
- "AP/Client Isolation"
- "Wireless Client Isolation"

**Where to Find It:**
- **Linksys:** Wireless > Wireless Security > AP Isolation
- **Netgear:** Advanced > Wireless Settings > AP Isolation
- **TP-Link:** Wireless > Wireless Settings > AP Isolation
- **ASUS:** Wireless > Professional > AP Isolation
- **D-Link:** Advanced > Wireless Settings > AP Isolation

### Step 3: Disable AP Isolation

1. Find the "AP Isolation" or "Client Isolation" setting
2. **Disable** or **Turn Off** the setting
3. **Save** the changes
4. Router may restart (wait 1-2 minutes)

### Step 4: Verify

After disabling AP Isolation:

1. **On PC:** Verify backend is still running
   ```powershell
   # Check if port 8000 is listening
   netstat -ano | Select-String ":8000.*LISTENING"
   ```

2. **On Tablet:** The app should now be able to connect
   - Restart the app if needed
   - Users should load successfully

## Alternative: Windows Firewall Check

If AP Isolation is not the issue, verify Windows Firewall:

1. Open **Windows Defender Firewall**
2. Go to **Advanced Settings**
3. Check **Inbound Rules** for port 8000
4. Ensure there's a rule allowing:
   - **Protocol:** TCP
   - **Local Port:** 8000
   - **Action:** Allow
   - **Profile:** Private, Domain (or All)

## Testing Connectivity

After disabling AP Isolation, test from tablet:

```powershell
# From PC, test if tablet can reach PC
# (This requires knowing tablet's IP, which you can get from router admin panel)

# Or test from another device on the same network:
# Open browser on phone/tablet and go to: http://192.168.12.153:8000/api/users
```

## Notes

- **Security Consideration:** Disabling AP Isolation allows devices on your network to communicate with each other. This is generally safe on a home network, but be aware of the security implications.
- **Router Restart:** Some routers restart when you change this setting. Wait for the router to fully restart before testing.
- **Multiple Networks:** If you have a guest network, AP Isolation might be enabled there but not on the main network. Ensure both devices are on the same network (main or guest).

## Current Configuration

- **PC IP:** `192.168.12.153`
- **Backend URL:** `http://192.168.12.153:8000/api`
- **Network:** Same WiFi network (both devices)
- **Status:** Waiting for AP Isolation to be disabled

