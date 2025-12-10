@echo off
echo Starting Sonotheia Forensic Viewer...
echo This will start a local web server to bypass CORS restrictions.
echo.

cd /d "%~dp0"
start "" "http://localhost:8088/forensic_viewer.html"
python -m http.server 8088

pause
