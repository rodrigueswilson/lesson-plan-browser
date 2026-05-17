# Grade 2 Math — Unit 1 only (Adding, Subtracting and Working With Data).
# For **all registry-backed Grade 2 Math units** (1, 3, 4, 6, 7), use:
#   powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1
#
# 1) Re-scrapes the unit Google Doc and linked resources under reference_docs/scraped
# 2) Re-ingests lessons into data/curriculum.db (CURRICULUM_DB_PATH if set)
#
# Prerequisites:
# - Valid OAuth: tools/scraper/credentials/credentials.json + token.json
# - If you see invalid_grant / expired token: delete tools/scraper/credentials/token.json and run
#   step 1 only; a browser window will open for re-consent.
#
# Usage (from repo root):
#   powershell -File tools/scraper/grade2_math_unit1_scrape_and_ingest.ps1
# Scrape only:
#   powershell -File tools/scraper/grade2_math_unit1_scrape_and_ingest.ps1 -ScrapeOnly
# Ingest only (uses Drive DOCX export; needs valid token):
#   powershell -File tools/scraper/grade2_math_unit1_scrape_and_ingest.ps1 -IngestOnly

param(
    [switch] $ScrapeOnly,
    [switch] $IngestOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

$UnitDocId = "15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU"

if (-not $IngestOnly) {
    Write-Host "Scraping unit doc $UnitDocId (depth 4, --force)..." -ForegroundColor Cyan
    python -m tools.scraper.main $UnitDocId --depth 4 --out reference_docs/scraped --force
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($ScrapeOnly) {
    Write-Host "Scrape-only done." -ForegroundColor Green
    exit 0
}

Write-Host "Ingesting into curriculum.db..." -ForegroundColor Cyan
python tools/db/ingest_wave_unit.py `
    --unit-id Math_2_U1_15E1iQ_x `
    --grade 2 `
    --subject Math `
    --unit-number 1 `
    --title "Grade 2 Unit 1: Adding, Subtracting and Working With Data" `
    --doc-id $UnitDocId

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running curriculum DB verify (data checks)..." -ForegroundColor Cyan
python tools/scraper/verify_curriculum_db.py
exit $LASTEXITCODE
