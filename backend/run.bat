@echo off
title NEXUS - FastAPI Backend (Port 8000)
cd /d "%~dp0"
echo ========================================================
echo   NEXUS AI Cognitive Assistant - Backend Server
echo   Running on: http://127.0.0.1:8000
echo   API Docs:   http://127.0.0.1:8000/docs
echo ========================================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
