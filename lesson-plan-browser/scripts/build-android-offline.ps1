<#
    build-android-offline.ps1
    --------------------------
    Builds an Android APK without invoking `tauri android android-studio-script`.
    The script performs three critical steps the CLI usually handles for us:
      1. Rebuilds the Rust shared library so the latest `tauri.conf.json`
         and `tauri.android.conf.json` (which pins `devUrl` to `tauri://localhost`)
         get baked into the .so artifact.
      2. Copies the freshly-built frontend bundle into
         `src-tauri/gen/android/app/src/main/assets` (the location that the
         generated WebView loaders read from).
      3. Recreates the `.tauri` metadata that the CLI normally drops into the
         assets folder so the runtime knows it should stay offline.

    Usage:
        pwsh .\scripts\build-android-offline.ps1 [-Target arm64|armv7|x86_64|x86] [-Release] [-DbPath <path>]
#>
[CmdletBinding()]
param(
    [ValidateSet("arm64", "armv7", "x86_64", "x86")]
    [string]$Target = "arm64",

    [switch]$Release,

    [string]$DbPath,

    [string]$LessonJsonSource,

    [string]$CacheSourcePath
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    throw "Unable to locate frontend at '$frontendDir'. Run this script from the repo that contains frontend/."
}

$srcTauriDir = Join-Path $frontendDir "src-tauri"
$androidDir  = Join-Path $srcTauriDir "gen\android"

if (-not (Test-Path (Join-Path $androidDir "app\build.gradle.kts"))) {
    throw "Android project not found in '$androidDir'. Run `cd frontend && tauri android init` first."
}
$assetsDir   = Join-Path $androidDir "app\src\main\assets"
$distDir     = Join-Path $frontendDir "dist"

$profileName   = if ($Release) { "release" } else { "debug" }
$gradleVariant = if ($Release) { "Release" } else { "Debug" }

$targetMap = @{
    "arm64"  = @{ triple = "aarch64-linux-android"; abi = "arm64-v8a"; gradleTask = "assembleArm64$gradleVariant"; rustTask = "rustBuildArm64$gradleVariant"  }
    "armv7"  = @{ triple = "armv7-linux-androideabi"; abi = "armeabi-v7a"; gradleTask = "assembleArmv7$gradleVariant"; rustTask = "rustBuildArm$gradleVariant"    }
    "x86_64" = @{ triple = "x86_64-linux-android";   abi = "x86_64";     gradleTask = "assembleX86_64$gradleVariant"; rustTask = "rustBuildX86_64$gradleVariant" }
    "x86"    = @{ triple = "i686-linux-android";     abi = "x86";        gradleTask = "assembleX86$gradleVariant";    rustTask = "rustBuildX86$gradleVariant"    }
}

$selectedTarget = $targetMap[$Target]
if (-not $selectedTarget) {
    throw "Unsupported target $Target"
}

$resolvedDbPath = $null
if ($DbPath) {
    if (-not (Test-Path $DbPath)) {
        throw "Database file not found at $DbPath"
    }
    $resolvedDbPath = (Resolve-Path $DbPath).Path
}

$resolvedLessonJsonSource = $null
if ($LessonJsonSource) {
    if (-not (Test-Path $LessonJsonSource)) {
        throw "Lesson JSON source not found at $LessonJsonSource"
    }
    $resolvedLessonJsonSource = (Resolve-Path $LessonJsonSource).Path
}

$resolvedCacheSourcePath = $null
if ($CacheSourcePath) {
    if (-not (Test-Path $CacheSourcePath)) {
        throw "Lesson cache source not found at $CacheSourcePath"
    }
    $resolvedCacheSourcePath = (Resolve-Path $CacheSourcePath).Path
}

function Sanitize-PathSegment {
    param([string]$Segment)
    if ([string]::IsNullOrWhiteSpace($Segment)) {
        return "default"
    }
    return ($Segment -replace '[^a-zA-Z0-9._-]', '_')
}

