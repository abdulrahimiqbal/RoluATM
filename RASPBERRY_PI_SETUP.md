# RoluATM Raspberry Pi 4B Setup Guide

## 🎯 Overview
This guide walks you through setting up your RoluATM crypto-to-cash kiosk on your Raspberry Pi 4B with the 7" touchscreen display you've purchased.

## 📦 Hardware You Have
Based on your orders:
- ✅ Raspberry Pi 4B Starter Kit (4GB RAM, 16GB microSD)
- ✅ Raspberry Pi 7" Touch Screen Display
- ✅ USB cables and power supply
- ✅ HDMI cable and case

## 🔧 Additional Hardware Needed
- **Telequip T-Flex coin dispenser** (for cash dispensing)
- **USB-to-Serial adapter** (if T-Flex uses RS232)
- **Stable internet connection** (WiFi or Ethernet)

## 🚀 Deployment Options

### Option 1: Full Local Deployment (Recommended)
Run everything on the Pi for maximum control and offline capability.

### Option 2: Hybrid with Vercel Frontend
Use Vercel for the frontend, local backend on Pi for hardware control.

## 📋 Step-by-Step Setup

### Phase 1: Raspberry Pi OS Setup

1. **Flash Raspberry Pi OS**
   ```bash
   # Use Raspberry Pi Imager to flash the microSD card
   # Choose "Raspberry Pi OS with Desktop (64-bit)"
   # Enable SSH and set username/password
   ```

2. **Initial Pi Configuration**
   ```bash
   # Connect your 7" display via ribbon cable
   # Boot up and run initial setup
   sudo raspi-config
   
   # Enable SSH, I2C, Serial (for T-Flex)
   # Set up WiFi if needed
   # Update system
   sudo apt update && sudo apt upgrade -y
   ```

3. **Install Required Software**
   ```bash
   # Install Node.js 18+
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install Python and pip
   sudo apt-get install -y python3 python3-pip python3-venv
   
   # Install Git
   sudo apt-get install -y git
   
   # Install PostgreSQL (for local database)
   sudo apt-get install -y postgresql postgresql-contrib
   
   # Install serial communication tools
   sudo apt-get install -y minicom screen
   ```

### Phase 2: Project Setup

1. **Clone Your Project**
   ```bash
   cd /home/pi
   git clone https://github.com/yourusername/RoluATM.git
   cd RoluATM
   ```

2. **Environment Configuration**
   ```bash
   # Copy and configure environment
   cp env.template .env.local
   
   # Edit with your specific settings
   nano .env.local
   ```

   **Key settings for Raspberry Pi:**
   ```env
   # API Configuration for Pi
   VITE_API_URL=http://localhost:8000
   HOST=0.0.0.0
   PORT=8000
   
   # Hardware Configuration
   TFLEX_PORT=/dev/ttyUSB0  # or /dev/ttyACM0
   DEV_MODE=false           # Set to false for production
   KIOSK_MODE=true          # Enable kiosk mode
   
   # Your World ID credentials
   VITE_WORLD_APP_ID=your_actual_app_id
   WORLD_CLIENT_SECRET=your_actual_secret
   
   # Database (local PostgreSQL)
   DATABASE_URL=postgresql://rolu:password@localhost:5432/roluatm
   ```

3. **Database Setup**
   ```bash
   # Setup PostgreSQL
   sudo -u postgres psql
   ```
   
   ```sql
   CREATE USER rolu WITH PASSWORD 'password';
   CREATE DATABASE roluatm OWNER rolu;
   GRANT ALL PRIVILEGES ON DATABASE roluatm TO rolu;
   \q
   ```

