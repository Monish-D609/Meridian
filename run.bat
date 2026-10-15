@echo off
title Meridian — LLM Evaluation & Benchmarking Platform Launcher
setlocal enabledelayedexpansion

echo ======================================================================
echo           MERIDIAN - LLM EVALUATION & BENCHMARKING PLATFORM
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your PATH!
    echo Please install Python 3.10+ and add it to your system PATH.
    pause
    exit /b 1
)

:: Check Node/pnpm
set "PKG_RUNNER=npm"
where pnpm >nul 2>nul
if %errorlevel% equ 0 (
    set "PKG_RUNNER=pnpm"
)

echo [*] Starting Backend Service on http://127.0.0.1:8000 ...
start "Meridian Backend (FastAPI)" cmd /k "cd /d "%ROOT_DIR%backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

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
