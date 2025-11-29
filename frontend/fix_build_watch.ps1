
$watchPath = "D:\LP\frontend\src-tauri\gen\android\app\build\intermediates\merged_jni_libs\universalDebug\mergeUniversalDebugJniLibFolders"
$target = "aarch64-linux-android"
$replacement = "arm64-v8a"

Write-Host "Monitoring for folder: $target in $watchPath..."

while ($true) {
    if (Test-Path "$watchPath\$target") {
        Write-Host "Found incorrect folder! Renaming..."
        try {
            if (Test-Path "$watchPath\$replacement") {
                Remove-Item "$watchPath\$replacement" -Recurse -Force
            }
            Rename-Item "$watchPath\$target" "$replacement"
            Write-Host "FIX APPLIED SUCCESSFULLY!"
            break
        } catch {
            Write-Host "Error renaming: $_"
        }
    }
    Start-Sleep -Milliseconds 500
}

