# Test User Management Workflow
# Tests the complete user CRUD operations

Write-Host "`n=== User Management Workflow Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://127.0.0.1:8000/api"

# Test 1: Health Check
Write-Host "[1/6] Testing API Health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host "  ✓ API is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ API health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: List Users
Write-Host "[2/6] Testing List Users..." -ForegroundColor Yellow
try {
    $users = Invoke-WebRequest -Uri "$baseUrl/users" -UseBasicParsing | ConvertFrom-Json
    Write-Host "  ✓ Found $($users.Count) users" -ForegroundColor Green
    foreach ($user in $users) {
        Write-Host "    - $($user.name) ($($user.email))" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Failed to list users: $_" -ForegroundColor Red
}

# Test 3: Get User by ID
Write-Host "[3/6] Testing Get User by ID..." -ForegroundColor Yellow
if ($users.Count -gt 0) {
    $testUserId = $users[0].id
    try {
        $user = Invoke-WebRequest -Uri "$baseUrl/users/$testUserId" -UseBasicParsing | ConvertFrom-Json
        Write-Host "  ✓ Retrieved user: $($user.name)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to get user: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠ Skipped (no users available)" -ForegroundColor Yellow
}

# Test 4: Create User
Write-Host "[4/6] Testing Create User..." -ForegroundColor Yellow
$newUser = @{
    first_name = "Test"
    last_name = "User"
    email = "test.user@example.com"
} | ConvertTo-Json

try {
    $created = Invoke-WebRequest -Uri "$baseUrl/users" -Method POST -Body $newUser -ContentType "application/json" -UseBasicParsing | ConvertFrom-Json
    Write-Host "  ✓ Created user: $($created.name) (ID: $($created.id))" -ForegroundColor Green
    
    # Clean up: Delete test user
    Write-Host "[5/6] Cleaning up test user..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "$baseUrl/users/$($created.id)" -Method DELETE -UseBasicParsing | Out-Null
        Write-Host "  ✓ Test user deleted" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Failed to delete test user: $_" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Failed to create user: $_" -ForegroundColor Red
    $errorDetails = $_.Exception.Response
    if ($errorDetails) {
        $reader = New-Object System.IO.StreamReader($errorDetails.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "    Error details: $responseBody" -ForegroundColor Red
    }
}

# Test 5: Authorization Test
Write-Host "[6/6] Testing Authorization..." -ForegroundColor Yellow
if ($users.Count -gt 0) {
    $testUserId = $users[0].id
    $headers = @{ "X-Current-User-Id" = $testUserId }
    try {
        $user = Invoke-WebRequest -Uri "$baseUrl/users/$testUserId" -Headers $headers -UseBasicParsing | ConvertFrom-Json
        Write-Host "  ✓ Authorization header accepted" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Authorization test: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Skipped (no users available)" -ForegroundColor Yellow
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""

