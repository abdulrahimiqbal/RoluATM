#!/bin/bash

echo "🎰 RoluATM System Startup"
echo "========================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $1 is in use${NC}"
        return 1
    else
        echo -e "${GREEN}Port $1 is available${NC}"
        return 0
    fi
}

# Function to kill processes on specific ports
cleanup_ports() {
    echo -e "${YELLOW}Cleaning up ports...${NC}"
    lsof -ti:8000,3000,3001,3002,3003 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Cleanup first
cleanup_ports

# Check required ports
echo -e "${BLUE}Checking ports...${NC}"
check_port 8000 || cleanup_ports
check_port 3000 || cleanup_ports
check_port 3001 || cleanup_ports

# Set environment variables
export WORLD_CLIENT_SECRET="sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19"
export DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
export DEV_MODE="true"
export MINI_APP_URL="https://mini-app-azure.vercel.app"

echo -e "${BLUE}Environment configured:${NC}"
echo "  - DEV_MODE: $DEV_MODE"
echo "  - MINI_APP_URL: $MINI_APP_URL"
echo ""

# Start backend
echo -e "${BLUE}Starting backend server...${NC}"
python3 pi_backend.py &
BACKEND_PID=$!
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start kiosk app
echo -e "${BLUE}Starting kiosk app...${NC}"
cd kiosk-app
npm run dev &
KIOSK_PID=$!
cd ..
sleep 3

# Start mini app
echo -e "${BLUE}Starting mini app...${NC}"
cd mini-app
npm run dev &
MINI_PID=$!
cd ..
sleep 3

echo ""
echo -e "${GREEN}🎉 RoluATM System Started Successfully!${NC}"
echo "=================================="
echo -e "${BLUE}Backend:${NC}    http://localhost:8000"
echo -e "${BLUE}Kiosk App:${NC}  http://localhost:3000"
echo -e "${BLUE}Mini App:${NC}   http://localhost:3001"
echo ""
echo -e "${YELLOW}Test the system:${NC}"
echo "1. Open kiosk app and select an amount"
echo "2. Scan the QR code with your phone"
echo "3. The mini app should load with the transaction"
echo ""
echo -e "${YELLOW}To stop the system:${NC}"
echo "Press Ctrl+C or run: ./stop-system.sh"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down RoluATM system...${NC}"
    kill $BACKEND_PID $KIOSK_PID $MINI_PID 2>/dev/null
    cleanup_ports
    echo -e "${GREEN}System stopped.${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
echo -e "${BLUE}System running... Press Ctrl+C to stop${NC}"
wait 