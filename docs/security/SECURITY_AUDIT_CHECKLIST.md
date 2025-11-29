# Security Audit Checklist

**Date:** January 2025  
**Purpose:** Verify security hardening recommendations from Supabase AI assistant

---

## ✅ Completed Items

### Backend Authorization
- [x] Authorization module created (`backend/authorization.py`)
- [x] User ID format validation added
- [x] Sanitized logging (no PII in logs)
- [x] All user-scoped endpoints protected
- [x] Unit tests created (`tests/test_authorization.py`)

### RLS Preparation
- [x] RLS policies prepared (`docs/supabase_rls_policies.sql`)
- [x] Policies validated against schema (TEXT columns, not UUID)
- [x] Policies commented out (not enabled yet)
- [x] Migration path documented

### Documentation
- [x] Authorization implementation guide
- [x] RLS decision rationale
- [x] Security audit checklist (this file)

---

## 🔍 Items to Verify

### 1. Service Role Key Security

**Check:** Service role key is NOT in client code

**Action Items:**
- [ ] Audit frontend codebase for `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Audit frontend codebase for `service_role`
- [ ] Verify `.env` files are in `.gitignore`
- [ ] Verify no keys in build artifacts
- [ ] Check Tauri config for exposed keys

**Command to check:**
```bash
# Search frontend for service role references
grep -r "service_role\|SERVICE_ROLE" frontend/
grep -r "SUPABASE.*KEY" frontend/

# Check for .env files (should be gitignored)
find . -name ".env*" -not -path "./node_modules/*"
```

**Status:** ✅ Initial check shows no service_role keys in frontend

---

### 2. Frontend API Client

**Check:** Frontend sends `X-Current-User-Id` header

**Action Items:**
- [ ] Update `api_tauri_fixed.ts` to send header
- [ ] Update all API calls to include current user ID
- [ ] Test authorization with header present
- [ ] Test authorization without header (backward compat)

**Current Status:** ⚠️ Header not yet implemented in frontend

**Example Implementation:**
```typescript
// In api_tauri_fixed.ts
async function request<T>(method: string, url: string, body?: any, userId?: string): Promise<{ data: T }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (userId) {
    headers['X-Current-User-Id'] = userId;
  }
  
  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    timeout: 120,
  });
  // ...
}
```

---

### 3. Database Indices

**Check:** Indices exist on ownership columns for RLS performance

**Action Items:**
- [x] Verify `idx_class_slots_user_id` exists
- [x] Verify `idx_weekly_plans_user_id` exists
- [x] Verify `idx_performance_metrics_plan_id` exists
- [ ] Add index on `users.id` if not exists (for RLS policies)

**SQL to verify:**
```sql
-- Check existing indices
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('users', 'class_slots', 'weekly_plans', 'performance_metrics');

-- Add index on users.id if needed (for RLS)
CREATE INDEX IF NOT EXISTS idx_users_id ON public.users(id);
```

**Status:** ✅ Indices already exist in schema

---

### 4. Authorization Logging

**Check:** Logs contain enough context but no PII

**Action Items:**
- [x] Sanitize user IDs in logs (truncate long IDs)
- [x] Log authorization failures with context
- [x] Avoid logging full user IDs
- [ ] Set up log monitoring/alerts for authorization failures
- [ ] Review log retention policy

**Current Implementation:**
- User IDs truncated to 8 chars + "..." in logs
- Authorization failures logged with sanitized IDs
- No PII (emails, names) in authorization logs

---

### 5. Rate Limiting

**Check:** Endpoints are rate-limited to prevent brute force

**Action Items:**
- [ ] Add rate limiting middleware to FastAPI
- [ ] Configure rate limits per endpoint
- [ ] Set lower limits for authorization-sensitive endpoints
- [ ] Monitor rate limit violations

**Recommended Implementation:**
```python
# Add to backend/api.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/users/{user_id}/slots")
@limiter.limit("10/minute")  # Lower limit for auth-sensitive endpoints
async def get_user_slots(...):
    ...
