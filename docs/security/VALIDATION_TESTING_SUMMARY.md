# Alertmanager Validation and Testing - Quick Reference

## Quick Commands

**Validate Configuration:**

Linux/Mac/Git Bash:
```bash
scripts/validate_alertmanager_config.sh
```

Windows PowerShell:
```powershell
scripts/validate_alertmanager_config.ps1
```

**Test Alert Payload:**

Linux/Mac/Git Bash (requires bash):
```bash
# Default test
scripts/test_alertmanager_payload.sh

# Specific alert
scripts/test_alertmanager_payload.sh CriticalRateLimitViolations

# Custom Alertmanager URL
ALERTMANAGER_URL=http://alertmanager:9093 scripts/test_alertmanager_payload.sh
```

## Pre-Production Checklist

- [ ] Run validation script - no errors
- [ ] Replace placeholder URLs/credentials
- [ ] Test alerts in staging
- [ ] Verify notifications received
- [ ] Verify runbook URLs work
- [ ] Test alert resolution

## Files Created

- `scripts/validate_alertmanager_config.sh` - Configuration validator (bash)
- `scripts/validate_alertmanager_config.ps1` - Configuration validator (PowerShell)
- `scripts/test_alertmanager_payload.sh` - Alert payload tester (bash)
- `docs/security/ALERTMANAGER_VALIDATION_TESTING.md` - Full guide

## Common Issues

**Template path:** Update `/etc/alertmanager/templates/*.tmpl` to match deployment

**Missing notifications:** Check receiver configs and webhook URLs

**Placeholder URLs:** Replace `your-docs-site.com` in `alerts.yml` and `alert_templates.tmpl`

See [ALERTMANAGER_VALIDATION_TESTING.md](ALERTMANAGER_VALIDATION_TESTING.md) for detailed troubleshooting.

