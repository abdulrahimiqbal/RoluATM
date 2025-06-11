#!/bin/bash
# RoluATM Raspberry Pi Deployment Script v2.0
# Automates the complete setup of RoluATM on Raspberry Pi 4B with 7" touchscreen
# Improved with best practices for production deployment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/rahiim/RoluATM"
USER="rahiim"
LOG_FILE="/home/rahiim/rolu-deployment.log"
LOCK_FILE="/tmp/rolu-deploy.lock"

# Logging functions with better formatting
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERROR: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  WARNING: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" >> "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_FILE"
}

log_step() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [STEP] $1" >> "$LOG_FILE"
}

# Cleanup function
cleanup() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
    fi
}

# Improved error handling
handle_error() {
    local line_no=$1
    local error_code=$2
    log_error "Deployment failed at line $line_no with exit code $error_code"
    log_error "Check the log file at $LOG_FILE for details"
    cleanup
    exit $error_code
}

# Setup error trapping
set -eE
trap 'handle_error ${LINENO} $?' ERR
trap cleanup EXIT

# Check if script is already running
if [ -f "$LOCK_FILE" ]; then
    log_error "Another instance of this script is already running. Remove $LOCK_FILE if this is incorrect."
    exit 1
fi

# Create lock file
echo $$ > "$LOCK_FILE"

# Pre-flight checks
check_prerequisites() {
    log_step "Running pre-flight checks..."
    
    # Check if running as non-root user with sudo access
    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run this script as root. Run as user '$USER' with sudo access."
        exit 1
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        log_info "Testing sudo access..."
        sudo true || {
            log_error "This script requires sudo access. Please run: sudo visudo"
            exit 1
        }
    fi
    
    # Check if running on Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warning "Not detected as Raspberry Pi - continuing anyway for testing"
    else
        log "Raspberry Pi detected"
    fi
    
    # Check available disk space (need at least 2GB free)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 2097152 ]; then  # 2GB in KB
        log_error "Insufficient disk space. Need at least 2GB free."
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_error "No internet connectivity. Please check your network connection."
        exit 1
    fi
    
    log "Pre-flight checks passed"
}

# Function to check if a package is installed
is_package_installed() {
    dpkg -l "$1" >/dev/null 2>&1
}

# Function to check if a service is running
is_service_running() {
    systemctl is-active --quiet "$1"
}

# Function to wait for service to be ready
wait_for_service() {
    local service=$1
    local timeout=${2:-30}
    local count=0
    
    log_info "Waiting for $service to be ready..."
    while [ $count -lt $timeout ]; do
        if is_service_running "$service"; then
            log "$service is ready"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    log_error "$service failed to start within ${timeout} seconds"
    return 1
}

# Banner
echo -e "${BLUE}"
echo "🍓 RoluATM Raspberry Pi Deployment v2.0"
echo "========================================"
echo "Enhanced deployment script with production best practices"
echo "This script will set up your Pi as a crypto-to-cash kiosk"
echo -e "${NC}"

# Run pre-flight checks
check_prerequisites

# Ask for confirmation
echo -n "Continue with RoluATM deployment? (y/N): "
read -r REPLY
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    cleanup
    exit 0
fi

log "Starting RoluATM deployment..."

# Phase 1: System Updates and Basic Tools
log_step "📦 Phase 1: System setup and updates"

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
    lsb-release \
    htop \
    vim \
    rsync \
    ufw

# Phase 2: Install Node.js with better error handling
log_step "🟢 Phase 2: Installing Node.js 18.x"

# Remove old Node.js if exists
if is_package_installed nodejs; then
    log "Removing existing Node.js installation..."
    sudo apt remove -y nodejs npm 2>/dev/null || true
fi

# Install Node.js 18.x
log "Adding NodeSource repository..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

log "Installing Node.js and npm..."
sudo apt install -y nodejs

