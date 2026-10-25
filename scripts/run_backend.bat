@echo off
title NEXUS - Backend Server (Port 8000)
echo Starting NEXUS FastAPI Backend...
cd /d "%~dp0..\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
