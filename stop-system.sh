#!/bin/bash

# RoluATM System Stop Script
echo "🛑 Stopping RoluATM System..."

# Kill all related processes
echo "🧹 Stopping all services..."
pkill -f "python.*backend" 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null
pkill -f "python.*pi_backend" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Kill processes on specific ports
echo "🔍 Freeing up ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null

sleep 2

echo "✅ All RoluATM services stopped"
echo "🔓 Ports 8000, 3000, 3001 are now free"

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    echo "🗑️  Cleaning log files..."
    rm -f backend.log kiosk.log mini.log
fi 