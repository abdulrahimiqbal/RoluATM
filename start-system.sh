#!/bin/bash

# RoluATM System Startup Script
echo "🎰 Starting RoluATM System..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*backend" 2>/dev/null
pkill -f "npm.*dev" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 3

# Check for port conflicts and kill processes using our ports
echo "🔍 Checking for port conflicts..."
for port in 8000 3000 3001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "⚠️  Killing process $pid using port $port"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
done

# Set environment variables
echo "🔧 Setting environment variables..."
export WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19
export DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
export DEV_MODE=true
export MINI_APP_URL=https://mini-app-azure.vercel.app

# Function to start backend
start_backend() {
    echo "🚀 Starting backend server..."
    cd "$(dirname "$0")"
    python3 pi_backend.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    echo "✅ Backend started with PID $BACKEND_PID"
    
    # Wait for backend to be ready
    echo "⏳ Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo "❌ Backend failed to start"
            exit 1
        fi
    done
}

# Function to start kiosk app
start_kiosk() {
    echo "🖥️  Starting kiosk app..."
    cd kiosk-app
    npm run dev > ../kiosk.log 2>&1 &
    KIOSK_PID=$!
    echo $KIOSK_PID > ../kiosk.pid
    echo "✅ Kiosk app started with PID $KIOSK_PID"
    cd ..
}

# Function to start mini app
start_mini() {
    echo "📱 Starting mini app..."
    cd mini-app
    npm run dev > ../mini.log 2>&1 &
    MINI_PID=$!
    echo $MINI_PID > ../mini.pid
    echo "✅ Mini app started with PID $MINI_PID"
    cd ..
}

# Start services
start_backend
sleep 3
start_kiosk
sleep 3
start_mini

echo ""
echo "🎉 RoluATM System Started Successfully!"
echo "=================================="
echo "🔗 Backend API:    http://localhost:8000"
echo "🖥️  Kiosk App:     http://localhost:3000"
echo "📱 Mini App:       http://localhost:3001"
echo ""
echo "📋 Service Status:"
echo "Backend PID: $(cat backend.pid 2>/dev/null || echo 'Not found')"
echo "Kiosk PID:   $(cat kiosk.pid 2>/dev/null || echo 'Not found')"
echo "Mini PID:    $(cat mini.pid 2>/dev/null || echo 'Not found')"
echo ""
echo "📝 Logs:"
echo "Backend: tail -f backend.log"
echo "Kiosk:   tail -f kiosk.log"
echo "Mini:    tail -f mini.log"
echo ""
echo "🛑 To stop: ./stop-system.sh" 