#!/bin/bash

# RoluATM System Status Check
echo "🔍 RoluATM System Status"
echo "========================"

# Function to check service status
check_service() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    local url=$4
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            # Check if service is responding
            if curl -s "$url" > /dev/null 2>&1; then
                echo "✅ $service_name: Running (PID: $pid, Port: $port)"
            else
                echo "⚠️  $service_name: Process running but not responding (PID: $pid)"
            fi
        else
            echo "❌ $service_name: Process not running (stale PID file)"
        fi
    else
        echo "❌ $service_name: Not running (no PID file)"
    fi
}

# Check all services
check_service "Backend" "backend.pid" "8000" "http://localhost:8000/health"
check_service "Kiosk App" "kiosk.pid" "3000" "http://localhost:3000"
check_service "Mini App" "mini.pid" "3001" "http://localhost:3001"

echo ""
echo "🌐 Service URLs:"
echo "Backend API:    http://localhost:8000"
echo "Kiosk App:      http://localhost:3000"
echo "Mini App:       http://localhost:3001"

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