function Get-WeekLabelFromFile {
    param([System.IO.FileInfo]$FileInfo)

    if (-not $FileInfo) {
        return $null
    }

    try {
        $jsonText = Get-Content -Path $FileInfo.FullName -Raw -ErrorAction Stop
        if (-not [string]::IsNullOrWhiteSpace($jsonText)) {
            $parsed = $jsonText | ConvertFrom-Json -ErrorAction Stop
            if ($parsed -and $parsed.metadata -and $parsed.metadata.week_of) {
                $weekValue = [string]$parsed.metadata.week_of
                if (-not [string]::IsNullOrWhiteSpace($weekValue)) {
                    return $weekValue.Trim()
                }
            }
        }
    } catch {
        # Fall back to folder names if parsing fails
    }

    if ($FileInfo.Directory -and -not [string]::IsNullOrWhiteSpace($FileInfo.Directory.Name)) {
        return $FileInfo.Directory.Name.Trim()
    }

    return $FileInfo.BaseName
}

function Get-PlanIdFromFile {
    param([System.IO.FileInfo]$FileInfo)

    if (-not $FileInfo) {
        return $null
    }

    try {
        $jsonText = Get-Content -Path $FileInfo.FullName -Raw -ErrorAction Stop
        if (-not [string]::IsNullOrWhiteSpace($jsonText)) {
            $parsed = $jsonText | ConvertFrom-Json -ErrorAction Stop
            if ($parsed) {
                $candidates = @()
                if ($parsed.PSObject.Properties.Name -contains "id") { $candidates += $parsed.id }
                if ($parsed.PSObject.Properties.Name -contains "plan_id") { $candidates += $parsed.plan_id }
                if ($parsed.PSObject.Properties.Name -contains "planId") { $candidates += $parsed.planId }
                if ($parsed.PSObject.Properties.Name -contains "metadata" -and $parsed.metadata) {
                    if ($parsed.metadata.PSObject.Properties.Name -contains "plan_id") { $candidates += $parsed.metadata.plan_id }
                    if ($parsed.metadata.PSObject.Properties.Name -contains "planId") { $candidates += $parsed.metadata.planId }
                }
                foreach ($candidate in $candidates) {
                    if ($candidate -and -not [string]::IsNullOrWhiteSpace([string]$candidate)) {
                        return [string]$candidate
                    }
                }
            }
        }
    } catch {
        # ignore parse errors and fall back to auto
    }

    return $null
}

function Get-LessonFileNames {
    param(
        [string]$WeekLabel,
        [string]$PlanId = "auto"
    )

    $primary = if ([string]::IsNullOrWhiteSpace($WeekLabel)) { "week" } else { $WeekLabel.Trim() }
    $alternates = @()
    if (-not [string]::IsNullOrWhiteSpace($primary)) {
        $alternates += $primary
        $sanitized = ($primary -replace '/', '-') -replace '\s+', ''
        if (-not [string]::IsNullOrWhiteSpace($sanitized) -and $sanitized -ne $primary) {
            $alternates += $sanitized
        }
    } else {
        $alternates += "week"
    }

    $encodedPlanId = if ([string]::IsNullOrWhiteSpace($PlanId)) { "auto" } else { [System.Uri]::EscapeDataString($PlanId.Trim()) }
    if ([string]::IsNullOrWhiteSpace($encodedPlanId)) {
        $encodedPlanId = "auto"
    }

    $fileNames = New-Object System.Collections.Generic.List[string]
    foreach ($value in $alternates) {
        $token = if ([string]::IsNullOrWhiteSpace($value)) { "week" } else { $value }
        $encoded = [System.Uri]::EscapeDataString($token)
        if ([string]::IsNullOrWhiteSpace($encoded)) {
            $encoded = "week"
        }
        $name = "${encoded}__${encodedPlanId}.json"
        if (-not $fileNames.Contains($name)) {
            $fileNames.Add($name)
        }
    }

    return $fileNames
}

