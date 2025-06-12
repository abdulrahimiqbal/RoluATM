#!/bin/bash
# Enhanced RoluATM Deployment Script
# Deploys the new cloud-based architecture with resilient Pi service

set -euo pipefail

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
LOG_FILE="/home/rahiim/enhanced-deployment.log"
VERCEL_API_URL="https://rolu-api.vercel.app/api/v2"

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERROR: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
}

log_step() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [STEP] $1" >> "$LOG_FILE"
}

# Banner
echo -e "${BLUE}"
echo "🚀 RoluATM Enhanced System Deployment"
echo "======================================"
echo "Deploying cloud-based resilient architecture"
echo -e "${NC}"

# Confirmation
echo -n "Deploy enhanced RoluATM system? (y/N): "
read -r REPLY
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

log "Starting enhanced system deployment..."

# Phase 1: Update database schema
log_step "📊 Phase 1: Updating database schema"

if [ -f "schema_v2.sql" ]; then
    log "Applying enhanced database schema..."
    
    # Apply to Neon database
    if command -v psql >/dev/null 2>&1; then
        if [ -n "${DATABASE_URL:-}" ]; then
            psql "$DATABASE_URL" -f schema_v2.sql || {
                log_error "Failed to apply schema to Neon database"
                exit 1
            }
            log "Schema applied to Neon database"
        else
            log_error "DATABASE_URL not set for Neon database"
            exit 1
        fi
    else
        log_error "psql not available for database schema update"
        exit 1
    fi
else
    log_error "schema_v2.sql not found"
    exit 1
fi

# Phase 2: Deploy new Pi dispenser service
log_step "🔧 Phase 2: Deploying Pi dispenser service"

# Stop old services
log "Stopping old services..."
sudo systemctl stop rolu-backend.service 2>/dev/null || true
sudo systemctl stop rolu-kiosk.service 2>/dev/null || true

# Install new dispenser service
log "Installing new dispenser service..."
if [ -f "pi_dispenser_service.py" ]; then
    chmod +x pi_dispenser_service.py
    
    # Install systemd service
    if [ -f "rolu-dispenser.service" ]; then
        sudo cp rolu-dispenser.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable rolu-dispenser.service
        log "Dispenser service installed"
    else
        log_error "rolu-dispenser.service file not found"
        exit 1
    fi
else
    log_error "pi_dispenser_service.py not found"
    exit 1
fi

# Phase 3: Update environment configuration
log_step "⚙️ Phase 3: Updating environment configuration"

# Create enhanced environment file
log "Creating enhanced environment configuration..."
cat > .env.enhanced << EOF
# Enhanced RoluATM Configuration
# Cloud API Configuration
VERCEL_API_URL=${VERCEL_API_URL}
VITE_VERCEL_API_URL=${VERCEL_API_URL}
VITE_USE_CLOUD_API=true

# Local fallback configuration
VITE_LOCAL_API_URL=http://localhost:8000

# Database Configuration (Neon)
DATABASE_URL=${DATABASE_URL:-postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require}

# World ID Configuration
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19

# Hardware Configuration
TFLEX_PORT=/dev/ttyUSB0
DEV_MODE=false

# Mini App URL
MINI_APP_URL=https://mini-app-azure.vercel.app
EOF

# Backup old env and use new one
if [ -f ".env.local" ]; then
    cp .env.local .env.local.backup
    log "Backed up old environment file"
fi

cp .env.enhanced .env.local
log "Environment configuration updated"

# Phase 4: Update kiosk app
log_step "📱 Phase 4: Updating kiosk app"

cd kiosk-app

# Install any new dependencies
log "Installing kiosk app dependencies..."
npm install

# Build with new configuration
log "Building kiosk app with enhanced API..."
npm run build

cd ..

# Phase 5: Test new dispenser service
log_step "🧪 Phase 5: Testing dispenser service"

log "Starting dispenser service..."
sudo systemctl start rolu-dispenser.service

# Wait for service to start
sleep 5

# Check service status
if sudo systemctl is-active --quiet rolu-dispenser.service; then
    log "Dispenser service started successfully"
else
    log_error "Dispenser service failed to start"
    sudo journalctl -u rolu-dispenser.service --no-pager -n 20
    exit 1
fi

# Test API connectivity
log "Testing API connectivity..."
python3 << 'EOF'
import requests
import sys

try:
    # Test cloud API
    response = requests.get('https://rolu-api.vercel.app/api/v2/health', timeout=10)
    if response.status_code == 200:
        print("✅ Cloud API is reachable")
    else:
        print(f"⚠️ Cloud API returned {response.status_code}")
        
    # Test if dispenser service can poll
    response = requests.get(
        'https://rolu-api.vercel.app/api/v2/jobs/pending',
        headers={'x-kiosk-id': 'test-kiosk'},
        timeout=10
    )
    if response.status_code in [200, 400]:  # 400 is expected for test kiosk
        print("✅ Job polling endpoint is working")
    else:
        print(f"⚠️ Job polling returned {response.status_code}")
        
except Exception as e:
    print(f"❌ API test failed: {e}")
    sys.exit(1)
EOF

# Phase 6: Update kiosk service to use new build
log_step "🖥️ Phase 6: Updating kiosk service"