# Verify installation
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    log "Node.js installed: $NODE_VERSION, npm: $NPM_VERSION"
else
    log_error "Node.js installation failed"
    exit 1
fi

# Phase 3: Install Python and dependencies
log_step "🐍 Phase 3: Setting up Python environment"

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    python3-psycopg2

PYTHON_VERSION=$(python3 --version)
log "Python installed: $PYTHON_VERSION"

# Phase 4: Install and configure PostgreSQL
log_step "🐘 Phase 4: Setting up PostgreSQL database"

sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Wait for PostgreSQL to be ready
wait_for_service postgresql

log "Creating RoluATM database and user..."
# Use more robust database setup with error checking
sudo -u postgres psql << EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'rolu') THEN
        CREATE USER rolu WITH PASSWORD 'rolu123';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'roluatm') THEN
        CREATE DATABASE roluatm OWNER rolu;
    END IF;
    
    GRANT ALL PRIVILEGES ON DATABASE roluatm TO rolu;
END
\$\$;
EOF

log "PostgreSQL setup complete"

# Phase 5: Install additional tools for Pi
log_step "🔧 Phase 5: Installing Raspberry Pi specific tools"

sudo apt install -y \
    chromium-browser \
    unclutter \
    xdotool \
    minicom \
    screen \
    xinput \
    openbox \
    xorg \
    xinit

# Phase 6: Clone and setup project with better error handling
log_step "📁 Phase 6: Setting up RoluATM project"

# Ensure user home directory exists
sudo mkdir -p "/home/$USER"
sudo chown "$USER:$USER" "/home/$USER"

# Remove existing project if it exists
if [ -d "$PROJECT_DIR" ]; then
    log_warning "Existing project found, backing up..."
    sudo mv "$PROJECT_DIR" "${PROJECT_DIR}.backup.$(date +%s)"
fi

# Clone project
log "Cloning RoluATM project..."
cd "/home/$USER"

# Clone with error handling
if ! git clone https://github.com/abdulrahimiqbal/RoluATM.git; then
    log_error "Failed to clone repository. Check internet connection and repository access."
    exit 1
fi

cd "$PROJECT_DIR"

# Fix ownership recursively
sudo chown -R "$USER:$USER" "$PROJECT_DIR"

# Phase 7: Install project dependencies with better error handling
log_step "📦 Phase 7: Installing project dependencies"

# Check if package.json files exist
if [ ! -f "kiosk-app/package.json" ]; then
    log_error "kiosk-app/package.json not found. Check repository structure."
    exit 1
fi

if [ ! -f "mini-app/package.json" ]; then
    log_error "mini-app/package.json not found. Check repository structure."
    exit 1
fi

log "Installing Node.js dependencies for kiosk app..."
cd kiosk-app
if ! npm install; then
    log_error "Failed to install kiosk-app dependencies"
    exit 1
fi
cd ..

log "Installing Node.js dependencies for mini app..."
cd mini-app
if ! npm install; then
    log_error "Failed to install mini-app dependencies"
    exit 1
fi
cd ..

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    log_warning "requirements.txt not found. Creating basic requirements..."
    cat > requirements.txt << 'EOF'
flask
psycopg2-binary
python-dotenv
uuid
EOF
fi

log "Setting up Python virtual environment..."
python3 -m venv venv

log "Activating virtual environment and installing Python dependencies..."
source venv/bin/activate
if ! pip install -r requirements.txt; then
    log_error "Failed to install Python dependencies"
    exit 1
fi

# Phase 8: Configure environment
log_step "⚙️ Phase 8: Configuring environment"

# Create environment file with validation
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
    log "Environment file created"
else
    log "Environment file already exists, skipping creation"
fi

# Phase 9: Set up database schema with better error handling
log_step "🗄️ Phase 9: Setting up database schema"

log "Testing database connection..."
if ! sudo -u postgres psql -d roluatm -c "SELECT 1;" >/dev/null 2>&1; then
    log_error "Cannot connect to database. Check PostgreSQL installation."
    exit 1
