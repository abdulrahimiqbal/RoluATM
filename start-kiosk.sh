#!/bin/bash
# Manual Kiosk Startup Script for RoluATM
# Use this to test the kiosk app manually

echo "🚀 Starting RoluATM Kiosk..."

# Check if HTTP server is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ HTTP server not running. Starting it..."
    python3 /home/rahiim/RoluATM/kiosk_server.py &
    sleep 3
fi

echo "✅ HTTP server is running"

# Check if we're in a graphical environment
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

echo "🌐 Opening kiosk app in browser..."
echo "📍 URL: http://localhost:3000"

# Start Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --start-fullscreen \
    --disable-web-security \
    --allow-running-insecure-content \
    --disable-features=VizDisplayCompositor \
    --no-first-run \
    --disable-default-apps \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    http://localhost:3000

echo "🛑 Kiosk closed" 