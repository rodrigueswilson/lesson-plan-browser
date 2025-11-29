# RLS vs Backend Authorization - Decision Summary

**Date:** January 2025  
**Question:** Should we enable Row-Level Security (RLS) on Supabase tables?  
**Answer:** Not yet - Backend authorization is the correct immediate solution.

---

## Summary

The Supabase AI assistant's recommendation is **mostly correct**, but RLS is **not appropriate** for our current architecture. We've implemented **backend authorization checks** instead, which is the right approach for a desktop app using service role keys.

## What We Implemented

### ✅ Backend Authorization (Done)

1. **Authorization Module** (`backend/authorization.py`)
   - `verify_user_access()` - Verifies user ID matches
   - `get_current_user_id()` - Extracts user ID from header
   - `verify_slot_ownership()` - Verifies slot ownership

2. **Protected Endpoints** (All user-scoped endpoints)
   - User management endpoints
   - Class slot endpoints
   - Weekly plan endpoints
   - All verify `X-Current-User-Id` header matches requested `user_id`

3. **RLS Policies Prepared** (`docs/supabase_rls_policies.sql`)
   - Policies written but commented out
   - Ready for future use when Supabase Auth is integrated

## Why RLS Won't Work Now

### 1. Service Role Key Bypasses RLS
```python
# Current setup uses service_role key
self.client = create_client(supabase_url, supabase_service_role_key)
# ↑ This bypasses ALL RLS policies
```

**Impact:** Even if RLS is enabled, the service role key ignores all policies.

### 2. No Supabase Auth Integration
```sql
-- RLS policies require auth.uid()
CREATE POLICY "users_select_own" ON users
    FOR SELECT USING (auth.uid()::text = user_id);
-- ↑ auth.uid() returns NULL without Supabase Auth
```

**Impact:** Policies can't identify the user without Supabase Auth JWTs.

### 3. Desktop App Architecture
- Single user per instance
- Local backend with direct database access
- No multi-tenant web architecture

**Impact:** RLS is designed for multi-user web apps, not desktop apps.

## What We Did Instead

### Backend Authorization Checks

```python
# Example: Protected endpoint
@app.get("/api/users/{user_id}/slots")
async def get_user_slots(
    user_id: str,
    current_user_id: Optional[str] = get_current_user_id,  # From header
):
    verify_user_access(user_id, current_user_id, allow_if_none=True)
    # ↑ Verifies user IDs match before database access
    ...
```

**Benefits:**
- ✅ Works with current architecture
- ✅ No database changes required
- ✅ Backward compatible (header optional)
- ✅ Provides defense-in-depth security
- ✅ Logs authorization failures

## When to Enable RLS

Enable RLS when:

1. ✅ **Supabase Auth is integrated**
   - Users authenticate via JWT tokens
   - Backend validates tokens
   - `auth.uid()` is available in policies

2. ✅ **Using anon key for client requests**
   - Service role key removed from client code
   - Client uses anon key with JWT tokens
   - RLS policies can enforce access

3. ✅ **Migrating to web/multi-user architecture**
   - Multiple users accessing same database
   - Need database-level enforcement
   - Defense-in-depth security model

## Migration Path

### Current State (Phase 1)
- ✅ Backend authorization checks implemented
- ✅ Header-based user identification
- ✅ Backward compatible (header optional)
- ❌ RLS disabled (not needed yet)

### Next Steps (Phase 2)
- [ ] Frontend sends `X-Current-User-Id` header
- [ ] Test authorization with real requests
- [ ] Monitor authorization logs
- [ ] Make header required (`allow_if_none=False`)

### Future (Phase 3)
- [ ] Integrate Supabase Auth
- [ ] Replace header with JWT tokens
- [ ] Enable RLS policies
- [ ] Switch to anon key for client requests
- [ ] Remove service role key from client code

## Files Created/Modified

### New Files
- `backend/authorization.py` - Authorization helpers
- `docs/supabase_rls_policies.sql` - RLS policies (prepared for future)
- `docs/security/AUTHORIZATION_IMPLEMENTATION.md` - Implementation guide
- `docs/security/RLS_AUTHORIZATION_DECISION.md` - This file

### Modified Files
- `backend/api.py` - Added authorization checks to all user-scoped endpoints

## Recommendations

### ✅ Do This Now
1. **Use backend authorization** - Already implemented
2. **Update frontend** - Send `X-Current-User-Id` header
3. **Monitor logs** - Track authorization failures
4. **Test thoroughly** - Verify authorization works

### ❌ Don't Do This Yet
1. **Don't enable RLS** - Won't work without Supabase Auth
2. **Don't remove service role key** - Still needed for backend operations
3. **Don't make header required yet** - Wait until frontend is updated

### 🔮 Plan For Future
1. **Supabase Auth integration** - When moving to web/multi-user
2. **Enable RLS** - After Auth is integrated
3. **Remove service role from client** - After RLS is enabled

## Conclusion

**The Supabase AI assistant's analysis was correct**, but the recommendation to enable RLS immediately was premature. We've implemented the **correct solution** (backend authorization) that works with our current architecture, and **prepared RLS policies** for future use when Supabase Auth is integrated.

---

**Status:** ✅ Backend authorization implemented, RLS policies prepared for future

