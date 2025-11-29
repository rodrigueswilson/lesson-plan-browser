# Alertmanager Complete Setup Guide

Complete guide to setting up, validating, and using Alertmanager for rate limiter and Redis monitoring.

## Quick Navigation

- **Setup:** [Alertmanager Receivers Guide](ALERTMANAGER_RECEIVERS_GUIDE.md) - Configure notification channels
- **Validation:** [Alertmanager Validation Guide](ALERTMANAGER_VALIDATION_TESTING.md) - Validate configuration
- **Testing:** [Alertmanager Test Payloads](ALERTMANAGER_TEST_PAYLOADS.md) - Copy-paste test commands
- **On-Call:** [On-Call Validation Checklist](ON_CALL_VALIDATION_CHECKLIST.md) - Quick validation steps
- **Runbooks:** [Alert Runbook](ALERT_RUNBOOK.md) - Detailed remediation steps

## Setup Checklist

### 1. Configuration Files

- [ ] `prometheus/alertmanager.yml` - Alert routing and receivers
- [ ] `prometheus/alert_templates.tmpl` - Notification templates (optional)
- [ ] `prometheus/alerts.yml` - Prometheus alert rules
- [ ] All files have correct paths and references

### 2. Receivers Configuration

- [ ] Slack webhook configured (if using Slack)
- [ ] PagerDuty integration key configured (if using PagerDuty)
- [ ] SMTP/Email configured (if using email)
- [ ] All placeholders replaced with real credentials
- [ ] Secrets stored in secrets manager (not in git)

### 3. Documentation URLs

- [ ] Replace `your-docs-site.com` in:
  - `prometheus/alerts.yml` (all `runbook_url` annotations)
  - `prometheus/alert_templates.tmpl` (if using templates)
- [ ] Verify runbook URLs are accessible
- [ ] Test anchor links (e.g., `#high-rate-limit-violations`)

### 4. Validation

- [ ] Run validation script: `scripts/validate_alertmanager_config.sh` (or `.ps1` on Windows)
- [ ] No placeholder values detected
- [ ] All receivers referenced in routes
- [ ] All alerts have `runbook_url` annotations

### 5. Testing

- [ ] Alertmanager accessible: `curl http://localhost:9093/-/healthy`
- [ ] Send test alerts: `scripts/test_alertmanager_payload.sh`
- [ ] Verify notifications received in all channels
- [ ] Verify runbook URLs work
- [ ] Test alert resolution

### 6. Production Deployment

- [ ] Configuration validated in staging
- [ ] All tests passing
- [ ] On-call team trained on validation checklist
- [ ] Monitoring for Alertmanager itself configured
- [ ] Runbook accessible to on-call team

## File Structure

```
prometheus/
├── alertmanager.yml              # Alert routing and receivers
├── alert_templates.tmpl          # Notification templates (optional)
├── alerts.yml                    # Prometheus alert rules
└── alertmanager_receivers_examples.yml  # Example receiver configs

scripts/
├── validate_alertmanager_config.sh      # Config validator (bash)
├── validate_alertmanager_config.ps1     # Config validator (PowerShell)
├── test_alertmanager_payload.sh        # Alert tester (bash)
└── test_alertmanager_curl.sh            # Interactive curl tester

docs/security/
├── ALERTMANAGER_RECEIVERS_GUIDE.md     # Receiver setup guide
├── ALERTMANAGER_VALIDATION_TESTING.md  # Validation guide
├── ALERTMANAGER_TEST_PAYLOADS.md       # Test payloads
├── ON_CALL_VALIDATION_CHECKLIST.md     # On-call checklist
├── ALERT_RUNBOOK.md                    # Detailed runbook
└── ALERT_RUNBOOK_QUICK_REFERENCE.md    # Quick reference
```

## Quick Commands Reference

**Validate configuration:**
```bash
# Linux/Mac/Git Bash
scripts/validate_alertmanager_config.sh

# Windows PowerShell
scripts/validate_alertmanager_config.ps1
```

**Test alerts:**
```bash
# Interactive test script
scripts/test_alertmanager_curl.sh

# Single alert test
scripts/test_alertmanager_payload.sh HighRateLimitViolations

# Custom Alertmanager URL
ALERTMANAGER_URL=http://staging-alertmanager:9093 scripts/test_alertmanager_payload.sh
```

**Health checks:**
```bash
# Alertmanager health
curl http://localhost:9093/-/healthy

# Active alerts
curl http://localhost:9093/api/v1/alerts | jq '.'

# Configuration status
curl http://localhost:9093/api/v1/status/config | jq '.data'
```

## Common Workflows

### Initial Setup

1. Copy receiver examples from `alertmanager_receivers_examples.yml`
2. Configure receivers in `alertmanager.yml`
3. Replace placeholder URLs in `alerts.yml`
4. Run validation script
5. Test in staging environment
6. Deploy to production

### On-Call Shift Start

1. Run pre-shift validation (see [On-Call Checklist](ON_CALL_VALIDATION_CHECKLIST.md))
2. Verify Alertmanager health
3. Check active alerts
4. Test notification channels

### During Incident

1. Verify alert received in Alertmanager
2. Check notification received (Slack/PagerDuty/Email)
3. Click runbook URL
4. Follow remediation steps in [Alert Runbook](ALERT_RUNBOOK.md)

### Post-Incident

1. Verify alert resolved
2. Check resolution notification received
3. Update runbook if gaps found
4. Document lessons learned

## Troubleshooting

**Alertmanager not responding:**
- Check process is running
- Check port 9093 accessible
- Review logs: `docker logs alertmanager` or `journalctl -u alertmanager`

**Alerts not routing:**
- Verify route matching in `alertmanager.yml`
- Check alert labels match route conditions
- Review Alertmanager logs

**Notifications not received:**
- Verify receiver webhook URLs/keys configured
- Check network connectivity
- Review receiver logs

**Runbook URLs broken:**
- Verify docs URL correct (not placeholder)
- Check URL accessible
- Verify anchor links work

## Next Steps

1. **Replace placeholders:** Update docs URLs and credentials
2. **Test in staging:** Send test alerts and verify notifications
3. **Train team:** Share on-call checklist with team
4. **Monitor:** Set up monitoring for Alertmanager itself
5. **Iterate:** Update runbooks based on incidents

## See Also

- [Production Rollout Playbook](PRODUCTION_ROLLOUT_PLAYBOOK.md) - Deployment guide
- [Rollback Procedures](ROLLBACK_PROCEDURES.md) - Emergency rollback steps
- [Incident Response Checklist](INCIDENT_RESPONSE_CHECKLIST.md) - Incident handling
- [Prometheus Metrics](PROMETHEUS_METRICS.md) - Metrics setup
- [Prometheus Alerts Dashboard](PROMETHEUS_ALERTS_DASHBOARD.md) - Alert rules and dashboard

