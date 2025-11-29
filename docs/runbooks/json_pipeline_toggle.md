# JSON Pipeline Toggle & Observability Runbook

**Version:** 1.0  
**Last Updated:** 2025-10-04  
**Owner:** Backend Team

---

## Overview

This runbook describes how to toggle the JSON output pipeline, monitor its performance, and roll back if issues arise.

---

## Feature Flag: ENABLE_JSON_OUTPUT

### Current Status

Check current status:
```bash
# View .env file
cat .env | grep ENABLE_JSON_OUTPUT

# Or check via API
curl http://localhost:8000/api/health | jq '.pipeline_mode'
```

### Enabling JSON Pipeline

**For All Users:**
```bash
# Edit .env
echo "ENABLE_JSON_OUTPUT=true" >> .env
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=100" >> .env

# Restart backend
systemctl restart lesson-plan-backend
# OR
docker-compose restart backend
```

**For Gradual Rollout (e.g., 10% of users):**
```bash
# Edit .env
echo "ENABLE_JSON_OUTPUT=true" >> .env
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=10" >> .env

# Restart backend
systemctl restart lesson-plan-backend
```

**For Testing (Single User):**
```bash
# Set rollout to 1% and test with specific user_id
# User assignment is deterministic based on hash
echo "ENABLE_JSON_OUTPUT=true" >> .env
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=1" >> .env
```

### Disabling JSON Pipeline

**Immediate Rollback:**
```bash
# Edit .env
echo "ENABLE_JSON_OUTPUT=false" >> .env

# Restart backend
systemctl restart lesson-plan-backend
```

---

## Monitoring & Observability

### Log Files

**Primary Log:**
```bash
# Tail JSON pipeline logs
tail -f logs/json_pipeline.log

# Filter for errors
tail -f logs/json_pipeline.log | jq 'select(.level == "error")'

# Filter for validation errors
tail -f logs/json_pipeline.log | jq 'select(.event_type == "validation_error")'

# Filter for token alerts
tail -f logs/json_pipeline.log | jq 'select(.event_type == "token_footprint_alert")'
```

**Application Log:**
```bash
# General application logs
tail -f logs/app.log
```

### Metrics Dashboard

**Access Dashboard:**
```bash
# If using Grafana
open http://localhost:3000/d/json-pipeline

# If using CSV export
python tools/export_metrics.py --output metrics/$(date +%Y%m%d).csv
```

**Key Metrics to Monitor:**

1. **Success Rate**
   - Target: >95%
   - Alert if: <90%

2. **Validation Error Rate**
   - Target: <5%
   - Alert if: >10%

3. **Average Retry Count**
   - Target: <1.5
   - Alert if: >2.0

4. **Token Usage Delta**
   - Target: <20% increase vs. markdown
   - Alert if: >20%

5. **Render Latency (p95)**
   - Target: <100ms
   - Alert if: >200ms

### Query Metrics Programmatically

```python
# Get metrics summary
from backend.telemetry import get_metrics_summary

summary = get_metrics_summary()
print(f"Success Rate: {summary['success_rate']:.1f}%")
print(f"Avg Token Count: {summary['avg_token_count']:.0f}")
print(f"Median Duration: {summary['median_duration_ms']:.0f}ms")
```

### Export Metrics to CSV

```bash
# Export all metrics
python tools/export_metrics.py --output metrics/export.csv

# View summary
python tools/metrics_summary.py
```

---

## Common Issues & Troubleshooting

### Issue 1: High Validation Error Rate

**Symptoms:**
- Validation error rate >10%
- Many retries
- Users reporting slow generation

**Diagnosis:**
```bash
# Check validation errors
tail -f logs/json_pipeline.log | jq 'select(.event_type == "validation_error")' | head -20

# Get error patterns
cat logs/json_pipeline.log | jq -r 'select(.event_type == "validation_error") | .validation_errors[]' | sort | uniq -c | sort -rn
```

**Resolution:**
1. Identify common error patterns
2. Update prompt with specific guidance
3. Adjust schema if constraints too strict
4. Enable JSON repair if not already enabled

### Issue 2: Token Usage Spike

**Symptoms:**
- Token usage >20% higher than markdown
- Cost alerts triggered
- Slow response times

**Diagnosis:**
```bash
# Check token footprint
tail -f logs/json_pipeline.log | jq 'select(.event_type == "token_footprint_comparison")'

# Calculate average delta
cat logs/json_pipeline.log | jq -r 'select(.event_type == "token_footprint_comparison") | .delta_pct' | awk '{sum+=$1; count++} END {print sum/count}'
```

**Resolution:**
1. Review JSON structure for redundancy
2. Trim empty fields before sending
3. Use ID references for repeated data
4. Adjust MAX_TOKENS_PER_LESSON if needed

### Issue 3: Render Failures

**Symptoms:**
- Render errors in logs
- Users not receiving output
- Timeout errors

**Diagnosis:**
```bash
# Check render errors
tail -f logs/json_pipeline.log | jq 'select(.event_type == "render_error")'

# Check render duration
cat logs/json_pipeline.log | jq -r 'select(.event_type == "render_success") | .duration_ms' | sort -n | tail -10
```

