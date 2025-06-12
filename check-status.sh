#!/bin/bash

# RoluATM System Status Check
echo "🔍 RoluATM System Status Check"
echo "=============================="

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i:$port >/dev/null 2>&1; then
        echo "✅ $service (port $port): RUNNING"
        return 0
    else
        echo "❌ $service (port $port): NOT RUNNING"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service=$2
    
    if curl -s "$url" >/dev/null 2>&1; then
        echo "✅ $service endpoint: RESPONDING"
        return 0
    else
        echo "❌ $service endpoint: NOT RESPONDING"
        return 1
    fi
}

echo ""
echo "📊 Port Status:"
check_port 8000 "Backend API"
check_port 3000 "Kiosk App"
check_port 3001 "Mini App"

echo ""
echo "🌐 Endpoint Status:"
check_endpoint "http://localhost:8000/health" "Backend Health"
check_endpoint "http://localhost:3000" "Kiosk App"
check_endpoint "http://localhost:3001" "Mini App"

echo ""
echo "🔗 Access URLs:"
echo "Backend API:    http://localhost:8000"
echo "Kiosk App:      http://localhost:3000"
echo "Mini App:       http://localhost:3001"

echo ""
echo "📋 Process Information:"
echo "Backend processes:"
pgrep -f "python.*app.py" | head -3
echo "Node processes:"
pgrep -f "npm run dev" | head -3

echo ""
echo "📊 Port Usage:"
for port in 8000 3000 3001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        process=$(ps -p $pid -o comm= 2>/dev/null)
        echo "Port $port: Used by PID $pid ($process)"
    else
        echo "Port $port: Available"
    fi
done

echo ""
echo "📝 Recent Log Activity:"
if [ -f "backend.log" ]; then
    echo "Backend (last 2 lines):"
    tail -2 backend.log | sed 's/^/  /'
fi

if [ -f "kiosk.log" ]; then
    echo "Kiosk (last 2 lines):"
    tail -2 kiosk.log | sed 's/^/  /'
fi

if [ -f "mini.log" ]; then
    echo "Mini (last 2 lines):"
    tail -2 mini.log | sed 's/^/  /'
fi

echo ""
echo "🔧 Management Commands:"
echo "./start-system.sh  - Start all services"
echo "./stop-system.sh   - Stop all services"
echo "./check-status.sh  - Show this status" 