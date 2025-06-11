#!/bin/bash

# RoluATM System Stop Script
echo "🛑 Stopping RoluATM System..."

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚡ Force stopping $service_name..."
                kill -9 "$pid" 2>/dev/null
            fi
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file found for $service_name"
    fi
}

# Stop services
stop_service "Backend" "backend.pid"
stop_service "Kiosk App" "kiosk.pid"
stop_service "Mini App" "mini.pid"

# Kill any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "python.*backend" 2>/dev/null
pkill -f "npm.*dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Kill processes on specific ports
for port in 8000 3000 3001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "🔧 Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    echo "🗑️  Cleaning log files..."
    rm -f backend.log kiosk.log mini.log
fi

echo ""
echo "✅ RoluATM System Stopped Successfully!"
echo "All services have been terminated and ports are free." 