function Copy-LessonPlanJson {
    param(
        [string]$SourceRoot,
        [string]$DestinationRoot,
        [string]$UserId,
        [string]$UserName
    )

    if (-not (Test-Path $SourceRoot)) {
        Write-Warning "Lesson plan source directory not found for $UserName ($SourceRoot)"
        return 0
    }

    $jsonFiles = Get-ChildItem -Path $SourceRoot -Recurse -Filter *.json -File -ErrorAction SilentlyContinue
    if (-not $jsonFiles -or $jsonFiles.Count -eq 0) {
        Write-Warning "No JSON files found for $UserName in $SourceRoot"
        return 0
    }

    $latestByWeek = @{}
    foreach ($file in $jsonFiles) {
        $weekLabel = Get-WeekLabelFromFile -FileInfo $file
        if ([string]::IsNullOrWhiteSpace($weekLabel)) {
            continue
        }
        $existing = $latestByWeek[$weekLabel]
        if (-not $existing -or $file.LastWriteTimeUtc -gt $existing.LastWriteTimeUtc) {
            $latestByWeek[$weekLabel] = $file
        }
    }

    if ($latestByWeek.Count -eq 0) {
        Write-Warning "Unable to derive week labels for $UserName lesson plans."
        return 0
    }

    [void][System.IO.Directory]::CreateDirectory($DestinationRoot)
    $userDir = Join-Path $DestinationRoot (Sanitize-PathSegment $UserId)
    [void][System.IO.Directory]::CreateDirectory($userDir)

    $copied = 0
    foreach ($entry in $latestByWeek.GetEnumerator()) {
        $weekLabel = $entry.Key
        $fileInfo = $entry.Value
        $planId = Get-PlanIdFromFile -FileInfo $fileInfo
        if (-not $planId) {
            $planId = "auto"
        }
        $fileNames = Get-LessonFileNames -WeekLabel $weekLabel -PlanId $planId
        foreach ($destName in $fileNames) {
            $destPath = Join-Path $userDir $destName
            Copy-Item -Path $fileInfo.FullName -Destination $destPath -Force
        }
        $copied++
    }

    Write-Host ("Copied {0} lesson JSON files for {1}" -f $copied, $UserName) -ForegroundColor Green
    return $copied
}

function Sync-LessonPlanPayload {
    param(
        [string]$SourceRoot,
        [string]$DestinationRoot
    )

    $mappings = @(
        @{
            UserId = "04fe8898-cb89-4a73-affb-64a97a98f820"
            UserName = "Wilson Rodrigues"
            PreferredFolders = @("Lesson Plan")
            Keywords = @("wilson", "lesson plan")
        },
        @{
            UserId = "29fa9ed7-3174-4999-86fd-40a542c28cff"
            UserName = "Daniela Silva"
            PreferredFolders = @("Daniela LP")
            Keywords = @("daniela")
        }
    )

    $totalCopied = 0
    $userDirs = @()
    try {
        $userDirs = Get-ChildItem -Path $SourceRoot -Directory -ErrorAction Stop
    } catch {
        Write-Warning "Unable to enumerate lesson plan source root '$SourceRoot': $_"
    }

    foreach ($mapping in $mappings) {
        $sourceCandidate = $null
        foreach ($preferred in $mapping.PreferredFolders) {
            $candidatePath = Join-Path $SourceRoot $preferred
            if (Test-Path $candidatePath) {
                $sourceCandidate = $candidatePath
                break
            }
        }

        if (-not $sourceCandidate -and $userDirs) {
            foreach ($dir in $userDirs) {
                foreach ($keyword in $mapping.Keywords) {
                    if ($dir.Name -match $keyword) {
                        $sourceCandidate = $dir.FullName
                        break
                    }
                }
                if ($sourceCandidate) { break }
            }
        }

        if (-not $sourceCandidate) {
            Write-Warning "No lesson plan directory matched for $($mapping.UserName) under $SourceRoot"
            continue
        }

        $copied = Copy-LessonPlanJson -SourceRoot $sourceCandidate -DestinationRoot $DestinationRoot -UserId $mapping.UserId -UserName $mapping.UserName
        $totalCopied += $copied
    }

    return $totalCopied
}

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Action
    )

    Write-Host "[$Title]" -ForegroundColor Cyan
    & $Action
    Write-Host ""
}

