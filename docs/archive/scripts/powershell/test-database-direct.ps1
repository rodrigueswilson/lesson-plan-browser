# Test database directly on device
Write-Host "=== Testing Database Access ===" -ForegroundColor Cyan

# Try to check database file
Write-Host "Checking database file existence..." -ForegroundColor Yellow
$result = adb shell "run-as com.lessonplanner.bilingual ls -la databases/lesson_planner.db 2>&1"
Write-Host $result

# Try to query users table
Write-Host "`nQuerying users table..." -ForegroundColor Yellow
$queryResult = adb shell "run-as com.lessonplanner.bilingual sqlite3 databases/lesson_planner.db 'SELECT COUNT(*) FROM users;' 2>&1"
Write-Host $queryResult

# Check if tables exist
Write-Host "`nChecking if users table exists..." -ForegroundColor Yellow
$tableCheck = adb shell "run-as com.lessonplanner.bilingual sqlite3 databases/lesson_planner.db '.tables' 2>&1"
Write-Host $tableCheck

