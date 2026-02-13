@echo off
echo ========================================================
echo   SmartV2X-CP Ultra - One-Click Application
echo ========================================================
echo.

echo [1/3] Determining Network IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set IP=%%a
set IP=%IP: =%
echo       Your Local IP Address is: %IP%
echo.

echo [2/3] Checking Dependencies...
pip install -r requirements.txt > nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing dependencies (first time only)...
    pip install -r requirements.txt
) else (
    echo       Dependencies already installed.
)

echo [3/3] Starting Unified Server...
echo       (Edge + Backend + Dashboard all-in-one)
echo.
echo       Press Ctrl+C to stop.
echo.
echo ========================================================
echo   APPLICATION RUNNING!
echo ========================================================
echo.
echo   Open the application on your PC or Mobile Device at:
echo.
echo       http://%IP%:3000
echo.
echo   (Ensure your firewall allows python.exe on port 3000)
echo.

python unified_server.py
pause
