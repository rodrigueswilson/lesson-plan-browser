# Deployment Checklist - Alerts & Monitoring

Use this checklist to track your progress deploying Prometheus and Alertmanager.

## Phase 1: Local Testing

### Setup
- [ ] Docker Compose file created (`docker-compose.monitoring.yml`)
- [ ] Prometheus config created (`prometheus/prometheus.yml`)
- [ ] Services started: `docker-compose -f docker-compose.monitoring.yml up -d`
- [ ] Prometheus accessible: http://localhost:9090
- [ ] Alertmanager accessible: http://localhost:9093

### Configuration
- [ ] Prometheus scrape config updated (FastAPI target)
- [ ] Alertmanager email configured
- [ ] Placeholder URLs replaced in `alerts.yml`
- [ ] Placeholder URLs replaced in `alert_templates.tmpl`
- [ ] Configs reloaded (Prometheus and Alertmanager)

### Testing
- [ ] FastAPI `/metrics` endpoint accessible
- [ ] Prometheus scraping FastAPI (check Targets page)
- [ ] Test alert sent successfully
- [ ] Email notification received
- [ ] Runbook URL works in email

**Time estimate:** 30 minutes

---

## Phase 2: Integration Testing

### Metrics Generation
- [ ] Rate limiting triggered (generate real metrics)
- [ ] Metrics visible in Prometheus
- [ ] Alert rules evaluating correctly

### Alert Validation
- [ ] Alerts fire when thresholds exceeded
- [ ] Alerts route to correct receivers
- [ ] Email notifications formatted correctly
- [ ] Runbook links present and working
- [ ] Alert resolution notifications work

### Threshold Tuning
- [ ] Alert thresholds appropriate for your traffic
- [ ] No false positives observed
- [ ] Alert firing frequency acceptable

**Time estimate:** 1 hour

---

## Phase 3: Staging Deployment

### Deployment
- [ ] Prometheus deployed to staging
- [ ] Alertmanager deployed to staging
- [ ] Persistent storage configured
- [ ] Health checks configured

### Configuration
- [ ] Environment labels set to `staging`
- [ ] Staging email addresses configured
- [ ] Scrape targets point to staging API
- [ ] Docs URLs updated for staging (if different)

### Validation
- [ ] Validation scripts run successfully
- [ ] Test alerts sent and verified
- [ ] All notification channels working
- [ ] Runbooks accessible from staging

### Monitoring Period
- [ ] Monitor for 24-48 hours
- [ ] No false positives
- [ ] All alert types tested
- [ ] Thresholds adjusted if needed

**Time estimate:** 2 hours (plus 24-48h monitoring)

---

## Phase 4: Production Deployment

### Pre-Deployment
- [ ] All placeholder URLs replaced
- [ ] Email SMTP tested and working
- [ ] Alert thresholds validated in staging
- [ ] Runbooks accessible to on-call team
- [ ] On-call rotation configured
- [ ] Escalation contacts added
- [ ] Team announcement sent

### Deployment
- [ ] Prometheus deployed to production
- [ ] Alertmanager deployed to production
- [ ] High availability configured (if needed)
- [ ] Persistent storage configured
- [ ] Backups configured

### Configuration
- [ ] Environment labels set to `production`
- [ ] Production email addresses configured
- [ ] Scrape targets point to production API
- [ ] Production docs URLs configured

### Verification
- [ ] Prometheus health check passes
- [ ] Alertmanager health check passes
- [ ] All targets UP in Prometheus
- [ ] Test alert sent and verified
- [ ] Email notifications received
- [ ] Runbook links work

**Time estimate:** 4 hours

---

## Phase 5: Ongoing Maintenance

### Weekly Checks
- [ ] Review alert firing frequency
- [ ] Check for false positives
- [ ] Verify email notifications working
- [ ] Review Prometheus/Alertmanager health

### Monthly Tasks
- [ ] Review and tune alert thresholds
- [ ] Update runbooks based on incidents
- [ ] Review alert rules for relevance
- [ ] Check storage usage

### As Needed
- [ ] Add new alerts for new issues
- [ ] Update runbooks with new procedures
- [ ] Adjust thresholds based on traffic patterns
- [ ] Update on-call contacts

---

## Quick Commands Reference

**Start services:**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Validate config:**
```bash
scripts/validate_alertmanager_config.sh
```

**Test alerts:**
```bash
scripts/test_alertmanager_payload.sh HighRateLimitViolations
```

**Reload configs:**
```bash
curl -X POST http://localhost:9090/-/reload  # Prometheus
curl -X POST http://localhost:9093/-/reload  # Alertmanager
```

**Check health:**
```bash
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:9093/-/healthy  # Alertmanager
```

**View alerts:**
```bash
curl http://localhost:9093/api/v1/alerts | jq '.'
```

---

## Troubleshooting

**Prometheus not scraping:**
- Check http://localhost:9090/targets
- Verify FastAPI `/metrics` accessible
- Check network connectivity

**Alerts not firing:**
- Check http://localhost:9090/alerts
- Verify rules loaded: http://localhost:9090/rules
- Check evaluation interval

**Email not received:**
- Verify SMTP settings
- Check Alertmanager logs
- Test SMTP separately

---

## Documentation

- [Full Deployment Guide](NEXT_STEPS_ALERTS_DEPLOYMENT.md)
- [Quick Summary](NEXT_STEPS_SUMMARY.md)
- [Alert Runbook](ALERT_RUNBOOK.md)
- [On-Call Checklist](ON_CALL_VALIDATION_CHECKLIST.md)