# Step 1: Build the frontend bundle so `dist/` is up to date.
Invoke-Step "1/7 Build frontend (npm run build:skip-check)" {
    Push-Location $frontendDir
    try {
        npm run build:skip-check | Write-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Vite build failed (npm run build:skip-check)"
        }
    }
    finally {
        Pop-Location
    }
    if (-not (Test-Path $distDir)) {
        throw "Expected bundle folder '$distDir' was not produced"
    }
}

# Step 2: Build the Rust shared library so the latest config (tauri://localhost devUrl) is embedded.
Invoke-Step "2/7 Build Rust target $($selectedTarget.triple) ($profileName)" {
    Push-Location $srcTauriDir
    try {
        $cargoArgs = @("build", "--target", $selectedTarget.triple)
        if ($Release) { $cargoArgs += "--release" }
        cargo @cargoArgs | Write-Host
        if ($LASTEXITCODE -ne 0) {
            throw "cargo build failed for $($selectedTarget.triple)"
        }
    }
    finally {
        Pop-Location
    }
}

# Step 3: Copy the freshly built .so into jniLibs (so Gradle no longer calls Tauri).
Invoke-Step "3/7 Sync liblesson_plan_browser/*.so into jniLibs" {
    $candidateLibs = @(
        "libbilingual_lesson_planner.so",
        "liblesson_plan_browser.so"
    )
    $libSource = $null
    $libName   = $null
    foreach ($candidate in $candidateLibs) {
        $path = Join-Path $srcTauriDir "target\$($selectedTarget.triple)\$profileName\$candidate"
        if (Test-Path $path) {
            $libSource = $path
            $libName   = $candidate
            break
        }
    }
    if (-not $libSource) {
        throw "Could not find a compiled .so in target\$($selectedTarget.triple)\$profileName. Run cargo build manually to verify toolchains."
    }

    $jniDir = Join-Path $androidDir "app\src\main\jniLibs\$($selectedTarget.abi)"
    New-Item -ItemType Directory -Force -Path $jniDir | Out-Null
    $destPath = Join-Path $jniDir $libName
    $maxAttempts = 5
    $success = $false

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            if (Test-Path $destPath) {
                Remove-Item $destPath -Force -ErrorAction Stop
            }
            Copy-Item $libSource $destPath -Force -ErrorAction Stop
            $success = $true
            break
        } catch {
            if ($attempt -eq $maxAttempts) {
                Write-Error "Failed to copy $libName -> $jniDir after $maxAttempts attempts. Last error: $_"
                throw
            }
            Start-Sleep -Milliseconds 300
        }
    }

    if ($success) {
        Write-Host "Copied $libName -> $jniDir" -ForegroundColor Green
    }
}

