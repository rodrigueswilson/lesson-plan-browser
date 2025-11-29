# Supabase Configuration Setup Script for Windows
# This script helps you set up your Supabase credentials

Write-Host "=== Supabase Configuration Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if local.properties already exists
if (Test-Path "local.properties") {
    Write-Host "⚠️  local.properties already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit
    }
}

# Copy example file
if (Test-Path "local.properties.example") {
    Copy-Item "local.properties.example" "local.properties"
    Write-Host "✅ Created local.properties from example" -ForegroundColor Green
} else {
    Write-Host "❌ local.properties.example not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Please enter your Supabase credentials:" -ForegroundColor Cyan
Write-Host ""

# Get Project 1 credentials
Write-Host "--- Project 1 (Wilson Rodrigues) ---" -ForegroundColor Yellow
$url1 = Read-Host "Project 1 URL (e.g., https://xxxxx.supabase.co)"
$key1 = Read-Host "Project 1 anon key"

Write-Host ""
Write-Host "--- Project 2 (Daniela Silva) ---" -ForegroundColor Yellow
$url2 = Read-Host "Project 2 URL (e.g., https://xxxxx.supabase.co)"
$key2 = Read-Host "Project 2 anon key"

# Update local.properties
$content = @"
# Supabase Configuration
# Project 1 (Wilson Rodrigues)
SUPABASE_URL_PROJECT1=$url1
SUPABASE_KEY_PROJECT1=$key1

# Project 2 (Daniela Silva)
SUPABASE_URL_PROJECT2=$url2
SUPABASE_KEY_PROJECT2=$key2
"@

Set-Content -Path "local.properties" -Value $content

Write-Host ""
Write-Host "✅ Configuration saved to local.properties" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review local.properties to verify your credentials"
Write-Host "2. Run: ./gradlew clean build"
Write-Host "3. Test the app on a device or emulator"
Write-Host ""

