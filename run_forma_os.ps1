# run_forma_os.ps1
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "        Starting Forma OS System          " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start the FastAPI Backend
Write-Host "[1/2] Starting FastAPI Backend (cloud_run)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd cloud_run; Write-Host '--- Forma OS Backend ---' -ForegroundColor Green; uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

# Wait a few seconds to let the backend initialize before starting the frontend
Write-Host "Waiting 3 seconds for backend to initialize..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

# 2. Start the Flutter Frontend
Write-Host "[2/2] Starting Flutter Frontend (flutter_app)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd flutter_app; Write-Host '--- Forma OS Frontend ---' -ForegroundColor Yellow; flutter run -d chrome" -WindowStyle Normal

Write-Host ""
Write-Host "✅ Forma OS is now booting up!" -ForegroundColor Green
Write-Host "Two new terminal windows have been opened so you can monitor both the Backend logs and the Flutter processes in parallel." -ForegroundColor White
Write-Host "Close those windows to stop the processes when you are done." -ForegroundColor DarkGray