```

**Status:** ⚠️ Not yet implemented

---

### 6. Integration Tests

**Check:** Authorization works end-to-end

**Action Items:**
- [x] Unit tests for authorization module
- [ ] Integration tests for API endpoints
- [ ] Test with valid header (should succeed)
- [ ] Test with mismatched header (should fail 403)
- [ ] Test without header (should succeed for backward compat)
- [ ] Test with invalid user_id format (should fail 400)

**Test Cases Needed:**
```python
# tests/test_api_authorization.py
def test_get_user_slots_with_valid_header():
    """Valid header should succeed"""
    
def test_get_user_slots_with_mismatched_header():
    """Mismatched header should fail 403"""
    
def test_get_user_slots_without_header():
    """No header should succeed (backward compat)"""
    
def test_update_slot_unauthorized():
    """Updating another user's slot should fail 403"""
```

**Status:** ⚠️ Unit tests done, integration tests pending

---

### 7. RLS Policy Validation

**Check:** RLS policies match actual schema

**Action Items:**
- [x] Verify policies use `auth.uid()::text` (not `auth.uid()`)
- [x] Verify policies match TEXT columns (not UUID)
- [x] Verify performance_metrics policy uses EXISTS subquery
- [ ] Test policies in staging before enabling
- [ ] Document policy testing procedure

**Schema Validation:**
- ✅ `users.id` is TEXT → `auth.uid()::text = id`
- ✅ `class_slots.user_id` is TEXT → `auth.uid()::text = user_id`
- ✅ `weekly_plans.user_id` is TEXT → `auth.uid()::text = user_id`
- ✅ `performance_metrics` uses EXISTS subquery (correct)

**Status:** ✅ Policies validated against schema

---

### 8. Server-Side User Derivation (Future)

**Check:** Plan for server-side user mapping

**Action Items:**
- [ ] Design session token system
- [ ] Plan local user → DB user_id mapping
- [ ] Document migration from header to session tokens
- [ ] Implement session validation

**Current Status:** ⚠️ Using header-based auth (acceptable for desktop app)

**Future Enhancement:**
- Desktop app authenticates locally
- Backend stores signed session token
- Backend maps session → user_id server-side
- Header becomes session token instead of user_id

---

### 9. Staging RLS Enablement Plan

**Check:** Plan exists for enabling RLS safely

**Action Items:**
- [ ] Create staging Supabase project
- [ ] Test Supabase Auth integration in staging
- [ ] Enable RLS in staging
- [ ] Test all endpoints with RLS enabled
- [ ] Document rollback procedure
- [ ] Create production enablement checklist

**Staging Checklist:**
1. [ ] Supabase Auth configured
2. [ ] Backend uses anon key (not service_role)
3. [ ] JWT tokens validated server-side
4. [ ] RLS policies enabled
5. [ ] All endpoints tested
6. [ ] Performance verified (indices working)
7. [ ] Rollback plan ready

**Status:** ⚠️ Plan documented but not executed

---

## 📊 Summary

### Completed: 5/9 Major Items
- ✅ Backend authorization implemented
- ✅ RLS policies prepared and validated
- ✅ Unit tests created
- ✅ Documentation complete
- ✅ Indices verified

### In Progress: 2/9 Major Items
- ⚠️ Frontend header implementation
- ⚠️ Integration tests

### Pending: 2/9 Major Items
- ⚠️ Rate limiting
- ⚠️ Staging RLS enablement

---

## 🎯 Priority Actions

### High Priority (Do Now)
1. **Update frontend** to send `X-Current-User-Id` header
2. **Add integration tests** for authorization
3. **Audit service_role key** usage (verify not in frontend)

### Medium Priority (Do Soon)
4. **Add rate limiting** to prevent brute force
5. **Set up log monitoring** for authorization failures

### Low Priority (Plan For Future)
6. **Server-side user derivation** (when moving to web)
7. **Staging RLS enablement** (when adding Supabase Auth)

---

## 🔒 Security Posture

**Current Level:** Medium-High
- ✅ Backend authorization implemented
- ✅ Input validation added
- ✅ Sanitized logging
- ⚠️ Header-based auth (acceptable for desktop)
- ⚠️ No rate limiting yet
- ⚠️ RLS not enabled (not needed yet)

**Target Level:** High
- ✅ Backend authorization
- ✅ Input validation
- ✅ Sanitized logging
- [ ] Rate limiting
- [ ] Integration tests
- [ ] Log monitoring
- [ ] RLS enabled (when Auth added)

---

**Last Updated:** January 2025  
**Next Review:** After frontend header implementation

