#!/bin/bash
# Sonotheia Master Launch Script
# Launches Backend (sonotheia-enhanced) and Frontend (Website-Sonotheia)

# Configuration
# Adjust these paths if your folder structure differs
BACKEND_DIR="$(pwd)/backend"
FRONTEND_DIR="$(pwd)/../Website-Sonotheia-v251120/frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== SONOTHEIA LAUNCH SYSTEM ===${NC}"

# Check paths
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    echo -e "${RED}Please verify the parallel directory structure.${NC}"
    exit 1
fi

# 1. Start Backend
echo -e "${BLUE}Starting Backend...${NC}"
cd "$BACKEND_DIR"
# Check venv
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
else
    echo -e "${RED}No virtual environment found! Please run setup first.${NC}"
    exit 1
fi

# Run Uvicorn in background
# Use 0.0.0.0 to enable local network access if desired, or 127.0.0.1 for security
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}Backend running (PID: $BACKEND_PID)${NC}"

# 2. Start Frontend
echo -e "${BLUE}Starting Frontend...${NC}"
cd "$FRONTEND_DIR"
# Vite dev server
# Force port 3000 to match backend CORS config
npm run dev -- --port 3000 --host &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend running (PID: $FRONTEND_PID)${NC}"

echo -e "${BLUE}=== SYSTEMS OPERATIONAL ===${NC}"
echo -e "Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "Frontend UI: ${GREEN}http://localhost:3000${NC}"
echo -e "Press Ctrl+C to shutdown."

# Cleanup handler
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}
trap cleanup INT

wait
