# Production Rollout Playbook

**Date:** January 2025  
**Purpose:** Step-by-step guide for deploying security-hardened backend to production

---

## Pre-Deployment Checklist

### 1. Code Verification ✅

- [x] All security hardening complete
- [x] Authorization module tested
- [x] Rate limiting implemented
- [x] Integration tests passing
- [x] Unit tests passing
- [ ] Code review completed
- [ ] Security review completed

### 2. Dependencies

```bash
# Verify all dependencies are installed
pip install -r requirements.txt

# Key dependencies for security features:
# - slowapi==0.1.9 (rate limiting)
# - fastapi (API framework)
# - pytest (testing)
```

### 3. Environment Variables

Verify these are set in production:

```bash
# Database
DATABASE_URL=sqlite:///./data/lesson_planner.db  # or Supabase URL

# Supabase (if using)
USE_SUPABASE=True
SUPABASE_PROJECT=project1
SUPABASE_URL_PROJECT1=https://your-project.supabase.co
SUPABASE_KEY_PROJECT1=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY_PROJECT1=your-service-role-key-here  # Server-side only!

# Server
HOST=127.0.0.1  # or 0.0.0.0 for external access
PORT=8000
```

**⚠️ CRITICAL:** Ensure `SUPABASE_SERVICE_ROLE_KEY` is:
- ✅ Only in backend environment variables
- ✅ Never in frontend code
- ✅ Never in git history
- ✅ Only accessible to server processes

---

## Phase 1: Database Migration

### Step 1.1: Backup Production Database

```bash
# SQLite backup
cp data/lesson_planner.db data/lesson_planner.db.backup.$(date +%Y%m%d_%H%M%S)

# Supabase backup (via dashboard or CLI)
# Use Supabase dashboard → Database → Backups
```

### Step 1.2: Verify Schema

```bash
# Check current schema
python -c "
from backend.database import SQLiteDatabase
db = SQLiteDatabase()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT sql FROM sqlite_master WHERE type=\"table\"')
    for row in cursor.fetchall():
        print(row[0])
"
```

### Step 1.3: Run Migrations (if needed)

```bash
# Migrations run automatically on init_db()
# Verify migrations completed:
python -c "
from backend.database import SQLiteDatabase
db = SQLiteDatabase()
print('Schema verified')
"
```

### Step 1.4: Verify Indices

```sql
-- Check indices exist (for RLS performance)
SELECT name, tbl_name FROM sqlite_master WHERE type='index';

-- Should see:
-- idx_class_slots_user_id
-- idx_weekly_plans_user_id
-- idx_performance_metrics_plan_id
```

---

## Phase 2: Backend Deployment

### Step 2.1: Deploy Code

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "import slowapi; print('Rate limiting ready')"
python -c "from backend.authorization import verify_user_access; print('Authorization ready')"
```

### Step 2.2: Start Backend

```bash
# Development
python -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000

# Production (with gunicorn)
gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 2.3: Verify Health

```bash
# Health check
curl http://localhost:8000/api/health

# Database health
curl http://localhost:8000/api/health/database

# Expected response:
# {"status": "healthy", "version": "1.0.0", ...}
```

### Step 2.4: Test Authorization

```bash
# Test valid authorization
curl -H "X-Current-User-Id: test-user-123" \
     http://localhost:8000/api/users/test-user-123/slots

# Test rate limiting (should get 429 after 30 requests)
for i in {1..35}; do
  curl -H "X-Current-User-Id: test-user-123" \
       http://localhost:8000/api/users/test-user-123/slots
done
```

---

## Phase 3: Frontend Deployment

### Step 3.1: Build Frontend

```bash
cd frontend
npm install
npm run build
```

### Step 3.2: Verify Authorization Header

```bash
# Check built files include authorization header support
grep -r "X-Current-User-Id" frontend/dist/
```

### Step 3.3: Deploy Frontend

```bash
# Tauri build
npm run tauri build

# Or web deployment
# Copy dist/ to web server
```

### Step 3.4: Test End-to-End

1. Open frontend application
2. Select a user
3. Check browser network tab
4. Verify `X-Current-User-Id` header is sent
5. Verify API calls succeed

---

## Phase 4: Monitoring Setup

### Step 4.1: Configure Log Forwarding

```bash
# Example: Forward logs to central system
# Adjust based on your logging infrastructure

# Log files location
tail -f logs/json_pipeline.log

# Monitor authorization failures
grep "authorization_denied" logs/json_pipeline.log

# Monitor rate limit violations
grep "rate_limit_exceeded" logs/json_pipeline.log
```

### Step 4.2: Set Up Alerts

**Authorization Failures:**
- Alert if > 10 failures/minute
- Alert if > 50 failures/hour
- Alert on SQL injection attempts

**Rate Limit Violations:**
- Alert if > 20 violations/minute
- Alert on sustained violations from single IP

**Example Alert Rules:**
```yaml
# Example Prometheus alert rules
groups:
  - name: authorization_alerts
    rules:
      - alert: HighAuthorizationFailures
        expr: rate(authorization_failures_total[5m]) > 10
        annotations:
          summary: "High rate of authorization failures detected"
      
      - alert: RateLimitViolations
        expr: rate(rate_limit_exceeded_total[5m]) > 20
        annotations:
          summary: "High rate of rate limit violations"
```

### Step 4.3: Monitor Key Metrics

**Dashboard Metrics:**
- Authorization success/failure rate
- Rate limit violations per endpoint
- API request volume
- Response times
- Error rates

---

## Phase 5: RLS Enablement (Future - When Supabase Auth Added)

### Step 5.1: Prerequisites

