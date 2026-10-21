# Meridian — LLM Evaluation & Benchmarking Platform Launcher
$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          MERIDIAN - LLM EVALUATION & BENCHMARKING PLATFORM          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 1. Detect Python Executable
$PyCmd = $null
$LocalVenv = Join-Path $RootDir "backend\venv\Scripts\python.exe"
$AnacondaPy = "C:\ProgramData\anaconda3\python.exe"

if (Test-Path $LocalVenv) {
    $PyCmd = $LocalVenv
} elseif ((Test-Path $AnacondaPy) -and (& $AnacondaPy -c "import pydantic_settings, fastapi" 2>$null; $LASTEXITCODE -eq 0)) {
    $PyCmd = $AnacondaPy
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PyPath = (Get-Command python).Source
    # Check if system python has dependencies; if not and Anaconda exists, prefer Anaconda
    & $PyPath -c "import pydantic_settings, fastapi" 2>$null
    if ($LASTEXITCODE -ne 0 -and (Test-Path $AnacondaPy)) {
        $PyCmd = $AnacondaPy
    } else {
        $PyCmd = $PyPath
    }
}

if (-not $PyCmd) {
    Write-Host "[ERROR] Python was not found in your PATH or known directories!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add it to your PATH." -ForegroundColor Yellow
    exit 1
}

# 2. Check dependencies
Write-Host "[*] Checking backend environment with $PyCmd..." -ForegroundColor Yellow
& $PyCmd -c "import pydantic_settings, fastapi, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[*] Installing missing backend dependencies..." -ForegroundColor Yellow
    $ReqPath = Join-Path $RootDir "backend\requirements.txt"
    & $PyCmd -m pip install -r $ReqPath
}

# 3. Determine package runner (pnpm or npm)
$PkgRunner = "npm"
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $PkgRunner = "pnpm"
}

$FrontendPath = Join-Path $RootDir "frontend"
$NodeModulesPath = Join-Path $FrontendPath "node_modules"
if (-not (Test-Path $NodeModulesPath)) {
    Write-Host "[*] Installing frontend packages..." -ForegroundColor Yellow
    Start-Process cmd.exe -ArgumentList "/c cd /d `"$FrontendPath`" && $PkgRunner install" -Wait
}

# 4. Start Backend
Write-Host "[*] Starting Backend Service on http://127.0.0.1:8000 ..." -ForegroundColor Green
$BackendPath = Join-Path $RootDir "backend"
Start-Process cmd.exe -ArgumentList "/k cd /d `"$BackendPath`" && `"$PyCmd`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

# 5. Start Frontend
Write-Host "[*] Starting Frontend Service on http://localhost:5173 ..." -ForegroundColor Green
Start-Process cmd.exe -ArgumentList "/k cd /d `"$FrontendPath`" && $PkgRunner run dev" -WindowStyle Normal

Start-Sleep -Seconds 3

# 6. Open default browser
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
