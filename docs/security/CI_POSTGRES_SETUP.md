# CI Integration Tests with Postgres

**Date:** January 2025  
**Purpose:** Guide for running integration tests against Postgres test container in CI

---

## Overview

The GitHub Actions workflow (`.github/workflows/ci-integration-tests.yml`) runs integration tests against a Postgres test container to provide a more production-like testing environment than SQLite.

---

## Workflow Structure

### Two Test Jobs

1. **`integration-tests-postgres`** - Tests against Postgres 15 container
2. **`integration-tests-sqlite`** - Tests against SQLite (fallback/compatibility)

Both jobs run in parallel to ensure:
- Tests work with production-like database (Postgres)
- Tests remain compatible with SQLite (current default)

---

## Postgres Test Container Setup

### Container Configuration

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: test_lesson_planner
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - 5432:5432
```

### Schema Creation

The workflow automatically creates the database schema:

- `users` table
- `class_slots` table
- `weekly_plans` table
- `performance_metrics` table
- Required indices for RLS performance

---

## Running Tests Locally with Postgres

### Option 1: Docker Compose (Recommended)

Create `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: test_lesson_planner
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"  # Use different port to avoid conflicts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Run tests:

```bash
# Start Postgres
docker-compose -f docker-compose.test.yml up -d

# Wait for Postgres
until pg_isready -h localhost -p 5433 -U test_user; do sleep 2; done

# Run tests
DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_lesson_planner" \
USE_SUPABASE=False \
pytest tests/test_integration_authorization.py -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Option 2: Local Postgres Instance

```bash
# Create test database
createdb test_lesson_planner

# Set environment variables
export DATABASE_URL="postgresql://localhost/test_lesson_planner"
export USE_SUPABASE=False

# Run tests
pytest tests/test_integration_authorization.py -v
```

---

## Using Postgres Test Fixtures

### Current Status

Tests currently use SQLite fixtures (`tests/test_integration_authorization.py`). To use Postgres:

1. **Use Postgres fixtures** (when available):
   ```python
   # In test file, import Postgres fixtures
   from tests.conftest_postgres import (
       postgres_test_client,
       postgres_user_a,
       postgres_user_b
   )
   
   def test_authorization_with_postgres(postgres_test_client, postgres_user_a):
       response = postgres_test_client.get(
           f"/api/users/{postgres_user_a}/slots",
           headers={"X-Current-User-Id": postgres_user_a}
       )
       assert response.status_code == 200
   ```

2. **Mark tests for Postgres**:
   ```python
   import pytest
   
   @pytest.mark.postgres
   def test_with_postgres(postgres_test_client):
       # Test code
       pass
   ```

3. **Run Postgres-specific tests**:
   ```bash
   pytest -m postgres tests/test_integration_authorization.py
   ```

---

## Benefits of Postgres Testing

### Production Parity

- **Same database engine** as production (Supabase uses Postgres)
- **Same SQL dialect** and features
- **Same constraints** and foreign keys
- **Same performance characteristics**

### RLS Testing

When RLS is enabled, Postgres tests can verify:
- RLS policies work correctly
- User isolation enforced at database level
- Performance impact of RLS policies

### Migration Testing

- Test database migrations against Postgres
- Verify schema changes work correctly
- Catch Postgres-specific issues early

---

## CI Workflow Triggers

The workflow runs on:

- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop`
- **File changes** in:
  - `backend/**`
  - `tests/**`
  - `requirements.txt`
  - `.github/workflows/ci-integration-tests.yml`

---

## Troubleshooting

### Postgres Container Not Ready

**Error:** `connection refused` or `timeout`

**Solution:**
```yaml
# Add health check wait step
- name: Wait for Postgres
  run: |
    until pg_isready -h localhost -p 5432 -U ${{ env.POSTGRES_USER }}; do
      echo "Waiting for Postgres..."
      sleep 2
    done
```

### Schema Creation Fails

**Error:** `relation already exists`

**Solution:** Use `CREATE TABLE IF NOT EXISTS` (already implemented)

### Test Fixtures Not Found

**Error:** `fixture 'postgres_test_client' not found`

**Solution:** Ensure `tests/conftest_postgres.py` is imported or add to `pytest.ini`:
```ini
[pytest]
python_files = conftest.py conftest_postgres.py test_*.py
```

---

## Future Enhancements

### Planned Improvements

1. **Full Postgres Fixture Support**
   - Complete `PostgresTestDatabase` implementation
   - All `DatabaseInterface` methods implemented
   - Seamless switching between SQLite and Postgres

2. **RLS Policy Testing**
   - Test RLS policies in CI
   - Verify user isolation
   - Performance benchmarks

3. **Migration Testing**
   - Test migrations against Postgres
   - Verify rollback procedures
   - Schema versioning tests

4. **Performance Testing**
   - Query performance benchmarks
   - Index effectiveness tests
   - Connection pool testing

---

## Related Documents

- `.github/workflows/ci-integration-tests.yml` - CI workflow definition
- `tests/test_integration_authorization.py` - Integration tests
- `tests/conftest_postgres.py` - Postgres test fixtures
- `docs/security/PRODUCTION_ROLLOUT_PLAYBOOK.md` - Deployment guide

---

**Last Updated:** January 2025  
**Status:** CI Ready ✅