fi

log "Creating database tables..."
# Use a more robust approach for database setup
if command -v python3 >/dev/null 2>&1; then
    python3 << 'EOF'
import sys
try:
    import psycopg2
    
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
    
except Exception as e:
    print(f'Database setup failed: {e}')
    sys.exit(1)
EOF
else
    log_error "Python3 not available for database setup"
    exit 1
fi

# Phase 10: Create systemd services with improvements
log_step "🔧 Phase 10: Creating systemd services"

# Backend service with better configuration
sudo tee /etc/systemd/system/rolu-backend.service > /dev/null << EOF
[Unit]
Description=RoluATM Backend Service
After=network-online.target postgresql.service
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/bin:/usr/local/bin:$PROJECT_DIR/venv/bin
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$PROJECT_DIR/.env.local
ExecStartPre=/bin/sleep 5
ExecStart=$PROJECT_DIR/venv/bin/python pi_backend.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rolu-backend

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

# Kiosk service with better configuration  
sudo tee /etc/systemd/system/rolu-kiosk.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Service
After=network-online.target rolu-backend.service
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR/kiosk-app
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
EnvironmentFile=-$PROJECT_DIR/.env.local
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rolu-kiosk

[Install]
WantedBy=multi-user.target
EOF

# Browser service with enhanced error handling
sudo tee /etc/systemd/system/rolu-browser.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Browser
After=graphical-session.target rolu-kiosk.service
Wants=graphical-session.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
ExecStartPre=/bin/sleep 15
ExecStartPre=/bin/bash -c 'while ! curl -s http://localhost:3000 >/dev/null; do sleep 1; done'
ExecStart=/usr/bin/chromium-browser \
    --start-fullscreen \
    --kiosk \
    --no-toolbar \
    --no-menubar \
    --no-context-menu \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    --disable-component-update \
    --check-for-update-interval=31536000 \
    --overscroll-history-navigation=0 \
    --disable-pinch \
    http://localhost:3000
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable rolu-backend.service
sudo systemctl enable rolu-kiosk.service  
sudo systemctl enable rolu-browser.service

log "Systemd services created and enabled"

# Phase 11: Configure auto-login and kiosk mode
log_step "🖥️ Phase 11: Configuring kiosk mode"

# Enable auto-login with better configuration
sudo systemctl enable getty@tty1.service
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin $USER %I \$TERM
Type=idle
EOF

# Install X11 configuration
sudo apt install -y xserver-xorg-legacy

# Configure X11 permissions
sudo sed -i 's/allowed_users=console/allowed_users=anybody/' /etc/X11/Xwrapper.config

# Configure auto-start X11 and browser with improved error handling
if [ ! -f "/home/$USER/.xinitrc" ]; then
    cat > "/home/$USER/.xinitrc" << 'EOF'
#!/bin/bash
# Start X11 configuration for kiosk mode
xset -dpms     # disable DPMS (Energy Star) features
xset s off     # disable screen saver  
xset s noblank # don't blank the video device
unclutter -idle 1 -root &

# Hide cursor completely in kiosk mode
unclutter -display :0 -noevents -grab &

# Start openbox window manager
exec openbox-session
EOF
    chmod +x "/home/$USER/.xinitrc"
    log "Created .xinitrc for kiosk mode"
fi

# Auto-start X11 in .bashrc with safety checks
if ! grep -q "startx" "/home/$USER/.bashrc"; then
    cat >> "/home/$USER/.bashrc" << 'EOF'

# Auto-start X11 for kiosk mode
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    # Check if X11 is already running
    if ! pgrep -x "Xorg" > /dev/null; then
        startx
    fi
fi
EOF
    log "Added X11 auto-start to .bashrc"
fi

# Configure basic firewall
log_step "🔥 Phase 11.5: Basic firewall configuration"
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 3000/tcp comment "Kiosk app"
sudo ufw allow 8000/tcp comment "Backend API"
log "Basic firewall configured"

