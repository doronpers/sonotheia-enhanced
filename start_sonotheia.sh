#!/bin/bash

# Sonotheia Enhanced - One-Click Launch Script
# Starts Backend and Frontend with Local Network Access

# Function to kill child processes on exit
cleanup() {
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C (SIGINT)
trap cleanup SIGINT

# 1. Detect Local IP
# Try en0 (WiFi on Mac) first, then fallback
LOCAL_IP=$(ipconfig getifaddr en0)
if [ -z "$LOCAL_IP" ]; then
    # Fallback to creating a dummy connection to 8.8.8.8 to find route
    LOCAL_IP=$(dscacheutil -q host -a name $(hostname) | grep "ip_address" | head -n 1 | awk '{print $2}')
fi

if [ -z "$LOCAL_IP" ]; then
    echo "Could not detect local IP. Defaulting to localhost."
    LOCAL_IP="localhost"
else
    echo "Detected Local IP: $LOCAL_IP"
fi

echo "=================================================="
echo "Starting Sonotheia Enhanced"
echo "Backend: http://$LOCAL_IP:8000"
echo "Frontend: http://$LOCAL_IP:3000"
echo "=================================================="

# 2. Start Backend
echo "Starting Backend..."
cd backend
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready (simple sleep for now)
sleep 2

# 3. Start Frontend
echo "Starting Frontend..."
cd frontend
# Ensure we use the correct Node version (v22)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
nvm use v22.21.1 > /dev/null 2>&1 || echo "Warning: Could not switch to Node v22.21.1"

# Set environment variables for React
export HOST=0.0.0.0
export REACT_APP_API_BASE="http://$LOCAL_IP:8000"
npm start &
FRONTEND_PID=$!
cd ..

# Keep script running
wait
