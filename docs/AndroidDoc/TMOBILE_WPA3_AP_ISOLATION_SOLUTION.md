# T-Mobile Router WPA3 AP Isolation - Solution

**Date:** November 25, 2025  
**Router:** T-Mobile Home Internet Gateway  
**WiFi Security:** WPA3/WPA3-PERSONAL  
**Issue:** AP Isolation cannot be disabled through web interface

## Problem

Your T-Mobile router is using **WPA3/WPA3-PERSONAL** security, and the web dashboard doesn't show advanced settings to disable AP Isolation. This is common with ISP-provided routers, especially those using WPA3.

## Solution Options

### Option 1: Check Settings Page (Try First)

1. **Click the Gear Icon (⚙️)** in the left navigation bar
2. **Look for:**
   - "Wi-Fi" or "Wireless" section
   - "Advanced Settings"
   - "Network Settings"
   - "Security Settings"
3. **Search for:**
   - "AP Isolation"
   - "Client Isolation"
   - "Wireless Isolation"
   - "Station Isolation"

**If you find it:** Disable it and save.

**If you don't find it:** Continue to Option 2 or 3.

### Option 2: Use a Personal Router (RECOMMENDED)

This is the most reliable solution for T-Mobile Home Internet routers with limited settings.

#### Setup Steps:

1. **Purchase a compatible router:**
   - Any standard WiFi router (TP-Link, Netgear, ASUS, etc.)
   - Should support WPA2 or WPA3
   - Should allow disabling AP Isolation

2. **Connect the router:**
   - Use an Ethernet cable
   - Connect from T-Mobile gateway's **LAN port** to your router's **WAN port**
   - Power on your router

3. **Configure your router:**
   - Access your router's admin panel (usually `192.168.1.1` or `192.168.0.1`)
   - Set up WiFi network (name and password)
   - **Disable AP Isolation** (most routers have this option)
   - Save settings

4. **Disable WiFi on T-Mobile gateway:**
   - Go back to T-Mobile dashboard (`http://192.168.12.1`)
   - Look for option to disable WiFi (may be in Settings)
   - This prevents interference between the two WiFi networks

5. **Connect devices:**
   - Connect both PC and tablet to **your personal router's WiFi**
   - Not the T-Mobile gateway WiFi

6. **Update API URL:**
   - Your PC will get a new IP address from your router
   - Check new IP: `Get-NetIPAddress` (on PC)
   - Update `frontend/src/lib/api.ts` with new IP
   - Rebuild and reinstall APK

#### Benefits:
- ✅ Full control over network settings
- ✅ Can disable AP Isolation
- ✅ Better performance and features
- ✅ More reliable device-to-device communication

### Option 3: Contact T-Mobile Support

If you prefer not to use a personal router:

1. **Call T-Mobile Support:** 1-844-275-9310
2. **Explain:** You need device-to-device communication disabled (AP Isolation)
3. **Ask:** Can they disable it remotely or provide instructions?
4. **Mention:** Your router uses WPA3 and the web interface doesn't show the option

**Note:** They may not be able to help, as many ISP routers have this limitation by design.

### Option 4: Try Changing WPA Version (May Not Work)

Some users report that changing WPA version can help:

1. In Settings, look for **"Wi-Fi Security"** or **"WPA Settings"**
2. Try changing from **"WPA3"** to **"WPA2"** or **"WPA/WPA2"**
3. Save and restart router
4. Test the app

**Note:** This may not be available on T-Mobile routers, and may not solve the AP Isolation issue.

## Why This Happens

- **ISP Router Limitations:** T-Mobile (and other ISPs) often provide routers with limited configuration options
- **WPA3 Security:** Newer security protocols sometimes have AP Isolation enabled by default for security
- **Firmware Restrictions:** ISP firmware may hide advanced settings from users

## Recommended Solution

**Use a Personal Router (Option 2)** is the most reliable solution because:
- You have full control
- Most routers allow disabling AP Isolation
- Better network management
- Works regardless of ISP router limitations

## Current Status

- **Router:** T-Mobile Home Internet Gateway
- **WiFi Security:** WPA3/WPA3-PERSONAL
- **Dashboard:** Limited settings (Home view only)
- **AP Isolation:** Likely enabled, cannot be disabled via web interface
- **Solution:** Use personal router or contact T-Mobile support

## Next Steps

1. **First:** Try clicking the Settings gear icon to see if more options appear
2. **If no options:** Consider purchasing a personal router (most reliable)
3. **Alternative:** Contact T-Mobile support to ask about AP Isolation