# Phase 12: Final setup and validation
log_step "✅ Phase 12: Final configuration and testing"

# Test database connection
log "Testing database connection..."
if python3 -c "import psycopg2; psycopg2.connect('postgresql://rolu:rolu123@localhost:5432/roluatm')" 2>/dev/null; then
    log "Database connection test passed"
else
    log_error "Database connection test failed"
    exit 1
fi

# Start services with proper ordering
log "Starting services..."

# Start backend first
sudo systemctl start rolu-backend.service
wait_for_service rolu-backend.service

# Test backend health
log "Testing backend health..."
sleep 5
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    log "Backend health check passed"
else
    log_warning "Backend health check failed, but continuing..."
fi

# Start kiosk service
sudo systemctl start rolu-kiosk.service
wait_for_service rolu-kiosk.service

# Show status with detailed information
log_step "📊 Service Status Check"
for service in rolu-backend rolu-kiosk; do
    if systemctl is-active --quiet "$service"; then
        log "✅ $service: Running"
        systemctl status "$service" --no-pager -l | head -3 >> "$LOG_FILE"
    else
        log_error "❌ $service: Failed"
        systemctl status "$service" --no-pager -l >> "$LOG_FILE"
    fi
done

# Create helpful scripts
log "Creating utility scripts..."
cat > "/home/$USER/rolu-status.sh" << 'EOF'
#!/bin/bash
echo "=== RoluATM System Status ==="
echo "Services:"
for service in rolu-backend rolu-kiosk rolu-browser; do
    status=$(systemctl is-active $service)
    echo "  $service: $status"
done

echo ""
echo "Network:"
echo "  Backend: $(curl -s http://localhost:8000/health >/dev/null && echo 'OK' || echo 'FAIL')"
echo "  Kiosk: $(curl -s http://localhost:3000 >/dev/null && echo 'OK' || echo 'FAIL')"

echo ""  
echo "System:"
echo "  Uptime: $(uptime -p)"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | awk 'NR==2{printf "%.1f%%\n", $3*100/$2}')"
echo "  Disk: $(df -h / | awk 'NR==2{print $5}')"
EOF

chmod +x "/home/$USER/rolu-status.sh"

cat > "/home/$USER/rolu-restart.sh" << 'EOF'
#!/bin/bash
echo "Restarting RoluATM services..."
sudo systemctl restart rolu-backend.service
sleep 5
sudo systemctl restart rolu-kiosk.service
echo "Services restarted. Check status with: ./rolu-status.sh"
EOF

chmod +x "/home/$USER/rolu-restart.sh"

# Final summary
echo -e "${GREEN}"
echo "🎉 RoluATM Deployment Complete!"
echo "================================"
echo ""
echo "✅ Backend running on: http://localhost:8000"
echo "✅ Kiosk app running on: http://localhost:3000"
echo "✅ Database: PostgreSQL (local)"
echo "✅ Services: Auto-start enabled"
echo "✅ Firewall: Configured"
echo "✅ Kiosk mode: Ready"
echo ""
echo "📱 Access your kiosk at: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "🔧 Useful commands:"
echo "   ./rolu-status.sh     - Check system status"
echo "   ./rolu-restart.sh    - Restart services"
echo "   sudo systemctl status rolu-backend"
echo "   sudo systemctl status rolu-kiosk"
echo "   journalctl -u rolu-backend -f"
echo ""
echo "📋 Logs available at: $LOG_FILE"
echo ""
echo "🔄 Reboot to enable full kiosk mode:"
echo "   sudo reboot"
echo ""
echo "⚠️  Remember to:"
echo "   1. Update .env.local with your actual World ID credentials"
echo "   2. Test the T-Flex hardware connection"
echo "   3. Verify the touchscreen calibration"
echo -e "${NC}"

log "RoluATM deployment completed successfully!"
log "System ready for production use after reboot"

# Clean up
cleanup 