4. **Install Dependencies**
   ```bash
   # Install Node.js dependencies
   npm install
   
   # Setup Python virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Phase 3: Hardware Configuration

1. **Configure Touch Screen**
   ```bash
   # Touch screen should work automatically
   # If issues, add to /boot/config.txt:
   sudo nano /boot/config.txt
   
   # Add if needed:
   # lcd_rotate=2  # If screen is upside down
   ```

2. **Set Up T-Flex Connection**
   ```bash
   # Find your serial device
   ls /dev/tty*
   
   # Test connection (when T-Flex is connected)
   sudo minicom -D /dev/ttyUSB0 -b 9600
   
   # Add user to dialout group for serial access
   sudo usermod -a -G dialout pi
   ```

3. **Configure Kiosk Mode**
   ```bash
   # Install Chromium for kiosk
   sudo apt-get install -y chromium-browser
   
   # Create autostart script
   mkdir -p ~/.config/autostart
   nano ~/.config/autostart/rolu-kiosk.desktop
   ```
   
   **Autostart content:**
   ```ini
   [Desktop Entry]
   Type=Application
   Name=RoluATM Kiosk
   Exec=/home/pi/RoluATM/start-kiosk.sh
   Hidden=false
   NoDisplay=false
   X-GNOME-Autostart-enabled=true
   ```

### Phase 4: Create Startup Scripts

1. **Frontend/Backend Startup Script**
   ```bash
   nano start-kiosk.sh
   chmod +x start-kiosk.sh
   ```
   
   **Script content:**
   ```bash
   #!/bin/bash
   cd /home/pi/RoluATM
   
   # Start backend in background
   source venv/bin/activate
   python server/app.py &
   BACKEND_PID=$!
   
   # Wait for backend to start
   sleep 10
   
   # Build and serve frontend
   npm run build
   npx serve -s dist -l 3000 &
   FRONTEND_PID=$!
   
   # Wait for frontend to start
   sleep 5
   
   # Start Chromium in kiosk mode
   chromium-browser \
     --kiosk \
     --disable-infobars \
     --disable-session-crashed-bubble \
     --disable-restore-session-state \
     --autoplay-policy=no-user-gesture-required \
     http://localhost:3000
   
   # Cleanup on exit
   kill $BACKEND_PID $FRONTEND_PID
   ```

### Phase 5: Testing

1. **Test Backend**
   ```bash
   source venv/bin/activate
   python server/app.py
   
   # Should see: "Backend running on port 8000"
   # Test with: curl http://localhost:8000/health
   ```

2. **Test Frontend**
   ```bash
   npm run build
   npx serve -s dist -l 3000
   
   # Visit: http://localhost:3000
   ```

3. **Test Hardware (with T-Flex connected)**
   ```bash
   python server/test_tflex.py
   ```

## 🌐 Alternative: Vercel + Pi Backend

If you prefer using Vercel for the frontend:

1. **Deploy Frontend to Vercel**
   ```bash
   # In your local development machine
   npm run build
   npx vercel --prod
   
   # Set environment variables in Vercel dashboard:
   # VITE_API_URL=http://your-pi-ip:8000
   ```

2. **Configure Pi for Backend Only**
   ```bash
   # Only run backend on Pi
   source venv/bin/activate
   python server/app.py
   
   # Make sure port 8000 is accessible
   sudo ufw allow 8000
   ```

3. **Point Chromium to Vercel**
   ```bash
   # In start-kiosk.sh, change the URL to:
   chromium-browser --kiosk https://your-vercel-app.vercel.app
   ```

## 🔧 Troubleshooting

### Common Issues

1. **Touch screen not working**
   ```bash
   # Check if detected
   xinput list
   
   # Calibrate if needed
   xinput-calibrator
   ```

2. **Serial port permission denied**
   ```bash
   # Add user to groups
   sudo usermod -a -G dialout,tty pi
   # Reboot required
   ```

3. **Network issues**
   ```bash
   # Check connection
   ping google.com
   
   # Check if ports are open
   netstat -tlnp | grep :8000
   ```

4. **Database connection issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test connection
   psql postgresql://rolu:password@localhost:5432/roluatm
   ```

## 🎯 Production Checklist

- [ ] World ID app configured and tested
- [ ] Database setup and migrations run
- [ ] T-Flex dispenser connected and tested
- [ ] Touch screen calibrated
- [ ] Autostart configured
- [ ] Network connectivity verified
- [ ] Backup strategy in place
- [ ] Monitoring/logging setup

## 📞 Next Steps

1. **Set up your World ID developer account**
2. **Connect and test T-Flex dispenser**
3. **Run through the complete user flow**
4. **Set up monitoring and logging**
5. **Create backup/recovery procedures**

## 🔐 Security Notes

- Change default passwords
- Enable firewall with only necessary ports
- Regular security updates
- Consider VPN for remote access
- Physical security for the kiosk

Ready to get started? Let me know if you need help with any specific step! 