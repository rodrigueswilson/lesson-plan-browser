Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Show-Step {
  param(
    [Parameter(Mandatory = $true)]
    [int] $Number,
    [Parameter(Mandatory = $true)]
    [string] $Message
  )

  Write-Host ""
  Write-Host ("STEP {0}: {1}" -f $Number, $Message) -ForegroundColor Cyan
}

function Resolve-PathSafe {
  param(
    [Parameter(Mandatory = $true)]
    [string] $Path
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Path not found: $Path"
  }

  return (Resolve-Path -LiteralPath $Path).Path
}

function Merge-Objects {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject] $Target,
    [Parameter(Mandatory = $true)]
    [pscustomobject] $Source
  )

  foreach ($prop in $Source.PSObject.Properties) {
    $name = $prop.Name
    $value = $prop.Value

    if ($null -eq $value) {
      $Target.PSObject.Properties.Remove($name) | Out-Null
      continue
    }

    if (($value -is [System.Management.Automation.PSObject]) -and ($Target.PSObject.Properties.Name -contains $name) -and ($Target.$name -is [System.Management.Automation.PSObject])) {
      Merge-Objects -Target $Target.$name -Source $value
    } else {
      $Target | Add-Member -NotePropertyName $name -NotePropertyValue $value -Force
    }
  }
}

$repoRoot = Resolve-PathSafe (Join-Path $PSScriptRoot '..')
$projectRoot = Resolve-PathSafe (Join-Path $repoRoot 'lesson-plan-browser\frontend')
$srcTauriDir = Resolve-PathSafe (Join-Path $projectRoot 'src-tauri')
$androidScaffold = Resolve-PathSafe (Join-Path $srcTauriDir 'gen\android')
$distDir = Join-Path $projectRoot 'dist'
$assetsRoot = Join-Path $androidScaffold 'app\src\main\assets'
$assetsDir = Join-Path $assetsRoot 'assets'
$jniArm64Dir = Join-Path $androidScaffold 'app\src\main\jniLibs\arm64-v8a'
$targetTriple = 'aarch64-linux-android'
$profile = 'release'
$libName = 'liblesson_plan_browser.so'
$libSource = Join-Path $srcTauriDir "target\$targetTriple\$profile\$libName"
$apkPath = Join-Path $androidScaffold 'app\build\outputs\apk\arm64\debug\app-arm64-debug.apk'
$baseTauriConfPath = Join-Path $srcTauriDir 'tauri.conf.json'
$androidTauriConfPath = Join-Path $srcTauriDir 'tauri.android.conf.json'
$generatedTauriConfPath = Join-Path $assetsRoot 'tauri.conf.json'

Write-Host "Frontend root: $projectRoot" -ForegroundColor Cyan
Write-Host "Android scaffold: $androidScaffold" -ForegroundColor Cyan

Show-Step -Number 1 -Message "Building frontend bundle (npm run build:tauri)"
Push-Location $projectRoot
try {
  npm run build:tauri
} finally {
  Pop-Location
}

if (-not (Test-Path -LiteralPath $distDir)) {
  throw "Frontend build failed: dist folder not found at $distDir"
}

Show-Step -Number 2 -Message "Checking cargo-ndk installation"
$cargoNdk = Get-Command cargo-ndk -ErrorAction SilentlyContinue
if (-not $cargoNdk) {
  Write-Host "cargo-ndk not found; installing via 'cargo install cargo-ndk'..." -ForegroundColor Yellow
  cargo install cargo-ndk
} else {
  Write-Host "cargo-ndk already installed at $($cargoNdk.Source)" -ForegroundColor Green
}

Show-Step -Number 3 -Message "Building Rust library for arm64-v8a (cargo ndk --target arm64-v8a --platform 26 --release build)"
Push-Location $srcTauriDir
try {
  cargo ndk --target arm64-v8a --platform 26 --release build
} finally {
  Pop-Location
}

if (-not (Test-Path -LiteralPath $libSource)) {
  throw "Rust build failed: $libName not found at $libSource"
}

Show-Step -Number 4 -Message "Copying $libName into Android jniLibs"
New-Item -ItemType Directory -Force -Path $jniArm64Dir | Out-Null
Copy-Item -Path $libSource -Destination (Join-Path $jniArm64Dir $libName) -Force

Show-Step -Number 5 -Message "Syncing dist assets into Android project"
if (Test-Path -LiteralPath $assetsDir) {
  Remove-Item $assetsDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
$distAssets = Join-Path $distDir 'assets'
if (Test-Path -LiteralPath $distAssets) {
  Copy-Item -Path (Join-Path $distAssets '*') -Destination $assetsDir -Recurse -Force
}
Copy-Item -Path (Join-Path $distDir 'index.html') -Destination $assetsRoot -Force

if (-not (Test-Path -LiteralPath $baseTauriConfPath)) {
  throw "Expected Tauri config at $baseTauriConfPath"
}

Show-Step -Number 6 -Message "Generating tauri.conf.json for Android assets"
$baseConfig = Get-Content -Raw -Path $baseTauriConfPath | ConvertFrom-Json
if (-not $baseConfig.build) {
  $baseConfig | Add-Member -NotePropertyName build -NotePropertyValue ([pscustomobject]@{}) -Force
}

if (Test-Path -LiteralPath $androidTauriConfPath) {
  $androidConfig = Get-Content -Raw -Path $androidTauriConfPath | ConvertFrom-Json
  Merge-Objects -Target $baseConfig -Source $androidConfig
}

$baseConfig.build.devUrl = "tauri://localhost"
$baseConfig | ConvertTo-Json -Depth 64 | Out-File -FilePath $generatedTauriConfPath -Encoding utf8

Show-Step -Number 7 -Message "Running Gradle assembleArm64Debug (--info, skipping rust tasks)"
Push-Location $androidScaffold
try {
  & .\gradlew.bat `
    assembleArm64Debug `
    --info `
    -PabiList=arm64-v8a `
    -ParchList=arm64 `
    -PtargetList=aarch64 `
    -x rustBuildArm64Debug `
    -x rustBuildUniversalDebug
} finally {
  Pop-Location
}

if (Test-Path -LiteralPath $apkPath) {
  Write-Host ""
  Write-Host "Success! APK created at:" -ForegroundColor Green
  Write-Host "  $apkPath" -ForegroundColor Green
} else {
  throw "Gradle finished but app-arm64-debug.apk was not found at $apkPath"
}




