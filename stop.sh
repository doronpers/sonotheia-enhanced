#!/bin/bash
# Stop script for Sonotheia Enhanced

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Sonotheia Enhanced services...${NC}"

# Project name (matches .env COMPOSE_PROJECT_NAME)
PROJECT_NAME="sonotheia-treehorn"

# Check if Docker Compose is being used (try v2 first, then v1)
DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose -p $PROJECT_NAME"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose -p $PROJECT_NAME"
fi

if [ -n "$DOCKER_COMPOSE_CMD" ] && $DOCKER_COMPOSE_CMD ps &> /dev/null; then
    echo "Stopping Docker containers..."
    $DOCKER_COMPOSE_CMD down
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
