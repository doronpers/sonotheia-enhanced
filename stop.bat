@echo off
REM Stop script for Sonotheia Enhanced (Windows)

echo Stopping Sonotheia Enhanced services...

REM Check if Docker Compose is being used
docker-compose ps >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Stopping Docker containers...
    docker-compose down
    echo [32m[OK] Docker services stopped[0m
) else (
    REM Stop local processes
    echo Stopping backend server (port 8000)...
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>nul
    )
    
    echo Stopping frontend server (port 3000)...
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>nul
    )
    
    echo [32m[OK] Services stopped[0m
)

pause
