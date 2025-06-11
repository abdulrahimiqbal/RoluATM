# 🍓 RoluATM Raspberry Pi Deployment Guide

## 🎯 Quick Overview

This guide will set up your Raspberry Pi 4B as a complete crypto-to-cash kiosk with:
- 7" touchscreen interface
- T-Flex coin dispenser control
- Local PostgreSQL database
- World ID verification via production mini app
- Auto-start kiosk mode

## 📦 Prerequisites

### Hardware
- ✅ Raspberry Pi 4B (4GB+ RAM recommended)
- ✅ 7" Touch Screen Display
- ✅ 16GB+ microSD card
- ✅ T-Flex coin dispenser with USB connection
- ✅ Stable internet connection

### Software Setup
- Raspberry Pi OS with Desktop (64-bit)
- SSH enabled for remote setup
- User account: `pi`

## 🚀 One-Command Deployment

### Step 1: Flash Raspberry Pi OS
1. Use [Raspberry Pi Imager](https://rpi.org/imager)
2. Choose "Raspberry Pi OS with Desktop (64-bit)"
3. Configure SSH, WiFi, and user credentials before flashing

### Step 2: SSH into Your Pi
```bash
ssh pi@[YOUR_PI_IP_ADDRESS]
```

### Step 3: Deploy RoluATM
```bash
# Download and run the deployment script
curl -fsSL https://raw.githubusercontent.com/abdulrahimiqbal/RoluATM/main/deploy-to-pi.sh | bash
```

**That's it!** The script will automatically:
- Install all dependencies (Node.js, Python, PostgreSQL)
- Clone your project from GitHub
- Set up the database
- Configure kiosk mode
- Install hardware drivers

## ⚙️ Manual Configuration

After deployment, configure your environment:

```bash
cd /home/pi/RoluATM
nano .env.local
```

**Update these values:**
```env
# Your actual World ID credentials
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19

# T-Flex port (check with: ls /dev/ttyUSB*)
TFLEX_PORT=/dev/ttyUSB0

# Set to false for production
DEV_MODE=false
```

## 🧪 Testing Your Setup

### Test 1: Run Deployment Test
```bash
cd /home/pi/RoluATM
./test-pi-deployment.sh
```

### Test 2: Start Backend Manually
```bash
cd /home/pi/RoluATM
source venv/bin/activate
python3 pi_backend.py
```

### Test 3: Full Kiosk Mode
```bash
cd /home/pi/RoluATM
./start-kiosk.sh
```

## 🔧 Hardware Setup

### Connect T-Flex Dispenser
1. Connect T-Flex to Pi via USB
2. Check connection: `ls /dev/ttyUSB*`
3. Test communication: `sudo minicom -D /dev/ttyUSB0 -b 9600`

### Configure Touch Screen
The 7" display should work automatically. If not:
```bash
# Check touch input
xinput list

# Calibrate if needed
xinput_calibrator
```

## 🚦 Auto-Start Configuration

### Enable Auto-Start on Boot
```bash
sudo systemctl start rolu-kiosk.service
sudo systemctl enable rolu-kiosk.service
```

### Disable Auto-Start
```bash
sudo systemctl stop rolu-kiosk.service
sudo systemctl disable rolu-kiosk.service
```

### Check Service Status
```bash
sudo systemctl status rolu-kiosk.service
```

## 📊 Monitoring and Logs

### View Live Logs
```bash
# Kiosk logs
tail -f /home/pi/RoluATM/logs/kiosk.log

# Backend logs
tail -f /home/pi/RoluATM/logs/backend.log

# System logs
sudo journalctl -u rolu-kiosk.service -f
```

### Check System Status
```bash
# Check all services
systemctl --user status

# Check database
sudo -u postgres psql -c "\l"

# Check disk space
df -h

# Check memory
free -h
```

## 🔨 Troubleshooting

### Common Issues

**1. T-Flex Not Detected**
```bash
# Check USB devices
lsusb

# Check serial permissions
sudo usermod -a -G dialout pi
# Logout and login again
```

**2. Database Connection Error**
```bash
# Restart PostgreSQL
sudo systemctl restart postgresql

# Check database status
sudo systemctl status postgresql

# Recreate database
sudo -u postgres dropdb roluatm
sudo -u postgres createdb roluatm -O rolu
```

**3. Touch Screen Not Working**
```bash
# Check display
DISPLAY=:0 xrandr

# Calibrate touch
sudo apt install xinput-calibrator
DISPLAY=:0 xinput_calibrator
```

**4. Kiosk Won't Start**
```bash
# Check logs
sudo journalctl -u rolu-kiosk.service --no-pager

# Test manually
cd /home/pi/RoluATM
./start-kiosk.sh
```

### Manual Recovery

**Reset Everything:**
```bash
# Stop services
sudo systemctl stop rolu-kiosk.service

# Backup current installation
sudo mv /home/pi/RoluATM /home/pi/RoluATM.backup

# Re-run deployment
curl -fsSL https://raw.githubusercontent.com/abdulrahimiqbal/RoluATM/main/deploy-to-pi.sh | bash
```

## 🏗️ File Structure

After deployment:
```
/home/pi/RoluATM/
├── kiosk-app/          # React kiosk interface
├── mini-app/           # Mini app (for reference)
├── logs/               # Application logs
├── venv/               # Python virtual environment
├── pi_backend.py       # Main Pi backend server
├── start-kiosk.sh      # Kiosk startup script
├── .env.local          # Environment configuration
├── schema.sql          # Database schema
└── deploy-to-pi.sh     # Deployment script
```

## 🔄 Updates and Maintenance

### Update RoluATM Code
```bash
cd /home/pi/RoluATM
git pull origin main
npm install
pip install -r requirements.txt
npm run build
sudo systemctl restart rolu-kiosk.service
```

### System Updates
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

### Database Backup
```bash
# Backup
pg_dump -U rolu roluatm > backup.sql

# Restore
psql -U rolu roluatm < backup.sql
```

## 📱 Production URLs

Your Pi will connect to these production services:
- **Mini App:** https://mini-app-azure.vercel.app
- **Kiosk Interface:** http://localhost:3000 (local)
- **Backend API:** http://localhost:8000 (local)

## 🎉 Success!

When everything is working:
1. **Boot:** Pi starts automatically into kiosk mode
2. **Display:** 7" touchscreen shows amount selection
3. **QR Code:** Generated pointing to production mini app
4. **Verification:** World ID verification in World App
5. **Dispensing:** T-Flex dispenses quarters
6. **Complete:** Transaction recorded in local database

Your crypto-to-cash kiosk is now ready for customers! 🪙 