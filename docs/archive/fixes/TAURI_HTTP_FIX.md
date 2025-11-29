# Tauri HTTP Connection Fix

## 🔍 Problem Identified

**Error**: "Network Error - Cannot load users"

**Root Cause**: The frontend is using `axios` which doesn't work in Tauri desktop apps. Tauri requires using its own HTTP client (`@tauri-apps/api/http`) for security reasons.

---

## ✅ Solution

Replace the API client to use Tauri's HTTP fetch instead of axios.

---

## 📝 Step-by-Step Fix

### Step 1: Backup Current API File

```bash
copy frontend\src\lib\api.ts frontend\src\lib\api.ts.backup
```

### Step 2: Replace with Tauri-Compatible Version

```bash
copy api_tauri_fixed.ts frontend\src\lib\api.ts
```

### Step 3: Restart the Frontend

Stop the frontend (Ctrl+C) and restart:
```bash
cd frontend
npm run tauri:dev
```

---

## 🔧 What Changed

### Before (Using axios - doesn't work in Tauri):
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export const userApi = {
  list: () => api.get<User[]>('/users'),
  // ...
};
```

### After (Using Tauri HTTP - works in Tauri):
```typescript
import { fetch } from '@tauri-apps/api/http';

async function request<T>(method: string, url: string, body?: any) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { data: response.data as T };
}

export const userApi = {
  list: () => request<User[]>('GET', `${API_BASE_URL}/users`),
  // ...
};
```

---

## 🎯 Why This Fixes It

1. **Tauri Security**: Tauri apps run in a sandboxed environment
2. **HTTP Scope**: Only allowed URLs (configured in `tauri.conf.json`) can be accessed
3. **Tauri HTTP Client**: Uses the allowed HTTP scope properly
4. **Axios Limitation**: Regular `axios` bypasses Tauri's security and fails

---

## ✅ Verification

After applying the fix and restarting:

1. **Open the app**
2. **Check Console** (F12):
   ```
   [API] GET http://localhost:8000/api/users
   [API] Response: 200 [array of users]
   [UserSelector] Users loaded: 12 users
   ```

3. **Users dropdown should populate** with all 12 users

4. **Create User should work**:
   ```
   [API] POST http://localhost:8000/api/users
   [API] Response: 200 {user object}
   [UserSelector] User created successfully
   ```

---

## 🐛 If It Still Doesn't Work

### Check 1: Tauri HTTP Scope

Verify `frontend/src-tauri/tauri.conf.json` has:
```json
"http": {
  "all": true,
  "request": true,
  "scope": ["http://localhost:8000/**"]
}
```

### Check 2: Backend Running

```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy",...}`

### Check 3: Import Statement

Make sure the import is correct:
```typescript
import { fetch } from '@tauri-apps/api/http';
```

NOT:
```typescript
import axios from 'axios';  // ❌ Won't work in Tauri
```

---

## 📊 Testing the Fix

### Test 1: Health Check
```typescript
// In browser console (F12)
import { fetch } from '@tauri-apps/api/http';

fetch('http://localhost:8000/api/health', { method: 'GET' })
  .then(r => console.log('Health:', r))
  .catch(e => console.error('Error:', e));
```

### Test 2: List Users
```typescript
fetch('http://localhost:8000/api/users', { method: 'GET' })
  .then(r => console.log('Users:', r.data))
  .catch(e => console.error('Error:', e));
```

### Test 3: Create User
```typescript
fetch('http://localhost:8000/api/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Test User', email: 'test@test.com' })
})
  .then(r => console.log('Created:', r.data))
  .catch(e => console.error('Error:', e));
```

---

## 🎓 Understanding Tauri HTTP

### Why Tauri Has Its Own HTTP Client

1. **Security**: Prevents arbitrary network access
2. **Scope Control**: Only allowed URLs can be accessed
3. **Cross-Platform**: Works consistently on Windows/Mac/Linux
4. **Native Integration**: Uses OS-native HTTP stack

### Allowed URLs (from tauri.conf.json)

```json
"scope": ["http://localhost:8000/**"]
```

This means:
- ✅ `http://localhost:8000/api/users` - Allowed
- ✅ `http://localhost:8000/api/health` - Allowed
- ❌ `http://google.com` - Blocked
- ❌ `http://localhost:3000` - Blocked

---

## 🚀 Expected Behavior After Fix

1. **App Starts**:
   - Console shows: `[API] GET http://localhost:8000/api/users`
   - Console shows: `[API] Response: 200 [...]`
   - Console shows: `[UserSelector] Users loaded: 12 users`
   - Users dropdown populates

2. **Click "Add User"**:
   - Form appears
   - Console shows: `[UserSelector] Add User button clicked`

3. **Create User**:
   - Console shows: `[API] POST http://localhost:8000/api/users`
   - Console shows: `[API] Response: 200 {...}`
   - Alert: "User created successfully!"
   - New user appears in dropdown

---

## 📁 Files for This Fix

1. **api_tauri_fixed.ts** - New Tauri-compatible API client
2. **TAURI_HTTP_FIX.md** - This document

---

## 💡 Quick Summary

**Problem**: Axios doesn't work in Tauri apps
**Solution**: Use `@tauri-apps/api/http` instead
**Fix**: Replace `frontend/src/lib/api.ts` with Tauri version
**Result**: Frontend can now connect to backend! ✅

---

## 🎯 Next Steps

1. ✅ Backup current api.ts
2. ✅ Copy api_tauri_fixed.ts to api.ts
3. ✅ Restart frontend
4. ✅ Test - users should load!
5. ✅ Create a user - should work!

The improved UserSelector component will show you exactly what's happening with detailed console logs! 🚀
