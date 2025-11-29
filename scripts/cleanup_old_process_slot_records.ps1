# PowerShell script to clean up old 'process_slot' performance metric records
# 
# Since we've replaced the top-level 'process_slot' tracking with detailed
# sub-operations (parse_*, llm_*, render_*), the old 'process_slot' records
# are no longer needed and clutter the analytics.

param(
    [switch]$DryRun,
    [switch]$Force
)

if (-not $DryRun -and -not $Force) {
    Write-Host "ERROR: Must specify either -DryRun (to preview) or -Force (to delete)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\scripts\cleanup_old_process_slot_records.ps1 -DryRun"
    Write-Host "  .\scripts\cleanup_old_process_slot_records.ps1 -Force"
    exit 1
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Cleanup Old 'process_slot' Records" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "Mode: DRY RUN (preview only)" -ForegroundColor Yellow
    python scripts/cleanup_old_process_slot_records.py --dry-run
} else {
    Write-Host "Mode: DELETE (permanent)" -ForegroundColor Red
    Write-Host ""
    Write-Host "WARNING: This will permanently delete all 'process_slot' records!" -ForegroundColor Red
    Write-Host "Press Ctrl+C to cancel, or Enter to continue..." -ForegroundColor Yellow
    $null = Read-Host
    
    python scripts/cleanup_old_process_slot_records.py --force
}

Write-Host ""

