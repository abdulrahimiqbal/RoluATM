#!/bin/bash
# RoluATM Raspberry Pi Deployment Script
# Automates the complete setup of RoluATM on Raspberry Pi 4B with 7" touchscreen

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/rahiim/RoluATM"
USER="rahiim"
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
echo -n "Continue with RoluATM deployment? (y/N): "
read -r REPLY
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

# Clone project
log "Cloning RoluATM project..."
cd /home/$USER
git clone https://github.com/abdulrahimiqbal/RoluATM.git

cd "$PROJECT_DIR"

# Fix ownership
sudo chown -R $USER:$USER "$PROJECT_DIR"

# Phase 7: Install project dependencies
log "📦 Phase 7: Installing project dependencies"

log "Installing Node.js dependencies for kiosk app..."
cd kiosk-app
npm install
cd ..

log "Installing Node.js dependencies for mini app..."
cd mini-app
npm install
cd ..

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
    cat > .env.local << 'EOF'
# RoluATM Raspberry Pi Configuration
# Database Configuration (Local PostgreSQL)
DATABASE_URL=postgresql://rolu:rolu123@localhost:5432/roluatm

# World ID Configuration (REPLACE WITH YOUR ACTUAL VALUES)
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19

# API Configuration
VITE_API_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8000

# Hardware Configuration
TFLEX_PORT=/dev/ttyUSB0
DEV_MODE=false
KIOSK_MODE=true

# Mini App URL (using production Vercel deployment)
MINI_APP_URL=https://mini-app-azure.vercel.app
EOF
fi

# Phase 9: Set up database schema
log "🗄️ Phase 9: Setting up database schema"

log "Creating database tables..."
python3 -c "
import psycopg2
import os

# Database connection
conn = psycopg2.connect('postgresql://rolu:rolu123@localhost:5432/roluatm')
cur = conn.cursor()

# Create transactions table
cur.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(36) PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nullifier_hash VARCHAR(256),
    progress VARCHAR(50) DEFAULT 'created',
    expires_at TIMESTAMP,
    mini_app_url TEXT,
    paid_at TIMESTAMP
);
''')

# Create indexes
cur.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_transactions_nullifier_hash ON transactions(nullifier_hash);')

conn.commit()
cur.close()
conn.close()
print('Database schema created successfully')
"

# Phase 10: Create systemd services
log "🔧 Phase 10: Creating systemd services"

# Backend service
sudo tee /etc/systemd/system/rolu-backend.service > /dev/null << EOF
[Unit]
Description=RoluATM Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/bin:/usr/local/bin:$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python pi_backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Kiosk service
sudo tee /etc/systemd/system/rolu-kiosk.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Service
After=network.target rolu-backend.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/kiosk-app
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/npm run dev
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Auto-start kiosk in browser on boot
sudo tee /etc/systemd/system/rolu-browser.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Browser
After=graphical.target rolu-kiosk.service
Wants=graphical.target

[Service]
Type=simple
User=$USER
Environment=DISPLAY=:0
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/chromium-browser --start-fullscreen --kiosk --no-toolbar --no-menubar --no-context-menu --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:3000
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable rolu-backend.service
sudo systemctl enable rolu-kiosk.service
sudo systemctl enable rolu-browser.service

# Phase 11: Configure auto-login and kiosk mode
log "🖥️ Phase 11: Configuring kiosk mode"

# Enable auto-login
sudo systemctl enable getty@tty1.service
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin $USER %I \$TERM
Type=idle
EOF

# Configure auto-start X11 and browser
if [ ! -f "/home/$USER/.xinitrc" ]; then
    cat > /home/$USER/.xinitrc << EOF
#!/bin/bash
xset -dpms     # disable DPMS (Energy Star) features.
xset s off     # disable screen saver
xset s noblank # don't blank the video device
unclutter -idle 0 &
exec openbox-session
EOF
    chmod +x /home/$USER/.xinitrc
fi

# Auto-start X11 in .bashrc
if ! grep -q "startx" /home/$USER/.bashrc; then
    echo "# Auto-start X11 for kiosk mode" >> /home/$USER/.bashrc
    echo "if [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then" >> /home/$USER/.bashrc
    echo "    startx" >> /home/$USER/.bashrc
    echo "fi" >> /home/$USER/.bashrc
fi

# Phase 12: Final setup
log "✅ Phase 12: Final configuration"

# Start services
log "Starting services..."
sudo systemctl start rolu-backend.service

# Wait a moment for backend to start
sleep 5

sudo systemctl start rolu-kiosk.service

# Show status
log "Service status:"
systemctl is-active rolu-backend.service && log "✅ Backend service: Running" || log_error "❌ Backend service: Failed"
systemctl is-active rolu-kiosk.service && log "✅ Kiosk service: Running" || log_error "❌ Kiosk service: Failed"

# Final message
echo -e "${GREEN}"
echo "🎉 RoluATM Deployment Complete!"
echo "================================"
echo ""
echo "✅ Backend running on: http://localhost:8000"
echo "✅ Kiosk app running on: http://localhost:3000"
echo "✅ Database: PostgreSQL (local)"
echo "✅ Services: Auto-start enabled"
echo ""
echo "📱 Access your kiosk at: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "🔧 To check status:"
echo "   sudo systemctl status rolu-backend"
echo "   sudo systemctl status rolu-kiosk"
echo ""
echo "📋 Logs available at: $LOG_FILE"
echo ""
echo "🔄 Reboot to enable full kiosk mode:"
echo "   sudo reboot"
echo -e "${NC}"

log "RoluATM deployment completed successfully!" 