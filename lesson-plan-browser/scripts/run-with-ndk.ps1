[CmdletBinding()]
param(
    [ValidateSet("arm64", "armv7", "x86_64", "x86")]
    [string]$Target = "arm64",

    [switch]$Release,

    [string]$ApiUrl,

    [string]$DbPath = "..\data\lesson_planner.db",

    [string]$JsonSourcePath,

    [string]$CacheSourcePath
)

$script:ErrorActionPreference = "Stop"

$ndkCandidates = @(
    $env:ANDROID_NDK_HOME,
    'C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865',
    'C:\Users\rodri\AppData\Local\Android\Sdk\ndk\25.2.9519653'
)

$ndkRoot = $null
foreach ($candidate in $ndkCandidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $ndkRoot = $candidate
        break
    }
}

if (-not $ndkRoot) {
    Write-Error "Unable to locate an installed Android NDK"
    exit 2
}

$llvmBin = Join-Path $ndkRoot 'toolchains\llvm\prebuilt\windows-x86_64\bin'
$env:ANDROID_NDK_HOME = $ndkRoot
$env:NDK_HOME = $ndkRoot
$env:CC_aarch64_linux_android = Join-Path $llvmBin 'aarch64-linux-android33-clang.cmd'
Set-Item -Path Env:CC_aarch64-linux-android -Value $env:CC_aarch64_linux_android
$env:AR_aarch64_linux_android = Join-Path $llvmBin 'llvm-ar.exe'
Set-Item -Path Env:AR_aarch64-linux-android -Value $env:AR_aarch64_linux_android
$env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = $env:CC_aarch64_linux_android
$env:PATH = $llvmBin + ';' + $env:PATH

Write-Host ("NDK configured: {0}" -f $ndkRoot)
Write-Host ("CC={0}" -f $env:CC_aarch64_linux_android)
Write-Host ("AR={0}" -f $env:AR_aarch64_linux_android)

$resolvedDbPath = $null
if ($DbPath) {
    if (-not (Test-Path $DbPath)) {
        throw "Database file not found at $DbPath"
    }
    $resolvedDbPath = (Resolve-Path $DbPath).Path
    Write-Host ("Bundling database: {0}" -f $resolvedDbPath)
}

$resolvedJsonSource = $null
if ($JsonSourcePath) {
    if (-not (Test-Path $JsonSourcePath)) {
        throw "Lesson JSON source not found at $JsonSourcePath"
    }
    $resolvedJsonSource = (Resolve-Path $JsonSourcePath).Path
    Write-Host ("Bundling lesson JSON from: {0}" -f $resolvedJsonSource)
}

$resolvedCacheSource = $null
if ($CacheSourcePath) {
    if (-not (Test-Path $CacheSourcePath)) {
        throw "Lesson cache source not found at $CacheSourcePath"
    }
    $resolvedCacheSource = (Resolve-Path $CacheSourcePath).Path
    Write-Host ("Bundling cached lesson plans from: {0}" -f $resolvedCacheSource)
}

$resolvedApiUrl = $ApiUrl
if (-not $resolvedApiUrl) {
    if ($env:VITE_ANDROID_API_BASE_URL) {
        $resolvedApiUrl = $env:VITE_ANDROID_API_BASE_URL
    } elseif ($env:VITE_API_BASE_URL) {
        $resolvedApiUrl = $env:VITE_API_BASE_URL
    } else {
        $resolvedApiUrl = "http://10.0.2.2:8000/api"
    }
}

$env:VITE_API_BASE_URL = $resolvedApiUrl
$env:VITE_ANDROID_API_BASE_URL = $resolvedApiUrl
$env:VITE_ENABLE_STANDALONE_DB = "true"
Write-Host ("API URL: {0}" -f $resolvedApiUrl)

Set-Location 'D:\LP\lesson-plan-browser'
.\scripts\build-android-offline.ps1 -Target $Target -Release:$Release -DbPath $resolvedDbPath -LessonJsonSource $resolvedJsonSource -CacheSourcePath $resolvedCacheSource
Write-Output ('exit:' + $LASTEXITCODE)
