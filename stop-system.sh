#!/bin/bash

echo "🛑 Stopping RoluATM System"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Killing all RoluATM processes...${NC}"

# Kill all related processes
pkill -f "python.*pi_backend" 2>/dev/null
pkill -f "vite.*kiosk" 2>/dev/null  
pkill -f "vite.*mini" 2>/dev/null
pkill -f "npm.*dev" 2>/dev/null

# Force kill processes on specific ports
echo -e "${YELLOW}Freeing up ports...${NC}"
lsof -ti:8000,3000,3001,3002,3003 | xargs kill -9 2>/dev/null || true

sleep 2

echo -e "${GREEN}✅ RoluATM system stopped${NC}"
echo "All ports are now available for restart" 