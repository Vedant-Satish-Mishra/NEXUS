@echo off
title NEXUS - Master Launcher
echo ========================================================
echo   Launching NEXUS AI Cognitive Assistant System
echo ========================================================

:: 1. Start Qwen 3 4B if port 8080 is not listening
netstat -ano | findstr 127.0.0.1:8080 >nul
if %errorlevel% neq 0 (
    echo [1/3] Starting Local Qwen 3 4B Model Server (port 8080)...
    start "Qwen 3 4B Server" cmd /c "cd /d D:\own ai\Local_Qwen3_System\qwen 3 4b && call run.bat"
    timeout /t 3 /nobreak >nul
) else (
    echo [1/3] Qwen 3 4B Server is already running on port 8080.
)

:: 2. Start Backend
echo [2/3] Starting NEXUS Backend (port 8000)...
start "NEXUS Backend" cmd /c "cd /d %~dp0backend && call run.bat"

:: 3. Start Frontend
echo [3/3] Starting NEXUS Frontend (port 3000)...
start "NEXUS Frontend" cmd /c "cd /d %~dp0nexus frontend && call start.bat"

timeout /t 3 /nobreak >nul
echo ========================================================
echo   All services launched! Opening browser...
echo ========================================================
start http://localhost:3000
pause
