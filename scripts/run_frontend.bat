@echo off
title NEXUS - Frontend Web UI (Port 5173)
echo Starting NEXUS Frontend...
cd /d "%~dp0..\nexus frontend"
npm run dev
pause
