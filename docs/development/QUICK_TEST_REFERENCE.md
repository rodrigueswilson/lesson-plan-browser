# Quick Test Reference

## 🚀 Start Everything

```powershell
# Terminal 1: Backend
cd D:\LP
$env:USE_SUPABASE = "False"
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd D:\LP\frontend
npm run dev

# Open: http://localhost:1420/
```

## ✅ Quick Test Checklist

### 1. User Management (2 min)
- [ ] Users load in dropdown (4 users)
- [ ] Select user → data loads
- [ ] Create user → appears in list
- [ ] Settings → update base path

### 2. Class Slots (3 min)
- [ ] Go to Plans page
- [ ] Add slot → fills form → saves
- [ ] Edit slot → changes save automatically
- [ ] Delete slot → removed
- [ ] Drag to reorder → order persists

### 3. Weekly Plans (5 min)
- [ ] Go to Home page
- [ ] Select week (if user has base_path_override)
- [ ] Select slots
- [ ] Process week → progress shows → completes

### 4. Plan History (1 min)
- [ ] Go to History page
- [ ] View past plans
- [ ] Check status indicators

### 5. Analytics (1 min)
- [ ] Go to Analytics page
- [ ] View metrics
- [ ] Check chart

## 🐛 Quick Debug

### Users Not Loading?
```powershell
# Check backend
Invoke-WebRequest http://127.0.0.1:8000/api/users

# Check frontend console (F12)
# Look for: [UserSelector] errors
```

### Slots Not Saving?
```powershell
# Check API directly
$headers = @{ "X-Current-User-Id" = "USER_ID" }
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/users/USER_ID/slots" -Headers $headers

# Check frontend console
# Look for: [SlotConfigurator] errors
```

### Processing Fails?
```powershell
# Check backend logs
# Look for LLM errors, file path errors

# Check frontend console
# Look for: [BatchProcessor] errors
```

## 📋 Test Results

**Date:** ___________

**User Management:** ✅ / ❌  
**Class Slots:** ✅ / ❌  
**Weekly Plans:** ✅ / ❌  
**Plan History:** ✅ / ❌  
**Analytics:** ✅ / ❌  

**Issues Found:**
1. 
2. 
3. 

---

**Full Guide:** `docs/development/FRONTEND_TESTING_GUIDE.md`

