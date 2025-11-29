# Validate Alertmanager Configuration (PowerShell)
# Checks that alertmanager.yml references templates and receivers correctly

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$AlertmanagerConfig = Join-Path $ProjectRoot "prometheus\alertmanager.yml"
$AlertTemplates = Join-Path $ProjectRoot "prometheus\alert_templates.tmpl"
$AlertsFile = Join-Path $ProjectRoot "prometheus\alerts.yml"

Write-Host "=== Validating Alertmanager Configuration ===" -ForegroundColor Cyan
Write-Host ""

# Check files exist
Write-Host "1. Checking files exist..." -ForegroundColor Yellow
if (-not (Test-Path $AlertmanagerConfig)) {
    Write-Host "   ERROR: alertmanager.yml not found at $AlertmanagerConfig" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ alertmanager.yml found" -ForegroundColor Green

if (-not (Test-Path $AlertTemplates)) {
    Write-Host "   ERROR: alert_templates.tmpl not found at $AlertTemplates" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ alert_templates.tmpl found" -ForegroundColor Green

if (-not (Test-Path $AlertsFile)) {
    Write-Host "   ERROR: alerts.yml not found at $AlertsFile" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ alerts.yml found" -ForegroundColor Green
Write-Host ""

# Check templates section exists
Write-Host "2. Checking templates configuration..." -ForegroundColor Yellow
$ConfigContent = Get-Content $AlertmanagerConfig -Raw
if ($ConfigContent -match "templates:") {
    Write-Host "   ✓ Templates section found" -ForegroundColor Green
    $TemplateMatch = [regex]::Match($ConfigContent, "templates:\s*\r?\n\s*-\s*['""]([^'""]+)['""]")
    if ($TemplateMatch.Success) {
        Write-Host "   Template path: $($TemplateMatch.Groups[1].Value)" -ForegroundColor Cyan
        Write-Host "   NOTE: Ensure this path matches your Alertmanager deployment" -ForegroundColor Yellow
    }
} else {
    Write-Host "   WARNING: No templates section found in alertmanager.yml" -ForegroundColor Yellow
    Write-Host "   Templates are optional but recommended for runbook URLs" -ForegroundColor Yellow
}
Write-Host ""

# Check receivers are defined
Write-Host "3. Checking receivers..." -ForegroundColor Yellow
$Receivers = Select-String -Path $AlertmanagerConfig -Pattern "^- name:" | ForEach-Object {
    if ($_.Line -match "- name:\s*['""]([^'""]+)['""]") {
        $matches[1]
    }
}
$ReceiverCount = ($Receivers | Measure-Object).Count
Write-Host "   Found $ReceiverCount receiver(s):" -ForegroundColor Cyan
$Receivers | ForEach-Object { Write-Host "     - $_" -ForegroundColor Cyan }
Write-Host ""

# Check routes reference receivers
Write-Host "4. Checking route references..." -ForegroundColor Yellow
$MissingReceivers = @()
foreach ($receiver in $Receivers) {
    if ($ConfigContent -match "receiver:\s*['""]$receiver['""]") {
        Write-Host "   ✓ Receiver '$receiver' is referenced in routes" -ForegroundColor Green
    } else {
        Write-Host "   WARNING: Receiver '$receiver' is defined but not referenced in routes" -ForegroundColor Yellow
        $MissingReceivers += $receiver
    }
}
Write-Host ""

# Check for placeholder values
Write-Host "5. Checking for placeholder values..." -ForegroundColor Yellow
$PlaceholdersFound = $false
$PlaceholderPatterns = @(
    "YOUR_SLACK_WEBHOOK_URL",
    "YOUR_PAGERDUTY_SERVICE_KEY",
    "oncall@example.com",
    "your-docs-site.com"
)

$PlaceholderLines = @()
foreach ($pattern in $PlaceholderPatterns) {
    $matches = Select-String -Path $AlertmanagerConfig -Pattern $pattern
    if ($matches) {
        $PlaceholdersFound = $true
        $PlaceholderLines += $matches | ForEach-Object { "Line $($_.LineNumber): $($_.Line.Trim())" }
    }
}

if ($PlaceholdersFound) {
    Write-Host "   WARNING: Placeholder values found in alertmanager.yml:" -ForegroundColor Yellow
    $PlaceholderLines | ForEach-Object { Write-Host "     $_" -ForegroundColor Yellow }
} else {
    Write-Host "   ✓ No placeholder values found" -ForegroundColor Green
}
Write-Host ""

# Check alerts.yml for runbook_url annotations
Write-Host "6. Checking alerts.yml for runbook_url annotations..." -ForegroundColor Yellow
$AlertsContent = Get-Content $AlertsFile -Raw
$AlertCount = ([regex]::Matches($AlertsContent, "- alert:")).Count
$RunbookCount = ([regex]::Matches($AlertsContent, "runbook_url:")).Count
Write-Host "   Found $AlertCount alert(s)" -ForegroundColor Cyan
Write-Host "   Found $RunbookCount runbook_url annotation(s)" -ForegroundColor Cyan
if ($AlertCount -eq $RunbookCount) {
    Write-Host "   ✓ All alerts have runbook_url annotations" -ForegroundColor Green
} else {
    Write-Host "   WARNING: Alert count ($AlertCount) != runbook_url count ($RunbookCount)" -ForegroundColor Yellow
}

if ($AlertsContent -match "your-docs-site.com") {
    Write-Host "   WARNING: Placeholder docs URL found in alerts.yml" -ForegroundColor Yellow
    Write-Host "   Replace 'your-docs-site.com' with your actual documentation URL" -ForegroundColor Yellow
}
Write-Host ""

# Check template file for placeholder URLs
Write-Host "7. Checking alert_templates.tmpl..." -ForegroundColor Yellow
$TemplatesContent = Get-Content $AlertTemplates -Raw
if ($TemplatesContent -match "your-docs-site.com") {
    Write-Host "   WARNING: Placeholder docs URL found in alert_templates.tmpl" -ForegroundColor Yellow
    Write-Host "   Replace 'your-docs-site.com' with your actual documentation URL" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ No placeholder URLs found in templates" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "=== Validation Summary ===" -ForegroundColor Cyan
if ($PlaceholdersFound) {
    Write-Host "⚠️  Configuration has placeholder values that need to be replaced" -ForegroundColor Yellow
    Write-Host "   See warnings above for details" -ForegroundColor Yellow
    exit 1
} elseif ($MissingReceivers.Count -gt 0) {
    Write-Host "⚠️  Some receivers are not referenced in routes" -ForegroundColor Yellow
    Write-Host "   Receivers: $($MissingReceivers -join ', ')" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Configuration looks good!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Replace placeholder URLs/credentials if any warnings were shown"
    Write-Host "2. Ensure template path matches your Alertmanager deployment"
    Write-Host "3. Test configuration with: scripts/test_alertmanager_payload.sh"
    exit 0
}

