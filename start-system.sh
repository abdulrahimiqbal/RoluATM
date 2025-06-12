#!/bin/bash

# RoluATM System Startup Script
echo "🎰 Starting RoluATM System..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*backend" 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null  
pkill -f "python.*pi_backend" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 3

# Check and kill processes on specific ports
echo "🔍 Checking for port conflicts..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
sleep 2

# Set environment variables
export WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19
export DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
export DEV_MODE=true
export MINI_APP_URL=http://localhost:3001

echo "✅ Environment variables set"
echo "✅ Backend will run on: http://localhost:8000"
echo "✅ Kiosk will run on: http://localhost:3000"
echo "✅ Mini app will run on: http://localhost:3001"

# Start backend in background
echo "🚀 Starting backend server..."
cd server && python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start kiosk app in background
echo "🚀 Starting kiosk app..."
cd kiosk-app && npm run dev &
KIOSK_PID=$!
cd ..

# Start mini app in background
echo "🚀 Starting mini app..."
cd mini-app && npm run dev &
MINI_PID=$!
cd ..

echo ""
echo "🎉 RoluATM System Started!"
echo "📱 Kiosk: http://localhost:3000"
echo "🌐 Mini App: http://localhost:3001"
echo "⚙️  Backend: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop all services"

# Wait for user interrupt
trap 'echo "🛑 Stopping all services..."; kill $BACKEND_PID $KIOSK_PID $MINI_PID 2>/dev/null; exit 0' INT

# Keep script running
wait 