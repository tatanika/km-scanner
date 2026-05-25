@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo Starting HTTPS server for KM Scanner...
echo.
python start_https.py
pause
