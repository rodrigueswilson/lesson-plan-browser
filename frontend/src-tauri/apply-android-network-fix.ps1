# Apply Android Network Security Configuration Fix
# Run this script after 'npx tauri android init' to enable cleartext HTTP traffic
# This allows the app to connect to the PC backend via http://10.0.2.2:8000

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResXmlDir = Join-Path $ScriptDir "gen\android\app\src\main\res\xml"
$NetworkConfigFile = Join-Path $ResXmlDir "network_security_config.xml"
$ManifestFile = Join-Path $ScriptDir "gen\android\app\src\main\AndroidManifest.xml"

Write-Host "[Android Network Fix] Applying network security configuration..."

# Create res/xml directory if it doesn't exist
if (-not (Test-Path $ResXmlDir)) {
    New-Item -ItemType Directory -Path $ResXmlDir -Force | Out-Null
    Write-Host "[OK] Created directory: $ResXmlDir"
}

# Create network_security_config.xml
$NetworkConfig = @"
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">127.0.0.1</domain>
    </domain-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">supabase.co</domain>
    </domain-config>
</network-security-config>
"@

Set-Content -Path $NetworkConfigFile -Value $NetworkConfig -Encoding UTF8
Write-Host "[OK] Created network_security_config.xml"

# Update AndroidManifest.xml
if (Test-Path $ManifestFile) {
    $manifestContent = Get-Content $ManifestFile -Raw
    
    # Clean up any malformed entries first
    $manifestContent = $manifestContent -replace '`n', ''
    $manifestContent = $manifestContent -replace 'android:networkSecurityConfig="@xml/network_security_config"\s*\n\s*', 'android:networkSecurityConfig="@xml/network_security_config" '
    
    # Check if already properly fixed
    if ($manifestContent -match 'android:usesCleartextTraffic="true"\s+android:networkSecurityConfig="@xml/network_security_config"') {
        Write-Host "[OK] AndroidManifest.xml already has network security config"
        # Still write it back to clean up any formatting issues
        Set-Content -Path $ManifestFile -Value $manifestContent -Encoding UTF8
    } else {
        # Replace usesCleartextTraffic if it exists as a variable
        $manifestContent = $manifestContent -replace 'android:usesCleartextTraffic="\$\{usesCleartextTraffic\}"', 'android:usesCleartextTraffic="true"'
        
        # Add network security config if not present
        if ($manifestContent -notmatch 'android:networkSecurityConfig') {
            # Add on the same line after usesCleartextTraffic
            if ($manifestContent -match '(android:usesCleartextTraffic="true")') {
                $manifestContent = $manifestContent -replace '(android:usesCleartextTraffic="true")', '$1 android:networkSecurityConfig="@xml/network_security_config"'
            } else {
                # If usesCleartextTraffic is not found, add both after theme
                $manifestContent = $manifestContent -replace '(android:theme="@style/Theme\.bilingual_lesson_planner")', '$1 android:usesCleartextTraffic="true" android:networkSecurityConfig="@xml/network_security_config"'
            }
        }
        
        Set-Content -Path $ManifestFile -Value $manifestContent -Encoding UTF8
        Write-Host "[OK] Updated AndroidManifest.xml"
    }
} else {
    Write-Host "[ERROR] AndroidManifest.xml not found: $ManifestFile"
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] Android network security fix applied!"
Write-Host "You can now build the APK with: .\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug"

