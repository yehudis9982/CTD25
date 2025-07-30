@echo off
echo ========================================
echo       Chess Game - Client-Server Demo
echo ========================================
echo.
echo This will start both server and client
echo Press Ctrl+C to stop
echo.
pause

echo Starting Chess Server...
start "Chess Server" cmd /k "python run_server.py"

echo Waiting for server to start...
timeout /t 3 /nobreak > nul

echo Starting Chess Client...
start "Chess Client" cmd /k "python run_client.py"

echo.
echo Both server and client are now running!
echo Close this window when done.
pause