- [ ] Supabase Auth integrated
- [ ] Frontend sends JWT tokens
- [ ] Backend validates JWT tokens
- [ ] Using anon key for client requests (not service_role)
- [ ] Staging environment ready

### Step 5.2: Enable RLS in Staging

```sql
-- 1. Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;

-- 2. Create policies (from docs/supabase_rls_policies.sql)
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT TO authenticated
    USING (auth.uid()::text = id);

CREATE POLICY "class_slots_select_own" ON public.class_slots
    FOR SELECT TO authenticated
    USING (auth.uid()::text = user_id);

-- ... (see docs/supabase_rls_policies.sql for all policies)

-- 3. Verify indices exist
CREATE INDEX IF NOT EXISTS idx_users_id ON public.users(id);
CREATE INDEX IF NOT EXISTS idx_class_slots_user_id ON public.class_slots(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON public.weekly_plans(user_id);
```

### Step 5.3: Test RLS in Staging

```bash
# Run integration tests
pytest tests/test_integration_authorization.py -v

# Test with real JWT tokens
curl -H "Authorization: Bearer $JWT_TOKEN" \
     https://staging-api.example.com/api/users/{user_id}/slots

# Verify users can only access their own data
# Verify users cannot access other users' data
```

### Step 5.4: Monitor Staging

- Monitor for 403 errors (should only be unauthorized access)
- Monitor for performance impact
- Verify all endpoints work correctly
- Run load tests

### Step 5.5: Enable RLS in Production

**Only after successful staging validation:**

```sql
-- Same steps as staging
-- Enable RLS
-- Create policies
-- Verify indices
```

**Monitor closely for 24-48 hours:**
- Watch for authorization errors
- Monitor performance
- Check user reports
- Be ready to rollback

---

## Rollback Procedures

### Rollback: Authorization Issues

**If authorization is blocking legitimate users:**

1. **Temporary fix:** Set `allow_if_none=True` in authorization checks
2. **Investigate:** Check logs for authorization failures
3. **Fix:** Correct authorization logic
4. **Redeploy:** Deploy fix

**Code change:**
```python
# In backend/authorization.py
verify_user_access(user_id, current_user_id, allow_if_none=True)  # Temporarily allow
```

### Rollback: Rate Limiting Too Strict

**If rate limits are blocking legitimate users:**

1. **Increase limits temporarily:**
```python
# In backend/rate_limiter.py
AUTH_LIMIT = "100/minute"  # Increase from 30
```

2. **Redeploy**
3. **Monitor usage**
4. **Adjust to appropriate level**

### Rollback: RLS Issues

**If RLS is blocking legitimate access:**

1. **Disable RLS temporarily:**
```sql
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_slots DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics DISABLE ROW LEVEL SECURITY;
```

2. **Investigate policy issues**
3. **Fix policies**
4. **Re-enable RLS**

### Rollback: Database Issues

**If database migration fails:**

1. **Restore backup:**
```bash
cp data/lesson_planner.db.backup.YYYYMMDD_HHMMSS data/lesson_planner.db
```

2. **Revert code to previous version**
3. **Investigate migration issue**
4. **Fix and retry**

---

## Post-Deployment Verification

### Day 1 Checks

- [ ] All endpoints responding
- [ ] Authorization working correctly
- [ ] Rate limiting active
- [ ] No authorization failures for legitimate users
- [ ] Logs being collected
- [ ] Alerts configured

### Week 1 Monitoring

- [ ] Monitor authorization failure rates
- [ ] Monitor rate limit violations
- [ ] Review logs for security issues
- [ ] Adjust rate limits if needed
- [ ] User feedback collected

### Month 1 Review

- [ ] Security metrics reviewed
- [ ] Rate limits adjusted based on usage
- [ ] Authorization patterns analyzed
- [ ] Documentation updated
- [ ] Team trained on new security features

---

## Troubleshooting

### Issue: Authorization Always Failing

**Symptoms:** All requests return 403

**Diagnosis:**
```bash
# Check logs
grep "authorization_denied" logs/json_pipeline.log

# Check header format
curl -v -H "X-Current-User-Id: user-123" \
     http://localhost:8000/api/users/user-123/slots
```

**Solutions:**
1. Verify header is being sent correctly
2. Check user ID format matches validation
3. Verify authorization logic

### Issue: Rate Limits Too Strict

**Symptoms:** Legitimate users hitting 429 errors

**Diagnosis:**
```bash
# Check rate limit violations
grep "rate_limit_exceeded" logs/json_pipeline.log | wc -l
```

**Solutions:**
1. Increase limits temporarily
2. Monitor actual usage patterns
3. Adjust limits based on data

### Issue: Performance Degradation

**Symptoms:** Slow API responses

**Diagnosis:**
- Check database query performance
- Check rate limiting overhead
- Check authorization check overhead

**Solutions:**
1. Add database indices
2. Optimize authorization checks
3. Consider caching

---

## Emergency Contacts

**On-Call Engineer:** [Contact Info]  
**Security Team:** [Contact Info]  
**Database Admin:** [Contact Info]

---

## Success Criteria

✅ **Deployment Successful If:**
- All endpoints responding correctly
- Authorization working as expected
- Rate limiting active and appropriate
- No legitimate users blocked
- Logs being collected
- Monitoring active
- Team trained

---

## Related Documents

- `docs/security/AUTHORIZATION_IMPLEMENTATION.md` - Authorization guide
- `docs/security/RATE_LIMITING.md` - Rate limiting guide
- `docs/security/RLS_AUTHORIZATION_DECISION.md` - RLS rationale
- `docs/supabase_rls_policies.sql` - RLS policies
- `tests/README_AUTHORIZATION_TESTS.md` - Test documentation

---

**Last Updated:** January 2025  
**Status:** Ready for Production Deployment ✅

