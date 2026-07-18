@echo off
title Jobexa Web Dashboard
echo ===========================================
echo Starting Jobexa Frontend Web Dashboard...
echo ===========================================
cd /d "%~dp0"
python -m http.server 3000
pause
