# view_scraping_history.ps1
$ErrorActionPreference = "Stop"
$CacheDir = ".\cloud_run\data\cache"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   Forma OS - Intelligence Web Scraping History      " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $CacheDir)) {
    Write-Host "No scraping history found yet. Prepare a match in Forma OS to start scraping!" -ForegroundColor Yellow
    exit
}

# Filter out the final AI profiles/gaps and only show the raw scraped news JSONs
$files = Get-ChildItem -Path $CacheDir -Filter "*.json" | Where-Object { $_.Name -notmatch "^profiles_" -and $_.Name -notmatch "^gaps_" }

if ($files.Count -eq 0) {
    Write-Host "No raw news scrapes found in cache." -ForegroundColor Yellow
    exit
}

Write-Host "Found $($files.Count) complete Intelligence Scrapes:`n" -ForegroundColor Green

foreach ($file in $files) {
    try {
        $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
        $scrapedAt = $content.scraped_at
        
        $teamArticles = 0
        if ($null -ne $content.team_articles) {
            $teamArticles = $content.team_articles.Count
        }

        $playerNames = @()
        $playerArticleCount = 0
        if ($null -ne $content.player_articles) {
            $playerNames = $content.player_articles.psobject.properties.name
            foreach ($prop in $content.player_articles.psobject.properties) {
                $playerArticleCount += $prop.Value.Count
            }
        }

        $sources = ""
        if ($null -ne $content.sources_used) {
            $sources = $content.sources_used -join ", "
        }
        
        $nameParts = $file.Name.Replace(".json", "").Split("__")
        $team = $nameParts[0].Replace("_", " ").ToUpper()
        $date = if ($nameParts.Length -gt 1) { $nameParts[1].Replace("_", "-") } else { "General" }

        Write-Host "> OPPONENT: $team" -ForegroundColor Yellow
        Write-Host "  Match Date: $date" -ForegroundColor DarkGray
        Write-Host "  Scraped At: $scrapedAt" -ForegroundColor DarkGray
        Write-Host "  Sources:    $sources" -ForegroundColor Cyan
        Write-Host "  Intelligence Collected:" -ForegroundColor White
        Write-Host "    - $teamArticles team-level articles"
        Write-Host "    - $playerArticleCount individual player articles across $($playerNames.Count) key players"
        Write-Host "-----------------------------------------------------" -ForegroundColor DarkGray
    } catch {
        # Skip files that might not be news scrape format
    }
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "LIVE SCRAPING VIEW:" -ForegroundColor White
Write-Host "To see the web scraping happen LIVE in real-time, just look at the green Backend PowerShell window (started via run_forma_os.ps1) while you click 'Prepare Match' in the app. I have injected a live stream logger so you can watch it extract data live!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
