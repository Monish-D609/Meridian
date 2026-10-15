@echo off
title Stopping Meridian Services
echo [*] Stopping Meridian processes on ports 8000 and 5173...

:: Kill processes on port 8000 (backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping backend process (PID %%a)...
    taskkill /F /PID %%a >nul 2>nul
)

:: Kill processes on port 5173 (frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo Stopping frontend process (PID %%a)...
    taskkill /F /PID %%a >nul 2>nul
)

echo [✓] Meridian services stopped.
timeout /t 2 >nul
