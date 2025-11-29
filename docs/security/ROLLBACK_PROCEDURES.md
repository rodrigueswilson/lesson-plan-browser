# Rollback Procedures

**Date:** January 2025  
**Purpose:** Quick reference for rolling back security features if issues arise

---

## Quick Rollback Reference

### Authorization Issues

**Symptom:** Legitimate users getting 403 Forbidden

**Quick Fix:**
```python
# In backend/authorization.py
# Temporarily allow requests without header
verify_user_access(user_id, current_user_id, allow_if_none=True)
```

**Full Rollback:**
```python
# Comment out authorization checks in backend/api.py
# @app.get("/api/users/{user_id}/slots")
# @rate_limit_auth
async def get_user_slots(...):
    # verify_user_access(user_id, current_user_id)  # Commented out
    ...
```

### Rate Limiting Too Strict

**Symptom:** Users hitting 429 Too Many Requests

**Quick Fix:**
```python
# In backend/rate_limiter.py
AUTH_LIMIT = "100/minute"  # Increase from 30
GENERAL_LIMIT = "200/minute"  # Increase from 100
```

**Full Rollback:**
```python
# In backend/api.py
# Comment out rate limit decorators
# @rate_limit_auth
async def endpoint(...):
    ...
```

**Or disable rate limiting entirely:**
```python
# In backend/api.py
# Comment out setup
# setup_rate_limiting(app)
```

### RLS Blocking Access

**Symptom:** Users can't access their own data after enabling RLS

**Quick Fix:**
```sql
-- Disable RLS temporarily
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_slots DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics DISABLE ROW LEVEL SECURITY;
```

**Full Rollback:**
```sql
-- Drop all policies
DROP POLICY IF EXISTS "users_select_own" ON public.users;
DROP POLICY IF EXISTS "class_slots_select_own" ON public.class_slots;
-- ... (drop all policies)

-- Disable RLS
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
-- ... (disable on all tables)
```

### Database Migration Issues

**Symptom:** Database errors after migration

**Quick Fix:**
```bash
# Restore from backup
cp data/lesson_planner.db.backup.YYYYMMDD_HHMMSS data/lesson_planner.db
```

**Full Rollback:**
1. Restore database backup
2. Revert code to previous version
3. Restart backend

---

## Rollback Decision Tree

```
Issue Detected?
├─ Authorization failures?
│  ├─ Legitimate users blocked? → Quick Fix: allow_if_none=True
│  └─ All requests failing? → Full Rollback: Comment out checks
│
├─ Rate limit violations?
│  ├─ Legitimate users blocked? → Quick Fix: Increase limits
│  └─ System overloaded? → Full Rollback: Disable rate limiting
│
├─ RLS blocking access?
│  ├─ Some users blocked? → Quick Fix: Disable RLS temporarily
│  └─ All users blocked? → Full Rollback: Drop policies + disable RLS
│
└─ Database errors?
   └─ Migration failed? → Full Rollback: Restore backup + revert code
```

---

## Emergency Contacts

**On-Call:** [Contact]  
**Security:** [Contact]  
**Database:** [Contact]

---

**Last Updated:** January 2025