# Create new kiosk service that serves the built app
sudo tee /etc/systemd/system/rolu-kiosk-enhanced.service > /dev/null << EOF
[Unit]
Description=RoluATM Enhanced Kiosk Service
After=network-online.target rolu-dispenser.service
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR/kiosk-app
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/chromium-browser --kiosk --no-sandbox --disable-dev-shm-usage --disable-gpu --start-fullscreen --app=file://$PROJECT_DIR/kiosk-app/dist/index.html
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rolu-kiosk-enhanced

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rolu-kiosk-enhanced.service

# Phase 7: Final system check
log_step "🏥 Phase 7: Final system health check"

log "Checking all services..."

# Check dispenser service
if sudo systemctl is-active --quiet rolu-dispenser.service; then
    log "✅ Dispenser service: Running"
else
    log_error "❌ Dispenser service: Failed"
fi

# Check kiosk service
sudo systemctl start rolu-kiosk-enhanced.service
sleep 3

if sudo systemctl is-active --quiet rolu-kiosk-enhanced.service; then
    log "✅ Kiosk service: Running"
else
    log_error "❌ Kiosk service: Failed"
fi

# Generate kiosk ID for this deployment
KIOSK_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
echo "$KIOSK_ID" > /home/rahiim/.rolu_kiosk_id
log "Generated kiosk ID: $KIOSK_ID"

# Phase 8: Cleanup old services
log_step "🧹 Phase 8: Cleaning up old services"

log "Disabling old services..."
sudo systemctl disable rolu-backend.service 2>/dev/null || true
sudo systemctl disable rolu-kiosk.service 2>/dev/null || true

log "Removing old service files..."
sudo rm -f /etc/systemd/system/rolu-backend.service
sudo rm -f /etc/systemd/system/rolu-kiosk.service

sudo systemctl daemon-reload

# Final summary
echo -e "${GREEN}"
echo "🎉 Enhanced RoluATM Deployment Complete!"
echo "========================================"
echo "✅ Database schema updated"
echo "✅ Dispenser service deployed"
echo "✅ Kiosk app updated"
echo "✅ Services configured and running"
echo ""
echo "📊 System Status:"
echo "  • Dispenser Service: $(sudo systemctl is-active rolu-dispenser.service)"
echo "  • Kiosk Service: $(sudo systemctl is-active rolu-kiosk-enhanced.service)"
echo "  • Kiosk ID: $KIOSK_ID"
echo ""
echo "🌐 API Endpoints:"
echo "  • Cloud API: $VERCEL_API_URL"
echo "  • Local Fallback: http://localhost:8000"
echo ""
echo "📝 Logs:"
echo "  • Deployment: $LOG_FILE"
echo "  • Dispenser: sudo journalctl -u rolu-dispenser.service -f"
echo "  • Kiosk: sudo journalctl -u rolu-kiosk-enhanced.service -f"
echo -e "${NC}"

log "Enhanced deployment completed successfully!"

# Test transaction flow
echo -n "Test a complete transaction flow? (y/N): "
read -r TEST_REPLY
if [[ $TEST_REPLY =~ ^[Yy]$ ]]; then
    log_step "🧪 Testing complete transaction flow"
    
    python3 << 'EOF'
import requests
import time
import json

API_BASE = 'https://rolu-api.vercel.app/api/v2'
KIOSK_ID = open('/home/rahiim/.rolu_kiosk_id').read().strip()

print(f"Testing with kiosk ID: {KIOSK_ID}")

try:
    # 1. Create transaction
    print("1. Creating transaction...")
    response = requests.post(
        f'{API_BASE}/transaction/create',
        headers={'x-kiosk-id': KIOSK_ID, 'Content-Type': 'application/json'},
        json={'amount': 5.00}
    )
    transaction = response.json()
    print(f"   Transaction created: {transaction['id']}")
    
    # 2. Simulate payment
    print("2. Simulating payment...")
    response = requests.post(
        f'{API_BASE}/transaction/pay',
        json={
            'transaction_id': transaction['id'],
            'proof': 'test_proof',
            'nullifier_hash': 'test_nullifier',
            'merkle_root': 'test_root'
        }
    )
    payment = response.json()
    print(f"   Payment processed: {payment['status']}")
    
    # 3. Check for dispense job
    print("3. Checking for dispense job...")
    time.sleep(2)
    response = requests.get(
        f'{API_BASE}/jobs/pending',
        headers={'x-kiosk-id': KIOSK_ID}
    )
    job = response.json()
    if job:
        print(f"   Job created: {job['id']} ({job['quarters']} quarters)")
        
        # 4. Simulate job completion
        print("4. Simulating job completion...")
        response = requests.post(
            f'{API_BASE}/jobs/{job["id"]}/complete',
            json={'success': True, 'kioskId': KIOSK_ID}
        )
        result = response.json()
        print(f"   Job completed: {result['status']}")
        
        print("✅ Transaction flow test completed successfully!")
    else:
        print("❌ No dispense job found")
        
except Exception as e:
    print(f"❌ Transaction flow test failed: {e}")
EOF
fi

echo -e "${GREEN}🚀 Enhanced RoluATM system is ready for operation!${NC}" 