# Alertmanager Receivers - Quick Reference

**Date:** January 2025  
**Purpose:** Quick copy-paste reference for common receiver configurations

---

## Slack

### Basic
```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ .Annotations.description }}'
    send_resolved: true
```

### With Runbook Link
```yaml
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#oncall-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: |
      *Severity:* {{ .GroupLabels.severity }}
      *Runbook:* {{ .Annotations.runbook_url }}
    send_resolved: true
```

**Get Webhook:** https://api.slack.com/apps → Incoming Webhooks

---

## PagerDuty

### Basic
```yaml
pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
    description: '{{ .GroupLabels.alertname }}'
    severity: '{{ .GroupLabels.severity }}'
    details:
      runbook_url: '{{ .Annotations.runbook_url }}'
    send_resolved: true
```

**Get Key:** PagerDuty → Services → Integrations → Prometheus

---

## Email (SMTP)

### Gmail
```yaml
email_configs:
  - to: 'oncall@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@gmail.com'
    auth_password: 'your-app-password'  # App Password, not regular password
    headers:
      Subject: 'Alert: {{ .GroupLabels.alertname }}'
    html: '<a href="{{ .Annotations.runbook_url }}">View Runbook</a>'
    require_tls: true
    send_resolved: true
```

### Generic SMTP
```yaml
email_configs:
  - to: 'oncall@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alertmanager@example.com'
    auth_password: 'your-password'
    headers:
      Subject: 'Alert: {{ .GroupLabels.alertname }}'
    html: '<a href="{{ .Annotations.runbook_url }}">View Runbook</a>'
    send_resolved: true
```

---

## Combined (Critical Alerts)

```yaml
- name: 'oncall-critical'
  pagerduty_configs:
    - service_key: 'YOUR_PAGERDUTY_KEY'
      description: 'CRITICAL: {{ .GroupLabels.alertname }}'
      severity: 'critical'
  
  slack_configs:
    - api_url: 'YOUR_SLACK_WEBHOOK_URL'
      channel: '#oncall-critical'
      title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
      text: 'Runbook: {{ .Annotations.runbook_url }}'
  
  email_configs:
    - to: 'oncall@example.com'
      smarthost: 'smtp.example.com:587'
      auth_username: 'alertmanager@example.com'
      auth_password: 'your-password'
      headers:
        Subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
  
  send_resolved: true
```

---

## Full Examples

See `prometheus/alertmanager_receivers_examples.yml` for complete examples.

---

**Last Updated:** January 2025

