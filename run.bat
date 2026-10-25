@echo off
title NEXUS - FastAPI Backend (Port 8000)
cd /d "%~dp0backend"
echo ========================================================
echo   Starting NEXUS Backend on http://127.0.0.1:8000
echo ========================================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
