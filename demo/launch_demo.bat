@echo off
echo Starting Sonotheia x Incode Demo Environment...
echo.

REM Check if Docker is available
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Starting with Docker...
    docker-compose up --build
) else (
    echo Starting locally...
    
    REM Start backend
    echo Starting backend on port 8000...
    cd backend
    start /B python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
    cd ..
    
    REM Start frontend if Node is available
    where npm >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Starting frontend on port 3000...
        cd frontend
        start /B npm start
        cd ..
    )
    
    echo.
    echo Services started!
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:3000
    echo API Docs: http://localhost:8000/docs
    echo.
    echo Press Ctrl+C to stop all services (you may need to manually kill python/node processes)
    
    pause
)
