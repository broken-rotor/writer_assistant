#!/bin/bash

# Quick Test Script - Fast feedback during development
# Runs minimal tests without full build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Quick Test ===${NC}"
echo ""

# Backend quick test
if [ "$1" == "backend" ] || [ "$1" == "" ]; then
    echo -e "${BLUE}Running backend tests...${NC}"
    cd "$BACKEND_DIR"

    if [ -d "venv" ]; then
        source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
        pytest tests/ -v -x  # Stop on first failure for quick feedback
        deactivate
        echo -e "${GREEN}✓ Backend tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Backend venv not found, run full build first${NC}"
    fi

    cd "$SCRIPT_DIR"
fi

# Frontend quick test (TypeScript check only, no full build)
if [ "$1" == "frontend" ] || [ "$1" == "" ]; then
    echo -e "${BLUE}Running frontend TypeScript check...${NC}"
    cd "$FRONTEND_DIR"

    if [ -d "node_modules" ]; then
        # Just check for TypeScript errors, don't build
        npx ng build --configuration development --dry-run
        echo -e "${GREEN}✓ Frontend TypeScript check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend node_modules not found, run full build first${NC}"
    fi

    cd "$SCRIPT_DIR"
fi

echo ""
echo -e "${GREEN}Quick test complete!${NC}"
