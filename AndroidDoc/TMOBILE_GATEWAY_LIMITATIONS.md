# T-Mobile Gateway Limitations - AP Isolation

**Date:** November 25, 2025  
**Gateway Model:** T-Mobile 5G Gateway  
**Firmware:** 1.101.78  
**UI Version:** v1.10.0  
**Serial:** QS2307559019914

## Gateway Information

Your T-Mobile 5G Gateway is a combined router/modem device provided by T-Mobile. According to [T-Mobile's FAQ](https://www.t-mobile.com/home-internet/faq), these gateways have limited configuration options compared to standard routers.

## AP Isolation Issue

**Problem:** T-Mobile gateways often do not expose AP Isolation settings to users through the web interface. This is a common limitation with ISP-provided routers.

**Why:** 
- ISP routers prioritize simplicity and security
- Advanced settings are often hidden or disabled
- Firmware is locked down to prevent user modifications

## Solutions

### Option 1: Check Settings (Try First)

1. Access gateway at `http://192.168.12.1`
2. Click Settings gear icon (⚙️)
3. Look for:
   - Wi-Fi / Wireless settings
   - Network / Advanced settings
   - Security settings
4. Search for "AP Isolation" or "Client Isolation"

**If found:** Disable it and save.

**If not found:** Continue to Option 2 or 3.

### Option 2: Contact T-Mobile Support

**Phone:** 1-844-275-9310

**What to ask:**
- "Can you disable AP Isolation (Client Isolation) on my gateway remotely?"
- "I need device-to-device communication for a local application"
- "My gateway firmware is 1.101.78, UI version v1.10.0"

**Note:** They may not be able to help, as this is often a firmware limitation.

### Option 3: Use a Personal Router (RECOMMENDED)

This is the most reliable solution for T-Mobile gateways with limited settings.

#### Setup:

1. **Purchase a standard WiFi router**
   - Any brand: TP-Link, Netgear, ASUS, etc.
   - Should support WPA2/WPA3
   - Should allow disabling AP Isolation

2. **Connect router to T-Mobile gateway:**
   - Ethernet cable: T-Mobile gateway LAN port → Your router WAN port
   - Power on your router

3. **Configure your router:**
   - Access admin panel (usually `192.168.1.1` or `192.168.0.1`)
   - Set up WiFi network
   - **Disable AP Isolation** (most routers have this option)
   - Save settings

4. **Optional: Disable WiFi on T-Mobile gateway:**
   - Go to `http://192.168.12.1`
   - Look for option to disable WiFi (may be in Settings)
   - Prevents interference between networks

5. **Connect devices:**
   - Connect both PC and tablet to **your router's WiFi**
   - Not the T-Mobile gateway WiFi

6. **Update app configuration:**
   - Get PC's new IP address: `Get-NetIPAddress` (on PC)
   - Update `frontend/src/lib/api.ts` with new IP
   - Rebuild and reinstall APK

#### Benefits:
- ✅ Full control over network settings
- ✅ Can disable AP Isolation
- ✅ Better performance and features
- ✅ Works regardless of T-Mobile gateway limitations

## T-Mobile Gateway Characteristics

Based on T-Mobile's documentation:
- **Limited Settings:** Web interface shows basic status and minimal configuration
- **Firmware Locked:** Advanced settings are not accessible to users
- **ISP Managed:** T-Mobile controls many settings remotely
- **Security Focused:** AP Isolation may be enabled by default for security

## Current Status

- **Gateway:** T-Mobile 5G Gateway (Firmware 1.101.78)
- **Settings Access:** Limited (Home view shows status only)
- **AP Isolation:** Likely enabled, not user-configurable
- **WiFi Security:** WPA3/WPA3-PERSONAL
- **Solution:** Use personal router (recommended) or contact T-Mobile support

## References

- [T-Mobile Home Internet FAQ](https://www.t-mobile.com/home-internet/faq)
- T-Mobile Support: 1-844-275-9310

