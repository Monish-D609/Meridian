# Meridian — LLM Evaluation & Benchmarking Platform Launcher
$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          MERIDIAN - LLM EVALUATION & BENCHMARKING PLATFORM          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python was not found in your PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add it to your PATH." -ForegroundColor Yellow
    exit 1
}

# Determine package runner (pnpm or npm)
$PkgRunner = "npm"
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $PkgRunner = "pnpm"
}

# Start Backend
Write-Host "[*] Starting Backend Service on http://127.0.0.1:8000 ..." -ForegroundColor Green
$BackendPath = Join-Path $RootDir "backend"
Start-Process cmd.exe -ArgumentList "/k cd /d `"$BackendPath`" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "[*] Starting Frontend Service on http://localhost:5173 ..." -ForegroundColor Green
$FrontendPath = Join-Path $RootDir "frontend"
Start-Process cmd.exe -ArgumentList "/k cd /d `"$FrontendPath`" && $PkgRunner run dev" -WindowStyle Normal

Start-Sleep -Seconds 3

# Open default browser
Write-Host "[*] Opening application in your default browser..." -ForegroundColor Green
Start-Process "http://localhost:5173/"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Meridian is running!" -ForegroundColor Green
Write-Host ""
Write-Host "  - Web UI:      http://localhost:5173/" -ForegroundColor White
Write-Host "  - Backend API: http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "  - API Docs:    http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Keep the two opened terminal windows running while using the app." -ForegroundColor Yellow
Write-Host "To stop everything, run 'stop.bat' or 'stop.ps1'." -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
