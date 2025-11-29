# Alertmanager Receivers Configuration Guide

**Date:** January 2025  
**Purpose:** Copy-paste ready receiver configurations for common notification channels

---

## Overview

This guide provides production-ready Alertmanager receiver configurations for:
- Slack
- PagerDuty
- Email (SMTP)
- Webhooks
- Opsgenie
- Microsoft Teams
- Discord

---

## Quick Start

### 1. Choose Your Receivers

Select receivers based on your notification needs:

- **Critical Alerts:** PagerDuty + Slack + Email
- **Warning Alerts:** Slack + Email
- **Team-Specific:** Slack channels per team

### 2. Copy Configuration

Copy receiver blocks from `prometheus/alertmanager_receivers_examples.yml` to your `prometheus/alertmanager.yml`

### 3. Replace Placeholders

- Replace `YOUR_SLACK_WEBHOOK_URL` with actual webhook
- Replace `YOUR_PAGERDUTY_SERVICE_KEY` with actual key
- Replace SMTP credentials with your email server details

---

## Slack Configuration

### Get Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Create new app or select existing
3. Go to "Incoming Webhooks"
4. Activate webhooks
5. Add webhook to workspace
6. Copy webhook URL

### Basic Slack Receiver

```yaml
receivers:
  - name: 'slack-oncall'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/REPLACE_WITH_YOUR_WEBHOOK'
        channel: '#oncall-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: |
          *Alert:* {{ .GroupLabels.alertname }}
          *Severity:* {{ .GroupLabels.severity }}
          *Runbook:* {{ .Annotations.runbook_url }}
        send_resolved: true
```

### Slack with Rich Formatting

```yaml
receivers:
  - name: 'slack-rich'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#oncall-alerts'
        username: 'Alertmanager'
        icon_emoji: ':warning:'
        title: '{{ .GroupLabels.alertname }}'
        title_link: '{{ .Annotations.runbook_url }}'
        text: |
          *Severity:* {{ .GroupLabels.severity }}
          *Environment:* {{ .GroupLabels.env }}
          *Description:* {{ .Annotations.description }}
        color: '{{ if eq .GroupLabels.severity "critical" }}danger{{ else }}warning{{ end }}'
        send_resolved: true
```

---

## PagerDuty Configuration

### Get PagerDuty Integration Key

1. Log into PagerDuty
2. Go to Configuration → Services
3. Create new service or select existing
4. Go to Integrations tab
5. Add Prometheus integration
6. Copy Integration Key

### Basic PagerDuty Receiver

```yaml
receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
        severity: '{{ .GroupLabels.severity }}'
        details:
          alertname: '{{ .GroupLabels.alertname }}'
          severity: '{{ .GroupLabels.severity }}'
          environment: '{{ .GroupLabels.env }}'
          runbook_url: '{{ .Annotations.runbook_url }}'
        send_resolved: true
```

### PagerDuty V2 Events API

```yaml
receivers:
  - name: 'pagerduty-v2'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_ROUTING_KEY'
        description: '{{ .GroupLabels.alertname }}'
        severity: '{{ .GroupLabels.severity }}'
        group: '{{ .GroupLabels.component }}'
        custom_details:
          runbook_url: '{{ .Annotations.runbook_url }}'
        links:
          - href: '{{ .Annotations.runbook_url }}'
            text: 'Runbook'
        send_resolved: true
```

---

## Email (SMTP) Configuration

### Gmail SMTP

```yaml
receivers:
  - name: 'email-gmail'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'  # Use App Password, not regular password
        headers:
          Subject: 'Alert: {{ .GroupLabels.alertname }}'
        html: |
          <h2>Alert: {{ .GroupLabels.alertname }}</h2>
          <p><strong>Severity:</strong> {{ .GroupLabels.severity }}</p>
          <p><strong>Runbook:</strong> <a href="{{ .Annotations.runbook_url }}">View Runbook</a></p>
        send_resolved: true
        require_tls: true
```

**Note:** For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password (not your regular password)

### Generic SMTP

