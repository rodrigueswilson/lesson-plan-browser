$ImageName = "python-android-build"
$BinariesDir = "d:\LP\frontend\src-tauri\binaries"
$OutputFile = "python-sync-processor-aarch64-linux-android"
$LogFile = "d:\LP\backend\extract-log.txt"

"Starting extraction..." | Out-File -FilePath $LogFile

# Ensure binaries directory exists
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
    "Created binaries directory: $BinariesDir" | Out-File -FilePath $LogFile -Append
}

# Create container
"Creating container..." | Out-File -FilePath $LogFile -Append
$ContainerID = docker create $ImageName 2>&1 | Tee-Object -FilePath $LogFile -Append
$ContainerID = $ContainerID.Trim()
"Container ID: $ContainerID" | Out-File -FilePath $LogFile -Append

if (-not $ContainerID) {
    "ERROR: No container ID returned" | Out-File -FilePath $LogFile -Append
    exit 1
}

# Extract binary
"Extracting binary..." | Out-File -FilePath $LogFile -Append
$TargetPath = Join-Path $BinariesDir $OutputFile
docker cp "${ContainerID}:/app/python-sync-processor" $TargetPath 2>&1 | Out-File -FilePath $LogFile -Append

# Cleanup
docker rm $ContainerID 2>&1 | Out-File -FilePath $LogFile -Append

# Verify
if (Test-Path $TargetPath) {
    $FileInfo = Get-Item $TargetPath
    $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    "SUCCESS: Binary extracted - Size: $SizeMB MB" | Out-File -FilePath $LogFile -Append
    "Location: $TargetPath" | Out-File -FilePath $LogFile -Append
} else {
    "ERROR: Binary not found after extraction" | Out-File -FilePath $LogFile -Append
}

Get-Content $LogFile

