@echo off
title Jobexa Backend Server
echo ===========================================
echo Starting Jobexa FastAPI Backend Server...
echo ===========================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=.
python -m uvicorn src.main:app --reload --port 8000
pause