# Step 4: Copy the built dist/ assets and bundle offline data payloads.
Invoke-Step "4/7 Copy dist + data -> app/src/main/assets" {
    if (Test-Path $assetsDir) {
        Remove-Item $assetsDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
    Copy-Item -Path (Join-Path $distDir "*") -Destination $assetsDir -Recurse -Force
    Write-Host "Assets copied to $assetsDir" -ForegroundColor Green

    if ($resolvedDbPath) {
        $dbAssetsDir = Join-Path $assetsDir "databases"
        New-Item -ItemType Directory -Force -Path $dbAssetsDir | Out-Null
        Copy-Item $resolvedDbPath (Join-Path $dbAssetsDir "lesson_planner.db") -Force
        Write-Host ("Bundled database asset from {0}" -f $resolvedDbPath) -ForegroundColor Green
    }

    $lessonPlanAssetsDir = Join-Path $assetsDir "lesson-plans"
    if ($resolvedCacheSourcePath) {
        New-Item -ItemType Directory -Force -Path $lessonPlanAssetsDir | Out-Null
        Copy-Item -Path (Join-Path $resolvedCacheSourcePath '*') -Destination $lessonPlanAssetsDir -Recurse -Force
        Write-Host ("Copied cached lesson plans from {0}" -f $resolvedCacheSourcePath) -ForegroundColor Green
    } elseif ($resolvedLessonJsonSource) {
        $copiedCount = Sync-LessonPlanPayload -SourceRoot $resolvedLessonJsonSource -DestinationRoot $lessonPlanAssetsDir
        if ($copiedCount -eq 0) {
            Write-Warning "Lesson plan source was provided but no files were bundled."
        }
    } else {
        New-Item -ItemType Directory -Force -Path $lessonPlanAssetsDir | Out-Null
        Write-Host "Lesson plan source not provided; created empty assets\lesson-plans directory." -ForegroundColor Yellow
    }
}

# Step 5: Recreate the `.tauri` offline metadata inside assets.
Invoke-Step "5/7 Populate assets/.tauri configs" {
    $tauriConfigDir = Join-Path $assetsDir ".tauri"
    [void][System.IO.Directory]::CreateDirectory($tauriConfigDir)

    $tauriConfPath = Join-Path $srcTauriDir "tauri.conf.json"
    if (Test-Path $tauriConfPath) {
        Copy-Item $tauriConfPath (Join-Path $tauriConfigDir "tauri.conf.json") -Force
    }

    $tauriAndroidConfPath = Join-Path $srcTauriDir "tauri.android.conf.json"
    $offlineUrl = "tauri://localhost"
    if (Test-Path $tauriAndroidConfPath) {
        Copy-Item $tauriAndroidConfPath (Join-Path $tauriConfigDir "tauri.android.conf.json") -Force
        try {
            $androidConfig = Get-Content $tauriAndroidConfPath -Raw | ConvertFrom-Json
            if ($androidConfig.build.devUrl) {
                $offlineUrl = $androidConfig.build.devUrl
            }
        }
        catch {
            Write-Warning "Unable to parse $tauriAndroidConfPath, defaulting devUrl to tauri://localhost"
        }
    }

    $androidRuntimeConfig = @{
        build = @{
            devUrl = $offlineUrl
            mode   = "offline"
        }
    }
    $androidConfigPath = Join-Path $tauriConfigDir "android-config.json"
    $androidRuntimeConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $androidConfigPath -Encoding UTF8
    Write-Host ("Wrote assets/.tauri/android-config.json (devUrl={0})" -f $offlineUrl) -ForegroundColor Green

    if (-not (Test-Path $androidConfigPath)) {
        throw "Failed to create assets/.tauri metadata"
    }
}

# Step 6: Mirror the configs at the root of assets so they survive any tooling quirks.
Invoke-Step "6/7 Mirror tauri configs at assets root" {
    foreach ($configName in @("tauri.conf.json", "tauri.android.conf.json")) {
        $sourcePath = Join-Path $srcTauriDir $configName
        if (Test-Path $sourcePath) {
            Copy-Item $sourcePath (Join-Path $assetsDir $configName) -Force
        }
    }
    Copy-Item (Join-Path $assetsDir ".tauri\android-config.json") (Join-Path $assetsDir "android-config.json") -Force
}

# Step 7: Run Gradle but skip the rustBuild* tasks so we do not trigger the WebSocket code-path again.
Invoke-Step "7/7 Gradle $($selectedTarget.gradleTask) (-x rustBuild…)" {
    Push-Location $androidDir
    try {
        $incrementalDir = Join-Path $androidDir "app\build\intermediates\incremental"
        if (Test-Path $incrementalDir) {
            Write-Host "Cleaning incremental build artifacts..." -ForegroundColor Yellow
            Remove-Item $incrementalDir -Recurse -Force -ErrorAction SilentlyContinue
        }

        $gradleArgs = @($selectedTarget.gradleTask, "-x", $selectedTarget.rustTask, "-x", "rustBuildUniversal$gradleVariant")
        .\gradlew.bat @gradleArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Gradle build failed (args: $gradleArgs)"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host "Offline Android build finished successfully." -ForegroundColor Green

