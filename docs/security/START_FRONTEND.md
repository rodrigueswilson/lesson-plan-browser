# Starting the Frontend

## Quick Start

**In a new PowerShell terminal:**

```powershell
cd D:\LP\frontend
npm run dev
```

**Wait for output:**
```
VITE v5.x.x ready in XXX ms
➜ Local:   http://localhost:1420/
```

Then open http://localhost:1420 in your browser.

---

## If Frontend Doesn't Start

### Check if port 1420 is in use:
```powershell
netstat -ano | findstr ":1420"
```

### Kill process on port 1420 (if needed):
```powershell
# Find process ID
netstat -ano | findstr ":1420" | findstr "LISTENING"

# Kill it (replace PID with actual process ID)
Stop-Process -Id <PID> -Force
```

### Install dependencies (if needed):
```powershell
cd D:\LP\frontend
npm install
```

### Then start again:
```powershell
npm run dev
```

---

## Testing RLS

Once the frontend is running:

1. **Open http://localhost:1420**
2. **Create/Login as a user**
3. **Create some class slots and weekly plans**
4. **Verify you can only see your own data**

The RLS policies will ensure users can only access their own data at the database level, even if there's a bug in the frontend or backend code.

---

## Current Status

- ✅ Backend: Running on http://127.0.0.1:8000
- ✅ RLS: Enabled on all tables
- ⏳ Frontend: Starting...

