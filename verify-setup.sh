#!/bin/bash
# Verification script for Sonotheia Enhanced setup
# Tests that all components are properly configured

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Sonotheia Enhanced - Setup Verification    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check function
check() {
    local name="$1"
    local command="$2"
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        ((ERRORS++))
        return 0  # Don't exit on error
    fi
}

warn() {
    local name="$1"
    local command="$2"
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name (optional)"
        ((WARNINGS++))
        return 0  # Don't exit on warning
    fi
}

echo -e "${BLUE}Checking Prerequisites...${NC}"
check "Docker installed" "command -v docker"
warn "Docker Compose v2" "docker compose version"
warn "Docker Compose v1" "command -v docker-compose"
check "Python 3 installed" "command -v python3"
check "Node.js installed" "command -v node"
check "npm installed" "command -v npm"

echo ""
echo -e "${BLUE}Checking Project Files...${NC}"
check "docker-compose.yml exists" "test -f docker-compose.yml"
check "backend/Dockerfile exists" "test -f backend/Dockerfile"
check "frontend/Dockerfile exists" "test -f frontend/Dockerfile"
check "frontend/nginx.conf exists" "test -f frontend/nginx.conf"
check "start.sh exists" "test -f start.sh"
check "stop.sh exists" "test -f stop.sh"
check "start.bat exists" "test -f start.bat"
check "stop.bat exists" "test -f stop.bat"
check ".env.example exists" "test -f .env.example"
check "QUICKSTART.md exists" "test -f QUICKSTART.md"

echo ""
echo -e "${BLUE}Checking Configuration Files...${NC}"
check "backend/requirements.txt exists" "test -f backend/requirements.txt"
check "frontend/package.json exists" "test -f frontend/package.json"
check "backend/config/settings.yaml exists" "test -f backend/config/settings.yaml"

echo ""
echo -e "${BLUE}Checking Scripts...${NC}"
check "start.sh is executable" "test -x start.sh"
check "stop.sh is executable" "test -x stop.sh"
check "start.sh syntax is valid" "bash -n start.sh"
check "stop.sh syntax is valid" "bash -n stop.sh"

echo ""
echo -e "${BLUE}Validating Docker Configuration...${NC}"
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        check "docker-compose.yml is valid" "docker compose config --quiet"
    elif command -v docker-compose &> /dev/null; then
        check "docker-compose.yml is valid" "docker-compose config --quiet"
    else
        echo -e "${YELLOW}⚠${NC} Cannot validate docker-compose.yml (no Docker Compose found)"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Cannot validate Docker configuration (Docker not available)"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}Checking Documentation...${NC}"
check "README.md exists" "test -f README.md"
check "API.md exists" "test -f API.md"
check "README has Quick Start section" "grep -q 'Quick Start' README.md"
check "README has Docker Setup section" "grep -q 'Docker Setup' README.md"
check "README has Troubleshooting section" "grep -q 'Troubleshooting' README.md"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS optional components missing${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Run: ${GREEN}./start.sh${NC} or ${GREEN}docker compose up${NC}"
    echo "  2. Open: ${GREEN}http://localhost:3000${NC} (Dashboard)"
    echo "  3. Open: ${GREEN}http://localhost:8000/docs${NC} (API Docs)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $ERRORS critical checks failed${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS optional components missing${NC}"
    fi
    echo ""
    echo "Please fix the errors above before starting the application."
    exit 1
fi
