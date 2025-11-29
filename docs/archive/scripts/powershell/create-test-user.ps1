# Create a test user in the database for standalone mode testing
Write-Host "=== Creating Test User in Database ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will create a test user in the local SQLite database"
Write-Host "to verify standalone mode is working."
Write-Host ""

# First, let's try to access the database via Tauri command
Write-Host "Note: This requires the app to be running and Tauri commands to work."
Write-Host "Alternatively, we can insert directly into the database file."
Write-Host ""

# Generate a test user ID and SQL
$userId = [System.Guid]::NewGuid().ToString()
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$firstName = "Test"
$lastName = "User"
$name = "$firstName $lastName"

Write-Host "Test user details:" -ForegroundColor Yellow
Write-Host "  ID: $userId"
Write-Host "  Name: $name"
Write-Host "  Created: $timestamp"
Write-Host ""

Write-Host "To create this user, you can:" -ForegroundColor Cyan
Write-Host "1. Use the app's 'Add User' button (if UI is working)"
Write-Host "2. Use Tauri command from frontend dev tools"
Write-Host "3. Insert directly into database file (requires root/adb access)"
Write-Host ""

# SQL to create user
$sql = @"
INSERT INTO users (id, first_name, last_name, name, email, created_at, updated_at)
VALUES ('$userId', '$firstName', '$lastName', '$name', 'test@example.com', '$timestamp', '$timestamp');
"@

Write-Host "SQL command:" -ForegroundColor Yellow
Write-Host $sql
Write-Host ""

Write-Host "To execute this SQL, you can use the Tauri sql_execute command"
Write-Host "from the browser console or create a helper function."

