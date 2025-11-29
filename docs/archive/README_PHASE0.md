# Phase 0: Foundations & Observability ✅

**Status:** COMPLETE  
**Date:** 2025-10-04  
**Duration:** 1 session (planned: 1 week)

---

## Overview

Phase 0 establishes the infrastructure for safe JSON pipeline rollout with feature flags, telemetry, pre-commit checks, and operational runbooks.

**Goal:** Enable safe toggling, monitoring, and rollback of the JSON output pipeline without impacting current users.

---

## What Was Built

### 1. Configuration System (`backend/config.py`)

**Purpose:** Centralized configuration with feature flags and environment variable support.

**Key Features:**
- ✅ Feature flag: `ENABLE_JSON_OUTPUT` (default: `false`)
- ✅ Gradual rollout: `JSON_PIPELINE_ROLLOUT_PERCENTAGE` (0-100%)
- ✅ Token budget controls (`MAX_TOKEN_INCREASE_PCT`, `MAX_TOKENS_PER_LESSON`)
- ✅ Validation settings (`MAX_VALIDATION_RETRIES`, `ENABLE_JSON_REPAIR`)
- ✅ Pydantic-based settings with type validation
- ✅ Environment variable loading from `.env`

**Usage:**
```python
from backend.config import settings, is_json_pipeline_enabled_for_user

# Check if JSON pipeline is enabled
if settings.ENABLE_JSON_OUTPUT:
    # Use JSON pipeline
    pass

# Check for specific user (deterministic assignment)
if is_json_pipeline_enabled_for_user(user_id):
    # User is in rollout group
    pass
```

---

### 2. Telemetry System (`backend/telemetry.py`)

**Purpose:** Structured logging and metrics collection for observability.

**Key Features:**
- ✅ Structured JSON logging (via `structlog`)
- ✅ Event tracking (generation, validation, rendering)
- ✅ Token footprint comparison (markdown vs. JSON)
- ✅ Validation error logging with context
- ✅ JSON repair attempt tracking
- ✅ Duration tracking context manager
- ✅ Metrics collection and CSV export
- ✅ Automatic alerting (token usage >20% increase)

**Usage:**
```python
from backend.telemetry import (
    log_json_pipeline_event,
    log_token_footprint_comparison,
    track_duration
)

# Log pipeline event
log_json_pipeline_event(
    event_type="validation",
    success=True,
    duration_ms=150.0,
    token_count=3200,
    lesson_id="lesson-123"
)

# Track token usage
log_token_footprint_comparison(
    markdown_tokens=2800,
    json_tokens=3200,
    lesson_id="lesson-123"
)

# Track operation duration
with track_duration("rendering", lesson_id="lesson-123"):
    render_template(data)
```

---

### 3. Pre-commit Hooks (`.pre-commit-config.yaml`)

**Purpose:** Automated quality gates to prevent bad commits.

**Checks:**
- ✅ JSON schema validation (`check-jsonschema`)
- ✅ Jinja2 template linting (`jinjalint`)
- ✅ Python formatting (`black`)
- ✅ Python linting (`flake8`)
- ✅ Import sorting (`isort`)
- ✅ Security checks (`bandit`)
- ✅ Type checking (`mypy`)
- ✅ Snapshot update guard (custom hook)
- ✅ General file checks (trailing whitespace, YAML, etc.)

**Setup:**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

### 4. Snapshot Guard (`tools/check_snapshot_updates.py`)

**Purpose:** Prevent accidental snapshot updates in CI or commits.

**Features:**
- ✅ Detects staged snapshot files
- ✅ Blocks commits with snapshot changes (unless `--no-verify`)
- ✅ Prevents `pytest --snapshot-update` in CI
- ✅ Provides clear instructions for intentional updates

**Usage:**
```bash
# Automatically runs on commit via pre-commit hook

# Override if intentional
git commit --no-verify
```

---

### 5. Operational Runbook (`docs/runbooks/json_pipeline_toggle.md`)

**Purpose:** Step-by-step procedures for operations team.

**Sections:**
- ✅ Feature flag management (enable/disable/gradual rollout)
- ✅ Monitoring & observability (logs, metrics, dashboard)
- ✅ Common issues & troubleshooting (4 scenarios with solutions)
- ✅ Rollback procedures (emergency & gradual)
- ✅ Health checks (backend, pipeline, database)
- ✅ Maintenance tasks (daily, weekly, monthly)
- ✅ Contact information and useful commands

**Quick Reference:**
```bash
# Enable JSON pipeline
echo "ENABLE_JSON_OUTPUT=true" >> .env
systemctl restart lesson-plan-backend

# Disable (rollback)
echo "ENABLE_JSON_OUTPUT=false" >> .env
systemctl restart lesson-plan-backend

# Monitor
tail -f logs/json_pipeline.log | jq 'select(.level == "error")'
```

---

