#!/bin/bash
"""
RoluATM Kiosk Startup Script for Raspberry Pi
Starts the backend, frontend, and launches Chromium in kiosk mode
"""

# Configuration
PROJECT_DIR="/home/pi/RoluATM"
BACKEND_PORT=8000
FRONTEND_PORT=3000
LOG_DIR="$PROJECT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/kiosk.log"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_DIR/kiosk.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_DIR/kiosk.log"
}

# Cleanup function
cleanup() {
    log "Shutting down RoluATM kiosk..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        log "Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        log "Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining processes
    pkill -f "python.*server/app.py" 2>/dev/null
    pkill -f "serve.*dist" 2>/dev/null
    pkill -f chromium 2>/dev/null
    
    log "Kiosk shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Change to project directory
cd "$PROJECT_DIR" || {
    log_error "Cannot access project directory: $PROJECT_DIR"
    exit 1
}

log "Starting RoluATM Kiosk System"
log "Project directory: $PROJECT_DIR"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    log_warning ".env.local not found, creating from template"
    cp env.template .env.local
    log_warning "Please configure .env.local with your settings!"
fi

# Start Backend
log "Starting Python backend on port $BACKEND_PORT..."
source venv/bin/activate || {
    log_error "Python virtual environment not found. Run setup first."
    exit 1
}

python server/app.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

if [ $? -eq 0 ]; then
    log "Backend started successfully (PID: $BACKEND_PID)"
else
    log_error "Failed to start backend"
    exit 1
fi

# Wait for backend to be ready
log "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
        log "Backend is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "Backend failed to start within 30 seconds"
        cleanup
        exit 1
    fi
    
    sleep 1
done

# Build and start frontend
log "Building frontend..."
npm run build >> "$LOG_DIR/build.log" 2>&1

if [ $? -eq 0 ]; then
    log "Frontend built successfully"
else
    log_error "Frontend build failed"
    cleanup
    exit 1
fi

log "Starting frontend server on port $FRONTEND_PORT..."
npx serve -s dist -l $FRONTEND_PORT > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

if [ $? -eq 0 ]; then
    log "Frontend started successfully (PID: $FRONTEND_PID)"
else
    log_error "Failed to start frontend"
    cleanup
    exit 1
fi

# Wait for frontend to be ready
log "Waiting for frontend to start..."
for i in {1..15}; do
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
        log "Frontend is ready!"
        break
    fi
    
    if [ $i -eq 15 ]; then
        log_error "Frontend failed to start within 15 seconds"
        cleanup
        exit 1
    fi
    
    sleep 1
done

# Hide cursor (for kiosk mode)
unclutter -idle 1 &

# Start Chromium in kiosk mode
log "Starting Chromium in kiosk mode..."
chromium-browser \
    --kiosk \
    --no-first-run \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-translate \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    --autoplay-policy=no-user-gesture-required \
    --no-sandbox \
    --disable-dev-shm-usage \
    --start-fullscreen \
    --window-position=0,0 \
    --window-size=800,480 \
    "http://localhost:$FRONTEND_PORT" &

CHROMIUM_PID=$!

log "Chromium started (PID: $CHROMIUM_PID)"
log "RoluATM Kiosk is now running!"
log "Backend: http://localhost:$BACKEND_PORT"
log "Frontend: http://localhost:$FRONTEND_PORT" 
log "Logs: $LOG_DIR/"

# Wait for Chromium to exit (user closed kiosk)
wait $CHROMIUM_PID

log "Chromium exited, shutting down kiosk..."
cleanup 