**Resolution:**
1. Check template syntax
2. Verify JSON structure matches schema
3. Increase RENDER_TIMEOUT_SECONDS if needed
4. Check for template infinite loops

### Issue 4: JSON Repair Not Working

**Symptoms:**
- JSON parsing errors despite repair enabled
- High retry count
- Malformed JSON in logs

**Diagnosis:**
```bash
# Check repair attempts
tail -f logs/json_pipeline.log | jq 'select(.event_type == "json_repair_failed")'

# Get failure rate
cat logs/json_pipeline.log | jq -r 'select(.event_type | startswith("json_repair")) | .event_type' | sort | uniq -c
```

**Resolution:**
1. Review failed JSON samples
2. Update prompt with JSON syntax guidance
3. Consider stricter LLM temperature
4. Add pre-validation JSON cleanup

---

## Rollback Procedures

### Emergency Rollback (Immediate)

**If JSON pipeline causes critical issues:**

```bash
# 1. Disable JSON pipeline
echo "ENABLE_JSON_OUTPUT=false" >> .env

# 2. Restart backend
systemctl restart lesson-plan-backend

# 3. Verify legacy pipeline active
curl http://localhost:8000/api/health | jq '.pipeline_mode'
# Should return: "markdown"

# 4. Check logs for errors
tail -100 logs/app.log

# 5. Notify team
echo "JSON pipeline disabled due to [REASON]" | mail -s "Pipeline Rollback" team@example.com
```

### Gradual Rollback

**If issues affect subset of users:**

```bash
# 1. Reduce rollout percentage
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=10" >> .env  # From 50% to 10%

# 2. Restart backend
systemctl restart lesson-plan-backend

# 3. Monitor metrics
tail -f logs/json_pipeline.log | jq 'select(.success == false)'

# 4. Continue reducing if issues persist
echo "JSON_PIPELINE_ROLLOUT_PERCENTAGE=0" >> .env
```

### Post-Rollback Actions

1. **Document Issues:**
   ```bash
   # Create incident report
   cp docs/templates/incident_report.md docs/incidents/$(date +%Y%m%d)_json_pipeline.md
   ```

2. **Analyze Logs:**
   ```bash
   # Export logs for analysis
   cat logs/json_pipeline.log | jq 'select(.timestamp > "2025-10-04T20:00:00")' > analysis/rollback_logs.json
   ```

3. **Plan Fixes:**
   - Review validation errors
   - Update schema if needed
   - Improve prompt guidance
   - Add tests for failure cases

4. **Re-enable When Ready:**
   - Start with 1% rollout
   - Monitor closely for 24 hours
   - Gradually increase to 10%, 25%, 50%, 100%

---

## Health Checks

### Backend Health

```bash
# Check backend status
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "pipeline_mode": "json",
  "version": "2.0.0",
  "uptime_seconds": 3600
}
```

### Pipeline Health

```bash
# Check pipeline metrics
curl http://localhost:8000/api/metrics/summary

# Expected response:
{
  "success_rate": 96.5,
  "avg_token_count": 3200,
  "median_duration_ms": 85,
  "avg_retry_count": 0.8
}
```

### Database Health

```bash
# Check retained payloads
sqlite3 data/lesson_plans.db "SELECT COUNT(*) FROM validated_payloads;"

# Check disk usage
du -sh data/lesson_plans.db
```

---

## Maintenance Tasks

### Daily

- [ ] Check success rate (should be >95%)
- [ ] Review error logs for patterns
- [ ] Verify token usage within budget

### Weekly

- [ ] Export metrics to CSV
- [ ] Review validation error trends
- [ ] Check disk usage for retained payloads
- [ ] Update dashboard if needed

### Monthly

- [ ] Clean up old retained payloads
- [ ] Review and update schema if needed
- [ ] Analyze token usage trends
- [ ] Update this runbook with new learnings

---

## Contacts

**On-Call Engineer:** [Your Team]  
**Escalation:** [Manager/Lead]  
**Slack Channel:** #lesson-plan-backend  
**Email:** backend-team@example.com

---

## Appendix

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_JSON_OUTPUT` | `false` | Enable JSON pipeline |
| `JSON_PIPELINE_ROLLOUT_PERCENTAGE` | `0` | Rollout percentage (0-100) |
| `ENABLE_TELEMETRY` | `true` | Enable logging |
| `MAX_TOKEN_INCREASE_PCT` | `20` | Alert threshold for token increase |
| `MAX_TOKENS_PER_LESSON` | `4000` | Hard limit for tokens |
| `MAX_VALIDATION_RETRIES` | `3` | Max retry attempts |
| `ENABLE_JSON_REPAIR` | `true` | Enable JSON repair |
| `RENDER_TIMEOUT_SECONDS` | `30` | Render timeout |

### Useful Commands

```bash
# Restart backend
systemctl restart lesson-plan-backend

# View logs
tail -f logs/json_pipeline.log

# Export metrics
python tools/export_metrics.py

# Run health check
curl http://localhost:8000/api/health

# Check git status
git status

# Run pre-commit checks
pre-commit run --all-files
```

---

**End of Runbook**
