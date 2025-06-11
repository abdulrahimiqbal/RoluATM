#!/bin/bash

echo "🥧 RoluATM Pi Setup Script"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️  This script is designed for Raspberry Pi${NC}"
    echo "Continuing anyway..."
fi

echo -e "${BLUE}🔧 Setting up RoluATM on Raspberry Pi...${NC}"

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Install required packages
echo -e "${BLUE}📦 Installing required packages...${NC}"
sudo apt install -y python3-pip python3-venv nodejs npm postgresql-client git curl

# Install Python dependencies
echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install psycopg2-binary requests

# Build kiosk app
echo -e "${BLUE}⚛️  Building kiosk app...${NC}"
cd kiosk-app
npm install
npm run build
cd ..

# Create systemd service for backend
echo -e "${BLUE}🔧 Creating systemd service...${NC}"
sudo tee /etc/systemd/system/rolu-backend.service > /dev/null << EOF
[Unit]
Description=RoluATM Backend Service
After=network.target

[Service]
Type=simple
User=rahiim
WorkingDirectory=/home/rahiim/RoluATM
Environment=WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19
Environment=DATABASE_URL=postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require
Environment=DEV_MODE=false
Environment=MINI_APP_URL=https://mini-app-azure.vercel.app
Environment=TFLEX_PORT=/dev/ttyUSB0
ExecStart=/home/rahiim/RoluATM/venv/bin/python /home/rahiim/RoluATM/pi_backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for kiosk
sudo tee /etc/systemd/system/rolu-kiosk.service > /dev/null << EOF
[Unit]
Description=RoluATM Kiosk Web Server
After=network.target

[Service]
Type=simple
User=rahiim
WorkingDirectory=/home/rahiim/RoluATM/kiosk-app/dist
ExecStart=/usr/bin/python3 -m http.server 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable rolu-backend.service
sudo systemctl enable rolu-kiosk.service

# Create desktop autostart for kiosk mode (optional)
echo -e "${BLUE}🖥️  Setting up kiosk mode...${NC}"
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/rolu-kiosk.desktop << EOF
[Desktop Entry]
Type=Application
Name=RoluATM Kiosk
Exec=chromium-browser --kiosk --no-sandbox --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://localhost:3000
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Create management scripts
echo -e "${BLUE}📝 Creating management scripts...${NC}"

# Start script
cat > start-pi-services.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting RoluATM services..."
sudo systemctl start rolu-backend.service
sudo systemctl start rolu-kiosk.service
sleep 3
echo "✅ Services started"
echo "Backend: http://localhost:8000"
echo "Kiosk:   http://localhost:3000"
EOF

# Stop script
cat > stop-pi-services.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping RoluATM services..."
sudo systemctl stop rolu-backend.service
sudo systemctl stop rolu-kiosk.service
echo "✅ Services stopped"
EOF

# Status script
cat > check-pi-status.sh << 'EOF'
#!/bin/bash
echo "📊 RoluATM Service Status"
echo "========================"
echo "Backend Service:"
sudo systemctl status rolu-backend.service --no-pager -l
echo ""
echo "Kiosk Service:"
sudo systemctl status rolu-kiosk.service --no-pager -l
echo ""
echo "🌐 Network Test:"
curl -s http://localhost:8000/health || echo "Backend not responding"
echo ""
echo "📝 Recent Logs:"
echo "Backend:"
sudo journalctl -u rolu-backend.service --no-pager -n 5
echo ""
echo "Kiosk:"
sudo journalctl -u rolu-kiosk.service --no-pager -n 5
EOF

chmod +x start-pi-services.sh stop-pi-services.sh check-pi-status.sh

echo -e "${GREEN}🎉 Pi setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Start services: ./start-pi-services.sh"
echo "2. Check status:   ./check-pi-status.sh"
echo "3. Stop services:  ./stop-pi-services.sh"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "Backend API: http://192.168.1.250:8000"
echo "Kiosk App:   http://192.168.1.250:3000"
echo ""
echo -e "${BLUE}🔧 Service Management:${NC}"
echo "sudo systemctl start/stop/restart rolu-backend.service"
echo "sudo systemctl start/stop/restart rolu-kiosk.service"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo "sudo journalctl -u rolu-backend.service -f"
echo "sudo journalctl -u rolu-kiosk.service -f" 