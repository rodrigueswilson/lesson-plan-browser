# Verify APK contains correct assets
$ErrorActionPreference = "Stop"

Write-Host "=== Verifying APK Assets ===" -ForegroundColor Cyan
Write-Host ""

$APKPath = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

if (-not (Test-Path $APKPath)) {
    Write-Host "ERROR: APK not found at: $APKPath" -ForegroundColor Red
    Write-Host "Please build the APK first." -ForegroundColor Yellow
    exit 1
}

Write-Host "APK found: $APKPath" -ForegroundColor Green
$APKInfo = Get-Item $APKPath
Write-Host "Size: $([math]::Round($APKInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
Write-Host "Last modified: $($APKInfo.LastWriteTime)" -ForegroundColor Gray
Write-Host ""

# Extract APK to temp directory
$TempDir = "$env:TEMP\apk_verify_$(Get-Random)"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Write-Host "Extracting APK..." -ForegroundColor Yellow

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($APKPath, $TempDir)
    Write-Host "APK extracted successfully" -ForegroundColor Green
    Write-Host ""
    
    # Check for HTML file
    $HtmlFiles = Get-ChildItem -Path $TempDir -Filter "index.html" -Recurse
    
    if ($HtmlFiles.Count -eq 0) {
        Write-Host "WARNING: No index.html found in APK!" -ForegroundColor Red
        Write-Host "Searching for all HTML files..." -ForegroundColor Yellow
        Get-ChildItem -Path $TempDir -Filter "*.html" -Recurse | ForEach-Object {
            Write-Host "  Found: $($_.FullName.Replace($TempDir, ''))" -ForegroundColor Gray
        }
    } else {
        Write-Host "=== HTML Files in APK ===" -ForegroundColor Cyan
        foreach ($HtmlFile in $HtmlFiles) {
            $RelativePath = $HtmlFile.FullName.Replace($TempDir, '')
            Write-Host "`n  $RelativePath" -ForegroundColor Yellow
            
            $Content = Get-Content $HtmlFile.FullName -Raw
            if ($Content -match 'src="/assets/index-(\w+)\.js"') {
                $Ref = $matches[0]
                $IsNew = $Ref -like "*TiTynWQK*"
                $IsOld = $Ref -like "*cOgOR3pL*"
                
                Write-Host "    References: $Ref" -ForegroundColor $(if ($IsNew) { "Green" } elseif ($IsOld) { "Red" } else { "Yellow" })
                
                if ($IsOld) {
                    Write-Host "    ❌ OLD FILE - APK contains outdated assets!" -ForegroundColor Red
                } elseif ($IsNew) {
                    Write-Host "    ✅ NEW FILE - APK has correct assets!" -ForegroundColor Green
                }
            } else {
                Write-Host "    ⚠️  Could not parse JavaScript reference" -ForegroundColor Yellow
            }
        }
    }
    
    # Check for JS files
    Write-Host "`n=== JavaScript Files in APK ===" -ForegroundColor Cyan
    $JSFiles = Get-ChildItem -Path $TempDir -Filter "index-*.js" -Recurse
    
    if ($JSFiles.Count -eq 0) {
        Write-Host "WARNING: No index-*.js files found!" -ForegroundColor Red
    } else {
        foreach ($JSFile in $JSFiles) {
            $RelativePath = $JSFile.FullName.Replace($TempDir, '')
            $SizeKB = [math]::Round($JSFile.Length / 1KB, 2)
            $IsNew = $JSFile.Name -like "*TiTynWQK*"
            $IsOld = $JSFile.Name -like "*cOgOR3pL*"
            
            Write-Host "  $($JSFile.Name) ($SizeKB KB)" -ForegroundColor $(if ($IsNew) { "Green" } elseif ($IsOld) { "Red" } else { "Gray" })
            Write-Host "    Path: $RelativePath" -ForegroundColor Gray
        }
        
        $NewFile = $JSFiles | Where-Object { $_.Name -like "*TiTynWQK*" }
        $OldFile = $JSFiles | Where-Object { $_.Name -like "*cOgOR3pL*" }
        
        if ($OldFile -and -not $NewFile) {
            Write-Host "`n❌ PROBLEM: APK only contains OLD JavaScript file!" -ForegroundColor Red
            Write-Host "The rebuild did not update the assets in the APK." -ForegroundColor Red
        } elseif ($NewFile -and $OldFile) {
            Write-Host "`n⚠️  WARNING: APK contains BOTH old and new JavaScript files!" -ForegroundColor Yellow
            Write-Host "This suggests incomplete cleanup." -ForegroundColor Yellow
        } elseif ($NewFile -and -not $OldFile) {
            Write-Host "`n✅ SUCCESS: APK contains only NEW JavaScript file!" -ForegroundColor Green
            Write-Host "If app still loads old file, it's a WebView cache issue." -ForegroundColor Yellow
        }
    }
    
} finally {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan

