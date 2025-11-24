#!/bin/bash
# Stop script for Sonotheia Enhanced

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Sonotheia Enhanced services...${NC}"

# Check if Docker Compose is being used
if docker-compose ps &> /dev/null; then
    echo "Stopping Docker containers..."
    docker-compose down
    echo -e "${GREEN}✓ Docker services stopped${NC}"
else
    # Stop local processes
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✓ Backend stopped${NC}" || echo "Backend not running"
        rm -f .backend.pid
    fi
    
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}✓ Frontend stopped${NC}" || echo "Frontend not running"
        rm -f .frontend.pid
    fi
    
    # Also try to kill by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo -e "${GREEN}All services stopped${NC}"
