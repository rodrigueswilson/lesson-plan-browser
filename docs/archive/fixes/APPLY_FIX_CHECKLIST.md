# Windows 11 Localhost Fix - Application Checklist

## Pre-Flight Safety Steps

### 1. Create System Restore Point (Recommended)
```
1. Press Win + S, search "Create a restore point"
2. Click "Create..." button
3. Name it: "Before KB5066835 localhost fix"
4. Wait for completion
```

### 2. Backup Registry Keys (Recommended)
```bash
# Run as Administrator
cd D:\LP
backup_registry_before_fix.bat
```

This creates backups in `registry_backups/` folder.

---

## Apply the Fix

### Step 1: Run Registry Fix
```
1. Right-click: fix_localhost_registry.bat
2. Select: "Run as administrator"
3. Press any key when prompted
4. Wait for: "Registry keys added successfully!"
```

### Step 2: Restart Computer
```
IMPORTANT: You MUST restart for changes to take effect
```

---

## Post-Restart Validation

### Test 1: Backend Health Check
```bash
cd D:\LP
.\start-backend-no-reload.bat
```

**Expected:** Backend starts and shows "Uvicorn running on http://0.0.0.0:8000"

### Test 2: Direct API Test
```bash
# In a NEW terminal window
cd D:\LP
python test_backend_directly.py
```

**Expected:**
- ✅ Health check passes
- ✅ Users load (3 users)
- ✅ Slots load (5 slots for Daniela Silva)
- When prompted, press 'y' to test processing

**Expected Processing:**
- ✅ Backend terminal shows logs (background_process_started, media_extracted, etc.)
- ✅ Processing completes without hanging
- ✅ Output file created in output/ folder

### Test 3: Frontend Connection
```bash
cd D:\LP\frontend
npm run tauri:dev
```

**Expected:**
- ✅ Tauri window opens
- ✅ Users load in dropdown (no error dialog)
- ✅ Can select user and week
- ✅ Can initiate processing
- ✅ Progress bar updates

### Test 4: End-to-End Processing (Optional)
```bash
# If you have pytest installed
cd D:\LP
pytest tests/test_simple_batch.py -v
```

**Expected:** All tests pass

---

## Success Criteria

### ✅ Fix Applied Successfully If:
1. Backend starts without errors
2. `test_backend_directly.py` completes processing
3. Backend logs appear during processing
4. Output file is created
5. Tauri frontend connects without errors
6. No "connection refused" or "connection reset" errors

### ❌ If Issues Persist:
1. Check backend terminal for new error messages
2. Verify registry keys were added:
   ```bash
   reg query "HKLM\SOFTWARE\Microsoft\IIS\Parameters" /v EnableHttp2
   reg query "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" /v EnableHttp2Tls
   ```
3. Ensure you restarted after applying fix
4. Check Windows Update for KB2267602 (Microsoft's official fix)

---

## Rollback Instructions

### If You Need to Undo the Fix:

**Option A: Use Undo Script**
```bash
# Run as Administrator
cd D:\LP
fix_localhost_registry_undo.bat
# Then restart
```

**Option B: Restore from Backup**
```
1. Go to registry_backups/ folder
2. Double-click the .reg files to restore
3. Restart computer
```

**Option C: Restore System Restore Point**
```
1. Press Win + S, search "Create a restore point"
2. Click "System Restore..."
3. Select the restore point you created
4. Follow the wizard
```

---

## When to Remove the Fix

### Microsoft's Official Fix
Once Microsoft releases the official fix (KB2267602 or later):

1. **Check for updates:**
   ```
   Settings > Windows Update > Check for updates
   ```

2. **Install KB2267602** (or newer fix)

3. **Restart computer**

4. **Remove registry workaround:**
   ```bash
   # Run as Administrator
   cd D:\LP
   fix_localhost_registry_undo.bat
   ```

5. **Restart again**

6. **Test everything still works**

---

## Troubleshooting

### "Access Denied" Error
- You must run the script as Administrator
- Right-click → "Run as administrator"

### "Cannot find path" Error
- Ensure you're in the D:\LP directory
- Use: `cd D:\LP` before running scripts

### Registry Keys Not Taking Effect
- You MUST restart your computer
- Changes don't apply until reboot

### Backend Still Crashes
- Check if KB5066835 is still installed
- Consider uninstalling the update instead
- Check for other Windows updates that might interfere

### Tauri Still Can't Connect
- Verify backend is running on 0.0.0.0:8000
- Check Windows Firewall isn't blocking connections
- Try running frontend as web app instead of Tauri

---

## Additional Resources

### Files Created This Session
- `fix_localhost_registry.bat` - Apply the fix
- `fix_localhost_registry_undo.bat` - Remove the fix
- `backup_registry_before_fix.bat` - Backup registry keys
- `SESSION_7_SOLUTION_FOUND.md` - Complete documentation
- `SESSION_7_COMPLETE_DIAGNOSTIC_REPORT.md` - Full diagnostic report

### Microsoft References
- KB5066835: October 2025 Cumulative Update (buggy)
- KB2267602: Known Issue Rollback (fix)
- https://learn.microsoft.com/en-us/answers/questions/5585563/

---

## Summary

**Problem:** Windows 11 KB5066835 broke localhost HTTP/2 connections
**Solution:** Disable HTTP/2 via registry (temporary workaround)
**Impact:** Forces HTTP/1.1 (minimal performance difference for local dev)
**Duration:** Until Microsoft releases official fix
**Safety:** Fully reversible, backed up, tested by many users

**Estimated Time:**
- Backup: 2 minutes
- Apply fix: 2 minutes
- Restart: 3 minutes
- Testing: 5 minutes
- **Total: ~12 minutes**

---

**Ready to proceed?** Follow the steps above and report back after restart!
