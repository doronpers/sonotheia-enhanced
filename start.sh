#!/bin/bash
# Quick start script for Sonotheia Enhanced
# Starts both backend and frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Sonotheia Enhanced - Quick Start Script     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is available (try v2 first, then v1)
DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Check if Docker is available
if command -v docker &> /dev/null && [ -n "$DOCKER_COMPOSE_CMD" ]; then
    echo -e "${GREEN}✓ Docker detected - Using Docker setup${NC}"
    echo ""
    
    # Stop any running containers
    echo -e "${YELLOW}Stopping any running containers...${NC}"
    $DOCKER_COMPOSE_CMD down 2>/dev/null || true
    
    # Start services
    echo -e "${YELLOW}Starting services with Docker Compose...${NC}"
    $DOCKER_COMPOSE_CMD up --build -d
    
    echo ""
    echo -e "${GREEN}✓ Services started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Access the application:${NC}"
    echo -e "  • Frontend Dashboard: ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Backend API:        ${GREEN}http://localhost:8000${NC}"
    echo -e "  • API Documentation:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}To view logs:${NC} $DOCKER_COMPOSE_CMD logs -f"
    echo -e "${YELLOW}To stop:${NC} $DOCKER_COMPOSE_CMD down"
    
else
    echo -e "${YELLOW}⚠ Docker not found - Using local setup${NC}"
    echo ""
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check for Node/npm
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        echo -e "${RED}✗ Node.js and npm are required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python and Node.js detected${NC}"
    echo ""
    
    # Setup backend
    echo -e "${YELLOW}Setting up backend...${NC}"
    cd backend
    
    if [ ! -d "venv" ]; then
        echo "  Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "  Activating virtual environment..."
    source venv/bin/activate
    
    echo "  Installing Python dependencies..."
    pip install -q -r requirements.txt
    
    echo "  Starting backend server..."
    uvicorn api.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    cd ..
    
    # Setup frontend
    echo -e "${YELLOW}Setting up frontend...${NC}"
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        echo "  Installing npm dependencies..."
        npm install --legacy-peer-deps --silent
    fi
    
    echo "  Starting frontend server..."
    BROWSER=none PORT=3000 npm start &
    FRONTEND_PID=$!
    
    cd ..
    
    # Save PIDs for cleanup
    echo "$BACKEND_PID" > .backend.pid
    echo "$FRONTEND_PID" > .frontend.pid
    
    echo ""
    echo -e "${GREEN}✓ Services started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Access the application:${NC}"
    echo -e "  • Frontend Dashboard: ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Backend API:        ${GREEN}http://localhost:8000${NC}"
    echo -e "  • API Documentation:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}To stop:${NC} ./stop.sh or press Ctrl+C"
    echo ""
    
    # Cleanup function for graceful shutdown
    cleanup() {
        echo ''
        echo -e "${YELLOW}Stopping services...${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        rm -f .backend.pid .frontend.pid
        exit 0
    }
    
    # Wait for user interrupt
    trap cleanup INT TERM
    
    # Keep script running
    wait
fi
