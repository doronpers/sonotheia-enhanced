@echo off
REM Quick start script for Sonotheia Enhanced (Windows)
REM Starts both backend and frontend services

echo ================================================
echo   Sonotheia Enhanced - Quick Start Script
echo ================================================
echo.

REM Check if Docker is available
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    where docker-compose >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [32m[OK] Docker detected - Using Docker setup[0m
        echo.
        
        echo Stopping any running containers...
        docker-compose down 2>nul
        
        echo Starting services with Docker Compose...
        docker-compose up --build -d
        
        echo.
        echo [32m[OK] Services started successfully![0m
        echo.
        echo Access the application:
        echo   - Frontend Dashboard: http://localhost:3000
        echo   - Backend API:        http://localhost:8000
        echo   - API Documentation:  http://localhost:8000/docs
        echo.
        echo To view logs: docker-compose logs -f
        echo To stop: docker-compose down
        goto :end
    )
)

echo [33m[WARNING] Docker not found - Using local setup[0m
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [31m[ERROR] Python 3 is required but not installed[0m
    exit /b 1
)

REM Check for Node/npm
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [31m[ERROR] Node.js is required but not installed[0m
    exit /b 1
)

echo [32m[OK] Python and Node.js detected[0m
echo.

REM Setup backend
echo Setting up backend...
cd backend

if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

echo   Activating virtual environment...
call venv\Scripts\activate.bat

echo   Installing Python dependencies...
pip install -q -r requirements.txt

echo   Starting backend server...
start /b cmd /c "uvicorn api.main:app --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1"

cd ..

REM Setup frontend
echo Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo   Installing npm dependencies...
    call npm install --legacy-peer-deps
)

echo   Starting frontend server...
set BROWSER=none
set PORT=3000
start /b cmd /c "npm start > ..\frontend.log 2>&1"

cd ..

echo.
echo [32m[OK] Services started successfully![0m
echo.
echo Access the application:
echo   - Frontend Dashboard: http://localhost:3000
echo   - Backend API:        http://localhost:8000
echo   - API Documentation:  http://localhost:8000/docs
echo.
echo To stop: run stop.bat or close this window
echo.
echo Logs are being written to backend.log and frontend.log

:end
pause
