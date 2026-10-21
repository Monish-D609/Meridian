@echo off
title Meridian — LLM Evaluation & Benchmarking Platform Launcher
setlocal enabledelayedexpansion

echo ======================================================================
echo           MERIDIAN - LLM EVALUATION & BENCHMARKING PLATFORM
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 1. Detect Python Executable
set "PY_CMD="

:: Check local backend venv
if exist "%ROOT_DIR%backend\venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%backend\venv\Scripts\python.exe"
)

:: Check Anaconda installation
if not defined PY_CMD (
    if exist "C:\ProgramData\anaconda3\python.exe" (
        "C:\ProgramData\anaconda3\python.exe" -c "import pydantic_settings, fastapi" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PY_CMD=C:\ProgramData\anaconda3\python.exe"
        )
    )
)

:: Check system PATH python
if not defined PY_CMD (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PY_CMD=python"
    )
)

:: If PATH python is missing dependencies, try Anaconda if present
if defined PY_CMD (
    "%PY_CMD%" -c "import pydantic_settings, fastapi" >nul 2>nul
    if !errorlevel! neq 0 (
        if exist "C:\ProgramData\anaconda3\python.exe" (
            set "PY_CMD=C:\ProgramData\anaconda3\python.exe"
        )
    )
)

if not defined PY_CMD (
    echo [ERROR] Python was not found in your PATH or known directories!
    echo Please install Python 3.10+ and add it to your system PATH.
    pause
    exit /b 1
)

:: 2. Verify backend dependencies
echo [*] Checking backend environment with: !PY_CMD!
"%PY_CMD%" -c "import pydantic_settings, fastapi, uvicorn" >nul 2>nul
if !errorlevel! neq 0 (
    echo [*] Installing missing backend dependencies...
    "%PY_CMD%" -m pip install -r "%ROOT_DIR%backend\requirements.txt"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
)

:: 3. Check Node/pnpm
set "PKG_RUNNER=npm"
where pnpm >nul 2>nul
if %errorlevel% equ 0 (
    set "PKG_RUNNER=pnpm"
)

if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [*] Installing frontend packages...
    cmd /c "cd /d "%ROOT_DIR%frontend" && %PKG_RUNNER% install"
)

:: 4. Start Services
echo [*] Starting Backend Service on http://127.0.0.1:8000 ...
start "Meridian Backend (FastAPI)" cmd /k "cd /d "%ROOT_DIR%backend" && "%PY_CMD%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: Wait 2 seconds for backend to start
timeout /t 2 /nobreak >nul

echo [*] Starting Frontend Service on http://localhost:5173 ...
start "Meridian Frontend (Vite + React)" cmd /k "cd /d "%ROOT_DIR%frontend" && %PKG_RUNNER% run dev"

:: Wait 3 seconds then open browser
timeout /t 3 /nobreak >nul
echo [*] Opening application in your default web browser...
start http://localhost:5173/

echo.
echo ======================================================================
echo [SUCCESS] Meridian is running!
echo.
echo   - Web UI:      http://localhost:5173/
echo   - Backend API: http://127.0.0.1:8000/
echo   - API Docs:    http://127.0.0.1:8000/docs
echo.
echo Leave the two opened terminal windows running while using the app.
echo To stop everything, close both windows or run 'stop.bat'.
echo ======================================================================
echo.
pause
