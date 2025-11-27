@echo off
REM Stop script for Sonotheia Enhanced (Windows)

echo Stopping Sonotheia Enhanced services...

REM Project name (matches .env COMPOSE_PROJECT_NAME)
set PROJECT_NAME=sonotheia-treehorn

REM Check if Docker Compose is being used (try v2 first, then v1)
docker compose -p %PROJECT_NAME% ps >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Stopping Docker containers...
    docker compose -p %PROJECT_NAME% down
    echo [32m[OK] Docker services stopped[0m
    goto :end
)

docker-compose -p %PROJECT_NAME% ps >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Stopping Docker containers...
    docker-compose -p %PROJECT_NAME% down
    echo [32m[OK] Docker services stopped[0m
    goto :end
)

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

:end
pause
