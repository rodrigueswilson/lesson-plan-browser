# Authorization Implementation

**Date:** January 2025  
**Status:** ✅ Implemented - Backend authorization checks added

---

## Overview

This document describes the authorization system implemented to protect user data in the API endpoints. The implementation provides defense-in-depth security by verifying that users can only access their own data.

## Current Architecture

- **Desktop App:** Tauri frontend with local FastAPI backend
- **Database:** Supabase PostgreSQL (using service role key)
- **Authentication:** No Supabase Auth yet (planned for future)
- **Authorization:** Backend-level checks via header-based user verification

## Implementation Details

### Authorization Module

Created `backend/authorization.py` with three main functions:

1. **`verify_user_access()`** - Verifies that `current_user_id` matches `requested_user_id`
2. **`get_current_user_id()`** - FastAPI dependency to extract user ID from `X-Current-User-Id` header
3. **`verify_slot_ownership()`** - Verifies slot ownership and returns the slot's user_id

### Header-Based User Identification

The system uses the `X-Current-User-Id` HTTP header to identify the authenticated user:

```http
GET /api/users/{user_id}/slots
X-Current-User-Id: abc123-def456-ghi789
```

### Backward Compatibility

All authorization checks use `allow_if_none=True` by default, meaning:
- If the header is **not provided**, access is allowed (backward compatible)
- If the header **is provided**, it must match the requested `user_id` or access is denied

This allows gradual migration:
1. **Phase 1 (Current):** Header optional, no breaking changes
2. **Phase 2 (Future):** Frontend sends header, backend enforces
3. **Phase 3 (Future):** Make header required, remove `allow_if_none`

## Protected Endpoints

All user-scoped endpoints now include authorization checks:

### User Management
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile
- `PUT /api/users/{user_id}/base-path` - Update base path
- `DELETE /api/users/{user_id}` - Delete user

### Class Slots
- `POST /api/users/{user_id}/slots` - Create slot
- `GET /api/users/{user_id}/slots` - Get user's slots
- `PUT /api/slots/{slot_id}` - Update slot (verifies ownership)
- `DELETE /api/slots/{slot_id}` - Delete slot (verifies ownership)

### Weekly Plans
- `GET /api/users/{user_id}/plans` - Get user's plans
- `POST /api/process-week` - Process week (verifies user_id in request body)

### Other
- `GET /api/recent-weeks?user_id={user_id}` - Get recent weeks

## Usage Examples

### Frontend (Tauri/React)

When making API calls, include the current user ID in headers:

```typescript
// In your API client
const userId = getCurrentUserId(); // From your user selector/store

fetch(`http://localhost:8000/api/users/${userId}/slots`, {
  headers: {
    'X-Current-User-Id': userId,
    'Content-Type': 'application/json',
  },
});
```

### Testing Authorization

Test that authorization works:

```bash
# Should succeed (matching user IDs)
curl -H "X-Current-User-Id: user-123" \
     http://localhost:8000/api/users/user-123/slots

# Should fail with 403 (mismatched user IDs)
curl -H "X-Current-User-Id: user-456" \
     http://localhost:8000/api/users/user-123/slots

# Should succeed (no header = backward compatible)
curl http://localhost:8000/api/users/user-123/slots
```

## Security Considerations

### Current Protection Level: **Medium**

✅ **What's Protected:**
- Backend verifies user access before database operations
- Prevents unauthorized access when header is provided
- Logs authorization failures for monitoring

⚠️ **Limitations:**
- Header is optional (backward compatibility)
- No authentication token validation (header can be spoofed)
- Service role key bypasses RLS (if enabled)

### Future Enhancements

1. **Supabase Auth Integration**
   - Replace header-based auth with JWT tokens
   - Validate tokens server-side
   - Extract `auth.uid()` from JWT

2. **Enable RLS**
   - Use RLS policies in `docs/supabase_rls_policies.sql`
   - Switch from service_role to anon key for client requests
   - Remove service_role key from client-side code

3. **Make Authorization Required**
   - Change `allow_if_none=False` in all endpoints
   - Require authentication token for all requests
   - Return 401 Unauthorized if no token provided

## RLS Policies (Future Use)

RLS policies are prepared in `docs/supabase_rls_policies.sql` but **not enabled** because:

1. Service role key bypasses RLS
2. No Supabase Auth integration yet
3. Desktop app doesn't require RLS at this time

**When to enable RLS:**
- When migrating to web/multi-user cloud architecture
- When implementing Supabase Auth
- When removing service_role key from client-side code

## Monitoring & Logging

Authorization events are logged:

```python
# Successful authorization
logger.debug("authorization_granted", extra={"user_id": user_id})

# Skipped (no header)
logger.warning("authorization_skipped", extra={"reason": "no_current_user_id"})

# Denied (mismatch)
logger.warning("authorization_denied", extra={
    "current_user_id": current_user_id,
    "requested_user_id": requested_user_id,
})
```

Monitor these logs to:
- Track authorization failures
- Identify potential security issues
- Plan migration to required authentication

## Migration Path

### Step 1: Update Frontend (Current)
- Add `X-Current-User-Id` header to all API calls
- Test that authorization works
- Monitor logs for any issues

### Step 2: Make Header Required (Future)
- Change `allow_if_none=False` in `backend/authorization.py`
- Update all endpoints to require header
- Frontend must send header or get 403

### Step 3: Add Supabase Auth (Future)
- Integrate Supabase Auth SDK
- Replace header with JWT token
- Validate tokens server-side
- Extract user ID from JWT claims

### Step 4: Enable RLS (Future)
- Uncomment RLS policies in `docs/supabase_rls_policies.sql`
- Switch to anon key for client requests
- Remove service_role key from client code
- Test that RLS policies work correctly

## Testing Checklist

- [x] Authorization module created
- [x] All user-scoped endpoints protected
- [x] Backward compatible (header optional)
- [x] Logging implemented
- [ ] Frontend updated to send header
- [ ] Integration tests added
- [ ] Authorization failure tests added

## Related Files

- `backend/authorization.py` - Authorization helpers
- `backend/api.py` - API endpoints (updated with authorization)
- `docs/supabase_rls_policies.sql` - RLS policies (future use)
- `docs/security/ACTUAL_USER_CONFIGURATIONS.md` - User configuration details

---

**Next Steps:**
1. Update frontend to send `X-Current-User-Id` header
2. Test authorization with real requests
3. Monitor logs for authorization events
4. Plan Supabase Auth integration (if moving to web)

