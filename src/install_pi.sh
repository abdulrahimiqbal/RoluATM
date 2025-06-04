#!/bin/bash
# WorldCash Kiosk Installation Script for Raspberry Pi 4B
# One-shot deployment script for production setup

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_USER="pi"
SERVICE_USER="worldcash"
KIOSK_MODE="${KIOSK_MODE:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_pi() {
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        warn "This doesn't appear to be a Raspberry Pi - continuing anyway"
    fi
}

install_system_packages() {
    log "Updating system packages..."
    apt update
    apt upgrade -y
    
    log "Installing required system packages..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        nginx \
        git \
        curl \
        build-essential \
        pkg-config \
        chromium-browser \
        xorg \
        openbox \
        lightdm \
        unclutter \
        udev
    
    success "System packages installed"
}

setup_user() {
    log "Setting up service user..."
    
    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d /opt/worldcash "$SERVICE_USER"
        success "Created service user: $SERVICE_USER"
    fi
    
    # Add pi user to dialout group for serial access
    usermod -a -G dialout "$INSTALL_USER"
    success "Added $INSTALL_USER to dialout group"
}

setup_python_environment() {
    log "Setting up Python environment..."
    
    # Create application directory
    mkdir -p /opt/worldcash
    cd /opt/worldcash
    
    # Copy source files
    cp -r "$PROJECT_ROOT"/* /opt/worldcash/
    
    # Create Python virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" /opt/worldcash
    chmod +x /opt/worldcash/src/backend/app.py
    
    success "Python environment configured"
}

build_frontend() {
    log "Building frontend..."
    
    cd /opt/worldcash
    
    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
    
    # Install dependencies and build
    npm install
    npm run build
    
    success "Frontend built successfully"
}

configure_nginx() {
    log "Configuring nginx..."
    
    # Generate self-signed certificate
    mkdir -p /etc/ssl/certs /etc/ssl/private
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/worldcash.key \
        -out /etc/ssl/certs/worldcash.crt \
        -subj "/C=US/ST=State/L=City/O=WorldCash/CN=worldcash.local"
    
    # Create nginx site configuration
    cat > /etc/nginx/sites-available/worldcash << 'EOF'
server {
    listen 80;
    listen 443 ssl;
    server_name _;
    
    ssl_certificate /etc/ssl/certs/worldcash.crt;
    ssl_certificate_key /etc/ssl/private/worldcash.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend static files
    location / {
        root /opt/worldcash/dist/public;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for hardware operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/worldcash /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    systemctl enable nginx
    systemctl restart nginx
    
    success "Nginx configured with TLS"
}

setup_systemd_services() {
    log "Setting up systemd services..."
    
    # WorldCash backend service
    cat > /etc/systemd/system/worldcash.service << EOF
[Unit]
Description=WorldCash Crypto-to-Cash Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=/opt/worldcash
Environment=PATH=/opt/worldcash/venv/bin
Environment=PYTHONPATH=/opt/worldcash
ExecStart=/opt/worldcash/venv/bin/python /opt/worldcash/src/backend/app.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/worldcash
PrivateTmp=true

# Resource limits
LimitNOFILE=1024
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF
    
    # Kiosk mode service (only if KIOSK_MODE is true)
    if [[ "$KIOSK_MODE" == "true" ]]; then
        cat > /etc/systemd/system/kiosk-chromium.service << 'EOF'
[Unit]
Description=Chromium Kiosk Mode
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=pi
Group=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    --disable-field-trial-config \
    --force-fieldtrials="*BackgroundTracing/default/" \
    --aggressive-cache-discard \
    --disable-background-networking \
    --disable-default-apps \
    --disable-extensions \
    --disable-sync \
    --disable-background-mode \
    --autoplay-policy=no-user-gesture-required \
    --start-fullscreen \
    --window-position=0,0 \
    --window-size=1920,1080 \
    https://localhost
Restart=always
RestartSec=5

[Install]
WantedBy=graphical-session.target
EOF
    fi
    
    # Enable services
    systemctl daemon-reload
    systemctl enable worldcash.service
    
    if [[ "$KIOSK_MODE" == "true" ]]; then
        systemctl enable kiosk-chromium.service
    fi
    
    success "Systemd services configured"
}

configure_boot_settings() {
    log "Configuring Raspberry Pi boot settings..."
    
    # Update config.txt for optimal performance
    BOOT_CONFIG="/boot/firmware/config.txt"
    if [[ ! -f "$BOOT_CONFIG" ]]; then
        BOOT_CONFIG="/boot/config.txt"  # Fallback for older Pi OS versions
    fi
    
    if [[ -f "$BOOT_CONFIG" ]]; then
        # Backup original config
        cp "$BOOT_CONFIG" "${BOOT_CONFIG}.backup"
        
        # Add GPU memory and display settings
        cat >> "$BOOT_CONFIG" << 'EOF'

# WorldCash Kiosk Settings
gpu_mem=128
dtoverlay=vc4-kms-v3d
max_framebuffers=2

# Disable unnecessary features
dtparam=audio=off
camera_auto_detect=0
display_auto_detect=0

# USB settings for hardware reliability
dwc_otg.speed=1
dwc_otg.lpm_enable=0
EOF
        
        success "Boot configuration updated"
    else
        warn "Boot config file not found - skipping boot settings"
    fi
}

setup_udev_rules() {
    log "Setting up udev rules for hardware..."
    
    # T-Flex coin dispenser udev rule
    cat > /etc/udev/rules.d/99-tflex.rules << 'EOF'
# Telequip T-Flex Coin Dispenser
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="tflex", GROUP="dialout", MODE="0664"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="dialout", MODE="0664"

# Generic USB-Serial for T-Flex (fallback)
SUBSYSTEM=="tty", ATTRS{interface}=="FT232R USB UART", SYMLINK+="tflex-uart", GROUP="dialout", MODE="0664"
EOF
    
    # Reload udev rules
    udevadm control --reload-rules
    udevadm trigger
    
    success "Udev rules configured"
}

setup_environment() {
    log "Setting up environment configuration..."
    
    # Create environment file
    cat > /opt/worldcash/.env << 'EOF'
# WorldCash Production Environment
DEV_MODE=false
TFLEX_PORT=/dev/ttyACM0
WORLD_API_URL=https://id.worldcoin.org/api/v1
WALLET_API_URL=https://wallet.example.com
FX_URL=https://api.kraken.com/0/public/Ticker?pair=WBTCUSD
FIAT_DENOM=USD
PORT=8000
HOST=127.0.0.1

# Security
MAX_WITHDRAWAL_USD=500.00
MIN_WITHDRAWAL_USD=1.00

# Timeouts
WORLD_ID_TIMEOUT=30
WALLET_TIMEOUT=10
DISPENSE_TIMEOUT=30
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" /opt/worldcash/.env
    chmod 600 /opt/worldcash/.env
    
    success "Environment configuration created"
}

configure_kiosk_desktop() {
    if [[ "$KIOSK_MODE" != "true" ]]; then
        return
    fi
    
    log "Configuring kiosk desktop environment..."
    
    # Configure lightdm for auto-login
    cat > /etc/lightdm/lightdm.conf.d/01-autologin.conf << 'EOF'
[Seat:*]
autologin-user=pi
autologin-user-timeout=0
user-session=openbox
EOF
    
    # Create openbox autostart for pi user
    sudo -u pi mkdir -p /home/pi/.config/openbox
    cat > /home/pi/.config/openbox/autostart << 'EOF'
# Hide cursor
unclutter -idle 0.1 -root &

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Start WorldCash kiosk
systemctl --user start kiosk-chromium
EOF
    
    chown pi:pi /home/pi/.config/openbox/autostart
    
    # Enable user service for kiosk
    sudo -u pi systemctl --user enable kiosk-chromium.service
    
    success "Kiosk desktop environment configured"
}

start_services() {
    log "Starting services..."
    
    # Start backend service
    systemctl start worldcash.service
    
    # Check service status
    if systemctl is-active --quiet worldcash.service; then
        success "WorldCash backend service started"
    else
        error "Failed to start WorldCash backend service"
        systemctl status worldcash.service
        exit 1
    fi
    
    # Start nginx
    systemctl restart nginx
    
    if systemctl is-active --quiet nginx; then
        success "Nginx web server started"
    else
        error "Failed to start nginx"
        exit 1
    fi
}

run_tests() {
    log "Running system tests..."
    
    # Test Python backend
    cd /opt/worldcash
    source venv/bin/activate
    
    # Test T-Flex connection (will use mock mode if hardware not present)
    python3 -c "
from src.backend.driver_tflex import TFlex
try:
    tflex = TFlex()
    status = tflex.status()
    print(f'T-Flex status: {status}')
    print('T-Flex driver test: PASS')
except Exception as e:
    print(f'T-Flex driver test: FAIL - {e}')
"
    
    # Test web server response
    sleep 5  # Give services time to start
    if curl -k -s https://localhost/health >/dev/null; then
        success "Web server health check: PASS"
    else
        warn "Web server health check: FAIL"
    fi
    
    # Test API endpoint
    if curl -k -s https://localhost/api/status >/dev/null; then
        success "API endpoint test: PASS"
    else
        warn "API endpoint test: FAIL"
    fi
}

cleanup() {
    log "Cleaning up..."
    
    # Remove build artifacts
    cd /opt/worldcash
    rm -rf node_modules
    rm -rf .git
    
    # Clear package caches
    apt autoremove -y
    apt autoclean
    
    success "Cleanup completed"
}

main() {
    log "Starting WorldCash Kiosk installation on Raspberry Pi..."
    
    check_root
    check_pi
    
    install_system_packages
    setup_user
    setup_python_environment
    build_frontend
    configure_nginx
    setup_systemd_services
    configure_boot_settings
    setup_udev_rules
    setup_environment
    configure_kiosk_desktop
    start_services
    run_tests
    cleanup
    
    success "WorldCash Kiosk installation completed!"
    
    echo ""
    echo "=============================================="
    echo "  WorldCash Kiosk Installation Complete"
    echo "=============================================="
    echo ""
    echo "Services:"
    echo "  Backend:  systemctl status worldcash"
    echo "  Web:      systemctl status nginx"
    if [[ "$KIOSK_MODE" == "true" ]]; then
        echo "  Kiosk:    systemctl status kiosk-chromium"
    fi
    echo ""
    echo "URLs:"
    echo "  Local:    https://localhost"
    echo "  Network:  https://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "Logs:"
    echo "  Backend:  journalctl -u worldcash -f"
    echo "  Web:      journalctl -u nginx -f"
    echo ""
    echo "Configuration:"
    echo "  App:      /opt/worldcash/.env"
    echo "  Web:      /etc/nginx/sites-available/worldcash"
    echo ""
    if [[ "$KIOSK_MODE" == "true" ]]; then
        echo "KIOSK MODE: System will auto-start in kiosk mode after reboot"
        echo "To disable: sudo systemctl disable kiosk-chromium"
    fi
    echo ""
    echo "Reboot recommended to ensure all settings take effect."
}

# Handle script interruption
trap 'error "Installation interrupted"; exit 1' INT TERM

# Run main installation
main "$@"
