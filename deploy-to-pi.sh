#!/bin/bash
"""
RoluATM Raspberry Pi Deployment Script
Automates the complete setup of RoluATM on Raspberry Pi 4B with 7" touchscreen
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/pi/RoluATM"
USER="pi"
LOG_FILE="/tmp/rolu-deployment.log"

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOG_FILE"
}

# Error handling
set -e
trap 'log_error "Deployment failed on line $LINENO"' ERR

# Banner
echo -e "${BLUE}"
echo "🍓 RoluATM Raspberry Pi Deployment"
echo "=================================="
echo "This script will set up your Pi as a crypto-to-cash kiosk"
echo -e "${NC}"

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    log_warning "Not detected as Raspberry Pi - continuing anyway"
fi

# Ask for confirmation
read -p "Continue with RoluATM deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

log "Starting RoluATM deployment..."

# Phase 1: System Updates and Basic Tools
log "📦 Phase 1: System setup and updates"

log "Updating package lists..."
sudo apt update

log "Upgrading system packages..."
sudo apt upgrade -y

log "Installing essential tools..."
sudo apt install -y \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Phase 2: Install Node.js
log "🟢 Phase 2: Installing Node.js 18.x"

# Remove old Node.js if exists
sudo apt remove -y nodejs npm 2>/dev/null || true

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

NODE_VERSION=$(node --version)
log "Node.js installed: $NODE_VERSION"

# Phase 3: Install Python and dependencies
log "🐍 Phase 3: Setting up Python environment"

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev

PYTHON_VERSION=$(python3 --version)
log "Python installed: $PYTHON_VERSION"

# Phase 4: Install PostgreSQL
log "🐘 Phase 4: Setting up PostgreSQL database"

sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
log "Creating RoluATM database..."
sudo -u postgres psql -c "CREATE USER rolu WITH PASSWORD 'rolu123';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE roluatm OWNER rolu;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE roluatm TO rolu;" 2>/dev/null || true

log "PostgreSQL setup complete"

# Phase 5: Install additional tools for Pi
log "🔧 Phase 5: Installing Raspberry Pi specific tools"

sudo apt install -y \
    chromium-browser \
    unclutter \
    xdotool \
    minicom \
    screen \
    xinput

# Phase 6: Clone and setup project
log "📁 Phase 6: Setting up RoluATM project"

# Remove existing project if it exists
if [ -d "$PROJECT_DIR" ]; then
    log_warning "Existing project found, backing up..."
    sudo mv "$PROJECT_DIR" "${PROJECT_DIR}.backup.$(date +%s)"
fi

# Clone project (assuming it's already pushed to GitHub)
log "Cloning RoluATM project..."
cd /home/pi
git clone https://github.com/abdulrahimiqbal/RoluATM.git

cd "$PROJECT_DIR"

# Fix ownership
sudo chown -R $USER:$USER "$PROJECT_DIR"

# Phase 7: Install project dependencies
log "📦 Phase 7: Installing project dependencies"

log "Installing Node.js dependencies..."
npm install

log "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

log "Installing Python dependencies..."
pip install -r requirements.txt

# Phase 8: Configure environment
log "⚙️ Phase 8: Configuring environment"

# Create environment file
if [ ! -f ".env.local" ]; then
    log "Creating environment configuration..."
    cat > .env.local << EOF
# RoluATM Raspberry Pi Configuration
# Generated on $(date)

# API Configuration
VITE_API_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8000

# Hardware Configuration
TFLEX_PORT=/dev/ttyUSB0
DEV_MODE=false
KIOSK_MODE=true

# Database Configuration (Local PostgreSQL)
DATABASE_URL=postgresql://rolu:rolu123@localhost:5432/roluatm

# World ID Configuration (REPLACE WITH YOUR ACTUAL VALUES)
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19

# Mini App URL (Production Vercel deployment)
MINI_APP_URL=https://mini-app-azure.vercel.app

# Display Configuration
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480
EOF

    log "Environment file created at .env.local"
    log_warning "Please update .env.local with your actual World ID credentials!"
else
    log "Environment file already exists"
fi

# Phase 9: Initialize database
log "🗄️ Phase 9: Setting up database tables"

# Create database schema
source venv/bin/activate
python3 << EOF
import os
os.environ['DATABASE_URL'] = 'postgresql://rolu:rolu123@localhost:5432/roluatm'

# Read and execute schema
with open('schema.sql', 'r') as f:
    schema = f.read()

import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute(schema)
conn.commit()
cur.close()
conn.close()
print("Database schema created successfully")
EOF

# Phase 10: Configure system for kiosk mode
log "🖥️ Phase 10: Configuring kiosk mode"

# Add user to necessary groups
sudo usermod -a -G dialout $USER
sudo usermod -a -G video $USER
sudo usermod -a -G input $USER

# Create systemd service for auto-start
sudo tee /etc/systemd/system/rolu-kiosk.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Service
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0
ExecStart=$PROJECT_DIR/start-kiosk.sh
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

# Make scripts executable
chmod +x start-kiosk.sh
chmod +x test-pi-deployment.sh

# Phase 11: Configure display and boot settings
log "📺 Phase 11: Configuring display settings"

# Configure boot settings for touchscreen
sudo tee -a /boot/config.txt > /dev/null << EOF

# RoluATM Kiosk Display Configuration
# Disable overscan for exact screen size
disable_overscan=1

# Enable touchscreen
dtoverlay=vc4-kms-v3d
max_framebuffers=2

# Set specific resolution for 7" display
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0

# GPU memory split
gpu_mem=128
EOF

# Configure auto-login and disable screen saver
sudo raspi-config nonint do_boot_behaviour B4  # Desktop autologin

# Disable screen blanking
sudo tee -a /home/$USER/.bashrc > /dev/null << EOF

# RoluATM Kiosk Settings
# Disable screen blanking
export DISPLAY=:0
xset s off
xset -dpms
xset s noblank
EOF

# Phase 12: Final setup and testing
log "🧪 Phase 12: Final setup and testing"

# Build the frontend
log "Building frontend..."
npm run build

# Test database connection
log "Testing database connection..."
source venv/bin/activate
python3 -c "
import psycopg2
import os
os.environ['DATABASE_URL'] = 'postgresql://rolu:rolu123@localhost:5432/roluatm'
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('Database connection successful')
conn.close()
"

# Enable the kiosk service (but don't start yet)
sudo systemctl daemon-reload
sudo systemctl enable rolu-kiosk.service

# Create logs directory
mkdir -p logs

# Phase 13: Summary and next steps
log "✅ Deployment completed successfully!"

echo -e "${GREEN}"
echo "🎉 RoluATM Raspberry Pi Deployment Complete!"
echo "============================================="
echo -e "${NC}"

echo -e "${BLUE}📋 What was installed:${NC}"
echo "  ✅ Node.js $(node --version)"
echo "  ✅ Python $(python3 --version)"
echo "  ✅ PostgreSQL database with 'roluatm' database"
echo "  ✅ Chromium browser for kiosk mode"
echo "  ✅ RoluATM project dependencies"
echo "  ✅ Systemd service for auto-start"

echo -e "${BLUE}📁 Project location:${NC} $PROJECT_DIR"
echo -e "${BLUE}📄 Logs location:${NC} $PROJECT_DIR/logs/"
echo -e "${BLUE}⚙️ Config file:${NC} $PROJECT_DIR/.env.local"

echo -e "${YELLOW}⚠️ IMPORTANT NEXT STEPS:${NC}"
echo "1. Edit $PROJECT_DIR/.env.local with your actual World ID credentials"
echo "2. Connect your T-Flex coin dispenser via USB"
echo "3. Test the setup: cd $PROJECT_DIR && ./test-pi-deployment.sh"
echo "4. Start manually: cd $PROJECT_DIR && ./start-kiosk.sh"
echo "5. Enable auto-start on boot: sudo systemctl start rolu-kiosk.service"

echo -e "${BLUE}🔧 Manual testing commands:${NC}"
echo "  Test backend: cd $PROJECT_DIR && source venv/bin/activate && python pi_backend.py"
echo "  Test kiosk:   cd $PROJECT_DIR && ./start-kiosk.sh"
echo "  View logs:    tail -f $PROJECT_DIR/logs/kiosk.log"

echo -e "${GREEN}🚀 Reboot your Pi to apply all display settings!${NC}"

log "Deployment log saved to: $LOG_FILE"
log "Deployment completed at $(date)" 