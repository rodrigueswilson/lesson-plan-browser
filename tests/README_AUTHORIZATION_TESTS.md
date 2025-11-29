# Authorization Integration Tests

**File:** `tests/test_integration_authorization.py`  
**Purpose:** Verify authorization checks work correctly for all user-scoped API endpoints

---

## Test Coverage

### Test Matrix

| Scenario | Header | Expected Status | Test Count |
|----------|--------|----------------|------------|
| Valid header | `X-Current-User-Id: user_a` | 200 OK | ✅ 8 tests |
| Mismatched header | `X-Current-User-Id: user_b` (but path uses `user_a`) | 403 Forbidden | ✅ 8 tests |
| Missing header | No header | 200 OK (backward compat) | ✅ 8 tests |
| Invalid format | `X-Current-User-Id: user@123` | 400 Bad Request | ✅ 6 tests |

### Endpoints Tested

- ✅ `GET /api/users/{user_id}/slots` - List slots
- ✅ `POST /api/users/{user_id}/slots` - Create slot
- ✅ `PUT /api/slots/{slot_id}` - Update slot
- ✅ `DELETE /api/slots/{slot_id}` - Delete slot
- ✅ `GET /api/users/{user_id}` - Get user
- ✅ `PUT /api/users/{user_id}` - Update user
- ✅ `GET /api/users/{user_id}/plans` - List plans
- ✅ `POST /api/process-week` - Process week
- ✅ `GET /api/recent-weeks` - Get recent weeks

### Edge Cases Tested

- ✅ Empty header value
- ✅ SQL injection attempts (`user'; DROP TABLE users; --`)
- ✅ Unicode characters (`user-测试-123`)
- ✅ Very long IDs (300+ characters)
- ✅ Special characters (`.`, ` `, `/`, `\`)
- ✅ Nonexistent user IDs (should return 404, not 403)

---

## Running Tests

### Run All Authorization Tests

```bash
pytest tests/test_integration_authorization.py -v
```

### Run Specific Test Class

```bash
# Test user slots authorization
pytest tests/test_integration_authorization.py::TestUserSlotsAuthorization -v

# Test user management authorization
pytest tests/test_integration_authorization.py::TestUserManagementAuthorization -v

# Test weekly plans authorization
pytest tests/test_integration_authorization.py::TestWeeklyPlansAuthorization -v

# Test edge cases
pytest tests/test_integration_authorization.py::TestEdgeCases -v
```

### Run with Markers

```bash
# Run only integration tests
pytest -m integration tests/test_integration_authorization.py -v
```

### Run with Coverage

```bash
pytest tests/test_integration_authorization.py --cov=backend.authorization --cov-report=html -v
```

---

## Test Fixtures

### Database Fixtures

- `test_db_path` - Temporary SQLite database file
- `test_settings` - Test configuration
- `test_db` - Initialized test database
- `test_client` - FastAPI TestClient with test database

### Data Fixtures

- `user_a` - Test user A (`test-user-a-123`)
- `user_b` - Test user B (`test-user-b-456`)
- `slot_a` - Test slot owned by user A

---

## Test Structure

```
tests/test_integration_authorization.py
├── TestUserSlotsAuthorization
│   ├── test_list_slots_valid_header
│   ├── test_list_slots_mismatched_header
│   ├── test_list_slots_missing_header
│   ├── test_create_slot_valid_header
│   ├── test_update_slot_valid_header
│   └── test_delete_slot_valid_header
├── TestUserManagementAuthorization
│   ├── test_get_user_valid_header
│   ├── test_update_user_valid_header
│   └── ...
├── TestWeeklyPlansAuthorization
│   ├── test_list_plans_valid_header
│   ├── test_process_week_valid_header
│   └── ...
├── TestRecentWeeksAuthorization
│   └── ...
└── TestEdgeCases
    ├── test_unicode_header
    ├── test_very_long_header
    ├── test_sql_injection_header
    └── ...
```

---

## Expected Test Results

### All Tests Passing

```
tests/test_integration_authorization.py::TestUserSlotsAuthorization::test_list_slots_valid_header PASSED
tests/test_integration_authorization.py::TestUserSlotsAuthorization::test_list_slots_mismatched_header PASSED
tests/test_integration_authorization.py::TestUserSlotsAuthorization::test_list_slots_missing_header PASSED
...
```

### Test Count

- **Total Tests:** ~40+ tests
- **Test Classes:** 5 classes
- **Coverage:** All user-scoped endpoints

---

## CI Integration

### GitHub Actions Example

```yaml
name: Authorization Tests

on:
  pull_request:
    paths:
      - 'backend/authorization.py'
      - 'backend/api.py'
      - 'tests/test_integration_authorization.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/test_integration_authorization.py -v --cov=backend.authorization
```

### Required for Deployment

Mark these tests as required in your CI/CD pipeline when:
- Authorization code is modified
- API endpoints are changed
- Security policies are updated

---

## Troubleshooting

### Test Failures

**Issue:** Tests fail with "database locked"  
**Solution:** Ensure tests use separate database files (fixtures handle this)

**Issue:** Tests fail with "module not found"  
**Solution:** Run from project root: `pytest tests/test_integration_authorization.py`

**Issue:** Authorization checks not working  
**Solution:** Verify `backend/authorization.py` is imported correctly in `backend/api.py`

### Debugging

Run with verbose output:
```bash
pytest tests/test_integration_authorization.py -v -s
```

Run single test:
```bash
pytest tests/test_integration_authorization.py::TestUserSlotsAuthorization::test_list_slots_valid_header -v -s
```

---

## Adding New Tests

### Template for New Endpoint Test

```python
def test_new_endpoint_valid_header(self, test_client, user_a):
    """Valid header should return 200 OK."""
    response = test_client.get(
        f"/api/users/{user_a}/new-endpoint",
        headers={"X-Current-User-Id": user_a}
    )
    assert response.status_code == 200

def test_new_endpoint_mismatched_header(self, test_client, user_a, user_b):
    """Mismatched header should return 403 Forbidden."""
    response = test_client.get(
        f"/api/users/{user_a}/new-endpoint",
        headers={"X-Current-User-Id": user_b}
    )
    assert response.status_code == 403

def test_new_endpoint_missing_header(self, test_client, user_a):
    """Missing header should return 200 OK (backward compatible)."""
    response = test_client.get(
        f"/api/users/{user_a}/new-endpoint"
        # No header
    )
    assert response.status_code == 200
```

---

## Related Files

- `backend/authorization.py` - Authorization module being tested
- `backend/api.py` - API endpoints being tested
- `tests/test_authorization.py` - Unit tests for authorization module
- `docs/security/AUTHORIZATION_IMPLEMENTATION.md` - Implementation guide

---

**Last Updated:** January 2025  
**Test Status:** ✅ All tests passing

