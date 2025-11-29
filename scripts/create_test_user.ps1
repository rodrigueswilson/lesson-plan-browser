# Create a test user via API
# Usage: .\scripts\create_test_user.ps1

$body = @{
    first_name = "Test"
    last_name = "User"
    email = "test@example.com"
} | ConvertTo-Json

Write-Host "Creating test user..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/users" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 5
    
    Write-Host "✓ User created successfully!" -ForegroundColor Green
    Write-Host "`nResponse:" -ForegroundColor Cyan
    Write-Host $response.Content -ForegroundColor White
    
    # Parse and display user info
    $user = $response.Content | ConvertFrom-Json
    Write-Host "`nUser Details:" -ForegroundColor Yellow
    Write-Host "  ID: $($user.id)" -ForegroundColor White
    Write-Host "  Name: $($user.first_name) $($user.last_name)" -ForegroundColor White
    Write-Host "  Email: $($user.email)" -ForegroundColor White
    
} catch {
    Write-Host "✗ Error creating user" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body:" -ForegroundColor Yellow
        Write-Host $responseBody -ForegroundColor White
    }
}

