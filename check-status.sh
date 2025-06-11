#!/bin/bash

echo "🔍 RoluATM System Status Check"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local port=$3
    
    echo -n "  $name: "
    
    # Check if port is listening
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        echo -e "${RED}❌ Not running (port $port not listening)${NC}"
        return 1
    fi
    
    # Check if service responds
    if curl -s --max-time 3 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Port open but not responding${NC}"
        return 1
    fi
}

echo -e "${BLUE}Checking services...${NC}"

# Check backend
check_service "Backend API" "http://localhost:8000/health" 8000
BACKEND_OK=$?

# Check kiosk app
check_service "Kiosk App" "http://localhost:3000" 3000
KIOSK_OK=$?

# Check mini app
check_service "Mini App" "http://localhost:3001" 3001
MINI_OK=$?

echo ""

# Overall status
if [ $BACKEND_OK -eq 0 ] && [ $KIOSK_OK -eq 0 ] && [ $MINI_OK -eq 0 ]; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
    echo ""
    echo -e "${BLUE}Access URLs:${NC}"
    echo "  Backend:   http://localhost:8000"
    echo "  Kiosk:     http://localhost:3000"
    echo "  Mini App:  http://localhost:3001"
    echo ""
    echo -e "${BLUE}Test transaction creation:${NC}"
    echo "  curl -X POST http://localhost:8000/api/transaction/create -H \"Content-Type: application/json\" -d '{\"amount\": 5}'"
else
    echo -e "${RED}❌ Some services are not running${NC}"
    echo ""
    echo -e "${BLUE}To start the system:${NC}"
    echo "  ./start-system.sh"
    echo ""
    echo -e "${BLUE}To stop the system:${NC}"
    echo "  ./stop-system.sh"
fi 