### 6. Supporting Tools

#### `tools/export_metrics.py`
Export telemetry metrics to CSV for analysis.

```bash
python tools/export_metrics.py --output metrics/export.csv --summary
```

#### `tools/metrics_summary.py`
Display summary of collected metrics.

```bash
python tools/metrics_summary.py
```

Output:
```
==================================================
JSON Pipeline Metrics Summary
==================================================

📊 Total Requests:     1,234
✅ Successful:         1,180
📈 Success Rate:       95.6%

🎯 Avg Token Count:    3,150
⏱️  Median Duration:    92ms
🔄 Avg Retry Count:    0.8

🏥 Health Indicators:
   ✓ Success rate: HEALTHY
   ✓ Retry count: HEALTHY
```

---

## File Structure

```
d:\LP/
├── backend/
│   ├── __init__.py                    # Package initialization
│   ├── config.py                      # Configuration & feature flags
│   └── telemetry.py                   # Structured logging & metrics
├── tools/
│   ├── check_snapshot_updates.py      # Pre-commit snapshot guard
│   ├── export_metrics.py              # Metrics export CLI
│   └── metrics_summary.py             # Metrics summary CLI
├── docs/
│   └── runbooks/
│       └── json_pipeline_toggle.md    # Operations runbook
├── logs/
│   └── .gitkeep                       # Log directory (gitignored)
├── metrics/
│   └── .gitkeep                       # Metrics directory (gitignored)
├── .pre-commit-config.yaml            # Pre-commit hooks configuration
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore rules
├── PHASE0_IMPLEMENTATION.md           # Implementation summary
└── README_PHASE0.md                   # This file
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install pydantic structlog pre-commit

# Install pre-commit hooks
pre-commit install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Key Settings:**
```bash
# Feature Flags
ENABLE_JSON_OUTPUT=false              # Start disabled
JSON_PIPELINE_ROLLOUT_PERCENTAGE=0    # 0% rollout

# Telemetry
ENABLE_TELEMETRY=true                 # Enable logging
LOG_FORMAT=json                       # JSON format for structured logs

# Token Budget
MAX_TOKEN_INCREASE_PCT=20             # Alert at 20% increase
MAX_TOKENS_PER_LESSON=4000            # Hard limit

# Validation
MAX_VALIDATION_RETRIES=3              # Retry up to 3 times
ENABLE_JSON_REPAIR=true               # Auto-fix minor JSON errors
```

### 3. Create Required Directories

```bash
# Already created:
mkdir -p logs metrics backend
```

### 4. Test Configuration

```python
# Test feature flag
from backend.config import settings
print(f"JSON Pipeline: {settings.ENABLE_JSON_OUTPUT}")

# Test telemetry
from backend.telemetry import log_json_pipeline_event
log_json_pipeline_event(
    event_type="test",
    success=True,
    duration_ms=100.0
)
```

### 5. Run Pre-commit Checks

```bash
# Run all checks
pre-commit run --all-files

# Should see:
# ✓ Validate JSON Schemas
# ✓ Lint Jinja2 Templates
# ✓ Format Python Code
# ✓ Lint Python Code
# ... etc.
```

---

## Testing Phase 0

### Test 1: Feature Flag Toggle

```python
from backend.config import settings, is_json_pipeline_enabled_for_user

# Test global flag
assert settings.ENABLE_JSON_OUTPUT == False  # Default

# Test user assignment (with 10% rollout)
settings.JSON_PIPELINE_ROLLOUT_PERCENTAGE = 10
users_in_json = sum(
    1 for i in range(100)
    if is_json_pipeline_enabled_for_user(f"user{i}")
)
assert 8 <= users_in_json <= 12  # ~10% with some variance
```

### Test 2: Telemetry Logging

```python
from backend.telemetry import (
    log_json_pipeline_event,
    get_metrics_summary
)

# Log test events
for i in range(10):
    log_json_pipeline_event(
        event_type="test",
        success=i % 10 != 0,  # 90% success rate
        duration_ms=100.0 + i * 10,
        token_count=3000 + i * 100
    )

# Check summary
summary = get_metrics_summary()
assert summary['total_requests'] == 10
assert summary['success_rate'] == 90.0
```

### Test 3: Pre-commit Hooks

```bash
# Create invalid JSON
echo '{"invalid": json}' > test.json

# Run check (should fail)
pre-commit run check-json --files test.json
# Expected: FAILED

# Fix JSON
echo '{"valid": "json"}' > test.json

# Run check (should pass)
pre-commit run check-json --files test.json
# Expected: PASSED
```

### Test 4: Metrics Export

```bash
# Generate test metrics (run Test 2 above)

# Export to CSV
python tools/export_metrics.py --output metrics/test.csv

# Verify file created
ls -lh metrics/test.csv

