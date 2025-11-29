
$basePath = "D:\LP\frontend\src-tauri\gen\android\app\build\intermediates\merged_jni_libs"
$target = "aarch64-linux-android"
$replacement = "arm64-v8a"

Write-Host "Monitoring recursively in: $basePath"

while ($true) {
    $found = Get-ChildItem -Path $basePath -Recurse -Filter $target -Directory -ErrorAction SilentlyContinue
    
    foreach ($folder in $found) {
        Write-Host "Found incorrect folder at: $($folder.FullName)"
        $parentPath = $folder.Parent.FullName
        $newPath = Join-Path -Path $parentPath -ChildPath $replacement
        
        try {
            if (Test-Path $newPath) {
                Write-Host "Target $newPath exists, removing..."
                Remove-Item $newPath -Recurse -Force
            }
            Rename-Item $folder.FullName $replacement
            Write-Host "RENAMED to $replacement"
        } catch {
            Write-Host "Error renaming: $_"
        }
    }
    Start-Sleep -Milliseconds 200
}

