# Grade 2 Math — all nine units in tools/db/g2_math_corpus.py (hub: Grade 2 Mathematics
# Curriculum Guide, doc id 1Wb_ty4UKX6uWOuSP71yFxkuC5XOyCp6l1pKdEN5HQfw).
# 1) Re-scrapes each unit Google Doc (depth 4, --force) under reference_docs/scraped
# 2) Ingests each unit into data/curriculum.db via ingest_g2_math_corpus.py
#
# Prerequisites: valid OAuth (tools/scraper/credentials/). See tools/scraper/SETUP.md.
#
# Usage (repo root):
#   powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1
# Scrape only:
#   powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1 -ScrapeOnly
# Ingest only:
#   powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1 -IngestOnly
# Single unit (must match corpus unit_id):
#   powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1 -UnitId Math_2_U4_1x8ll9eW

param(
    [switch] $ScrapeOnly,
    [switch] $IngestOnly,
    [string] $UnitId = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if (-not $IngestOnly) {
    Write-Host "Scraping Grade 2 Math corpus units..." -ForegroundColor Cyan
    if ($UnitId) {
        python tools/scraper/scrape_g2_math_units.py --unit-id $UnitId
    } else {
        python tools/scraper/scrape_g2_math_units.py
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($ScrapeOnly) {
    Write-Host "Scrape-only done." -ForegroundColor Green
    exit 0
}

Write-Host "Ingesting Grade 2 Math corpus..." -ForegroundColor Cyan
if ($UnitId) {
    python tools/db/ingest_g2_math_corpus.py --unit-id $UnitId
} else {
    python tools/db/ingest_g2_math_corpus.py
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running curriculum DB verify..." -ForegroundColor Cyan
python tools/scraper/verify_curriculum_db.py
exit $LASTEXITCODE
