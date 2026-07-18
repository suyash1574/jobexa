@echo off
title Jobexa Telegram Bot
echo ===========================================
echo Starting Jobexa Telegram Bot...
echo ===========================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=.
python bot.py
pause