```yaml
receivers:
  - name: 'email-smtp'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'your-smtp-password'
        headers:
          Subject: '{{ if eq .GroupLabels.severity "critical" }}[CRITICAL]{{ else }}[WARNING]{{ end }} {{ .GroupLabels.alertname }}'
        html: |
          <h2>{{ .GroupLabels.alertname }}</h2>
          <p><a href="{{ .Annotations.runbook_url }}">View Runbook</a></p>
        send_resolved: true
```

### Office 365 / Outlook SMTP

```yaml
receivers:
  - name: 'email-office365'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.office365.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'your-password'
        headers:
          Subject: 'Alert: {{ .GroupLabels.alertname }}'
        html: |
          <h2>{{ .GroupLabels.alertname }}</h2>
          <p><a href="{{ .Annotations.runbook_url }}">View Runbook</a></p>
        send_resolved: true
        require_tls: true
```

---

## Combined Receiver Example

### Critical Alerts - Multi-Channel

```yaml
receivers:
  - name: 'oncall-critical'
    # PagerDuty for immediate notification
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_CRITICAL_KEY'
        description: 'CRITICAL: {{ .GroupLabels.alertname }}'
        severity: 'critical'
        details:
          runbook_url: '{{ .Annotations.runbook_url }}'
    
    # Slack for team visibility
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/REPLACE_WITH_YOUR_WEBHOOK'
        channel: '#oncall-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          *Runbook:* {{ .Annotations.runbook_url }}
          *Description:* {{ .Annotations.description }}
    
    # Email for record keeping
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'your-password'
        headers:
          Subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        html: |
          <h2>CRITICAL Alert</h2>
          <p><a href="{{ .Annotations.runbook_url }}">View Runbook</a></p>
    
    send_resolved: true
```

---

## Security Best Practices

### Store Secrets Securely

**Option 1: Environment Variables**
```yaml
receivers:
  - name: 'slack-secure'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
```

**Option 2: Secret Management**
- Use Kubernetes secrets
- Use HashiCorp Vault
- Use cloud provider secret managers

**Option 3: Separate Config File**
```bash
# Store sensitive values in separate file
# alertmanager-secrets.yml (not in git)
# Reference in main config
```

### Use App Passwords

- Gmail: Use App Passwords (not regular passwords)
- Office 365: Use App Passwords if 2FA enabled
- Never commit passwords to git

---

## Testing Receivers

### Test Slack Webhook

```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert from Alertmanager"}' \
  YOUR_SLACK_WEBHOOK_URL
```

### Test Email

```bash
# Use mail command or send test email
echo "Test" | mail -s "Test Alert" oncall@example.com
```

### Test PagerDuty

```bash
# Trigger test incident via PagerDuty API
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "YOUR_ROUTING_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "Test alert",
      "severity": "critical",
      "source": "alertmanager-test"
    }
  }'
```

---

## Common Issues

### Slack Webhook Not Working

**Symptoms:** No messages in Slack

**Solutions:**
1. Verify webhook URL is correct
2. Check Slack app permissions
3. Test webhook directly with curl
4. Check Alertmanager logs

### Email Not Sending

**Symptoms:** No emails received

**Solutions:**
1. Verify SMTP credentials
2. Check firewall allows SMTP port (587/465)
3. Test SMTP connection: `telnet smtp.example.com 587`
4. Check Alertmanager logs for errors
5. Verify TLS settings match server

### PagerDuty Not Triggering

**Symptoms:** No incidents in PagerDuty

**Solutions:**
1. Verify integration key is correct
2. Check PagerDuty service is active
3. Verify severity mapping
4. Check Alertmanager logs

---

## Integration Examples

### Route Critical to PagerDuty

```yaml
route:
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
```

### Route by Component

```yaml
route:
  routes:
    - match:
        component: redis
      receiver: 'redis-team'
    - match:
        component: rate_limiter
      receiver: 'rate-limiter-team'
```

### Route by Environment

```yaml
route:
  routes:
    - match:
        env: prod
      receiver: 'oncall-critical'
    - match:
        env: staging
      receiver: 'oncall-warning'
```

---

## Files Reference

- `prometheus/alertmanager_receivers_examples.yml` - All receiver examples
- `prometheus/alertmanager.yml` - Main Alertmanager config
- `docs/security/ALERTMANAGER_SETUP.md` - Setup guide

---

**Last Updated:** January 2025  
**Status:** Ready for Use ✅

