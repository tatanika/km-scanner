@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   KM Scanner - Local Server
echo ============================================
echo.
echo Server: http://localhost:8080
echo.
echo Your local IP addresses (open on phone):
ipconfig | findstr /i "IPv4"
echo.
echo Press Ctrl+C to stop.
echo.

python -m http.server 8080