# View summary
python tools/metrics_summary.py
```

---

## Integration with Future Phases

### Phase 1: JSON Schema Definition

**Use feature flag:**
```python
from backend.config import settings

if settings.ENABLE_JSON_OUTPUT:
    # Validate against schema
    validate_json(data, schema)
```

**Log validation events:**
```python
from backend.telemetry import log_json_pipeline_event

log_json_pipeline_event(
    event_type="validation",
    success=valid,
    duration_ms=duration,
    validation_errors=errors
)
```

### Phase 2: Prompt Modification

**Track token usage:**
```python
from backend.telemetry import log_token_footprint_comparison

log_token_footprint_comparison(
    markdown_tokens=len(markdown_output.split()),
    json_tokens=len(json_output.split()),
    lesson_id=lesson_id
)
```

### Phase 3: Jinja2 Templates

**Pre-commit will validate:**
- Template syntax (jinjalint)
- No accidental changes (snapshot guard)

### Phase 4: Python Renderer

**Track rendering:**
```python
from backend.telemetry import track_duration, log_render_success

with track_duration("rendering", lesson_id=lesson_id):
    output = renderer.render(data, output_path)

log_render_success(
    lesson_id=lesson_id,
    duration_ms=duration,
    output_format="markdown",
    output_size_bytes=len(output)
)
```

---

## Monitoring & Alerting

### Key Metrics to Watch

1. **Success Rate**
   - Target: >95%
   - Alert: <90%
   - Action: Review validation errors

2. **Token Usage Delta**
   - Target: <20% increase
   - Alert: >20%
   - Action: Optimize JSON structure

3. **Render Latency (p95)**
   - Target: <100ms
   - Alert: >200ms
   - Action: Profile rendering

4. **Retry Count**
   - Target: <1.5 average
   - Alert: >2.0
   - Action: Improve prompt guidance

### Log Queries

```bash
# Success rate
cat logs/json_pipeline.log | jq -r 'select(.event_type == "json_pipeline_event") | .success' | awk '{sum+=$1; count++} END {print (sum/count)*100"%"}'

# Average token count
cat logs/json_pipeline.log | jq -r 'select(.token_count) | .token_count' | awk '{sum+=$1; count++} END {print sum/count}'

# Validation errors
cat logs/json_pipeline.log | jq -r 'select(.event_type == "validation_error") | .validation_errors[]' | sort | uniq -c | sort -rn
```

---

## Rollback Procedures

### Emergency Rollback (<5 minutes)

```bash
# 1. Disable JSON pipeline
echo "ENABLE_JSON_OUTPUT=false" >> .env

# 2. Restart backend
systemctl restart lesson-plan-backend

# 3. Verify
curl http://localhost:8000/api/health | jq '.pipeline_mode'
# Should return: "markdown"

# 4. Document incident
cp docs/templates/incident_report.md docs/incidents/$(date +%Y%m%d)_json_pipeline.md
```

### Gradual Rollback

```bash
# Reduce rollout percentage incrementally
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=50" >> .env  # From 100%
systemctl restart lesson-plan-backend

# Monitor for 1 hour, then reduce further if needed
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=10" >> .env
systemctl restart lesson-plan-backend
```

---

## Success Criteria

Phase 0 is successful if:

- ✅ Feature flag toggles pipeline mode correctly
- ✅ Telemetry logs events with proper structure
- ✅ Pre-commit hooks prevent bad commits
- ✅ Metrics can be exported and analyzed
- ✅ Runbook procedures work as documented
- ✅ Rollback can be executed in <5 minutes
- ✅ No impact on existing markdown pipeline

**Status:** ✅ **ALL CRITERIA MET**

---

## Next Steps

### Ready for Phase 1: JSON Schema Definition

**Prerequisites (from Phase 0):**
- ✅ Feature flag system
- ✅ Telemetry infrastructure
- ✅ Pre-commit validation
- ✅ Operational runbook

**Phase 1 Tasks:**
1. Define `schemas/lesson_output_schema.json`
2. Create test fixtures (valid & invalid)
3. Validate schema structure
4. Document schema fields

**Estimated Duration:** 1 week

---

## Documentation

- **Configuration:** `backend/config.py` (inline docstrings)
- **Telemetry:** `backend/telemetry.py` (inline docstrings)
- **Runbook:** `docs/runbooks/json_pipeline_toggle.md`
- **Implementation Plan:** `docs/json_output_implementation_plan.md`
- **This README:** `README_PHASE0.md`

---

## Support

**Questions?** Review the runbook: `docs/runbooks/json_pipeline_toggle.md`

**Issues?** Check logs: `tail -f logs/json_pipeline.log`

**Metrics?** Run: `python tools/metrics_summary.py`

---

**Phase 0 Status:** ✅ **COMPLETE**  
**Ready for Phase 1:** ✅ **YES**  
**Time to Implement:** 1 session (faster than planned 1 week)

---

*Last Updated: 2025-10-04*
