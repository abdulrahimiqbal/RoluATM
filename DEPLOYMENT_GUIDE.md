# RoluATM Deployment Guide

This guide covers deploying the RoluATM system to production environments.

## Overview

The RoluATM system consists of three main components:

1. **Kiosk App** - React frontend for the Raspberry Pi touchscreen (Port 3000)
2. **Mini App** - React app with MiniKit for World App integration (Port 3001)  
3. **Backend API** - Python Flask server for transaction processing (Port 8000)

## Prerequisites

- Raspberry Pi 4 with touchscreen display
- T-Flex coin dispenser connected via USB/Serial
- PostgreSQL database (Neon.tech recommended)
- World ID app credentials
- Node.js 18+ and Python 3.8+

## 1. Raspberry Pi Setup

### Hardware Setup

1. **Install Raspberry Pi OS**
   ```bash
   # Use Raspberry Pi Imager to flash latest Pi OS Lite
   # Enable SSH, set user credentials
   ```

2. **Connect Hardware**
   - Connect 7" touchscreen display
   - Connect T-Flex coin dispenser via USB
   - Ensure power supply can handle both Pi and dispenser

3. **Install Dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install Python dependencies
   sudo apt install -y python3-pip python3-venv
   
   # Install system dependencies
   sudo apt install -y git nginx
   ```

### Application Deployment

1. **Clone Repository**
   ```bash
   cd /home/pi
   git clone https://github.com/your-username/RoluATM.git
   cd RoluATM
   ```

2. **Configure Environment**
   ```bash
   # Copy environment template
   cp env.example .env.local
   
   # Edit with your credentials
   nano .env.local
   ```

   Required environment variables:
   ```env
   VITE_WORLD_APP_ID=your_world_app_id
   WORLD_CLIENT_SECRET=your_world_client_secret
   DATABASE_URL=your_neon_database_url
   TFLEX_PORT=/dev/ttyUSB0
   DEV_MODE=false
   MINI_APP_URL=https://your-mini-app-domain.com
   ```

3. **Install Dependencies**
   ```bash
   # Install root dependencies
   npm install
   
   # Install kiosk app dependencies
   cd kiosk-app && npm install && cd ..
   
   # Install backend dependencies
   cd server
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   ```

4. **Build Kiosk App**
   ```bash
   cd kiosk-app
   npm run build
   cd ..
   ```

5. **Configure Nginx**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/roluatm
   sudo ln -s /etc/nginx/sites-available/roluatm /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl reload nginx
   ```

6. **Create System Services**
   ```bash
   # Backend service
   sudo tee /etc/systemd/system/roluatm-backend.service << EOF
   [Unit]
   Description=RoluATM Backend Service
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/RoluATM/server
   Environment=PATH=/home/pi/RoluATM/server/venv/bin
   ExecStart=/home/pi/RoluATM/server/venv/bin/python app.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start services
   sudo systemctl daemon-reload
   sudo systemctl enable roluatm-backend
   sudo systemctl start roluatm-backend
   ```

7. **Configure Display and Touch**
   ```bash
   # Add to /boot/config.txt
   sudo tee -a /boot/config.txt << EOF
   
   # 7" Touchscreen
   lcd_rotate=2
   display_rotate=2
   
   # Disable sleep/screensaver
   hdmi_blanking=1
   EOF
   ```

8. **Setup Kiosk Mode**
   ```bash
   # Install minimal window manager
   sudo apt install -y openbox chromium-browser unclutter
   
   # Create autostart script
   mkdir -p /home/pi/.config/openbox
   tee /home/pi/.config/openbox/autostart << EOF
   # Disable screen blanking
   xset s off
   xset -dpms
   xset s noblank
   
   # Hide cursor
   unclutter -idle 0.5 -root &
   
   # Start Chromium in kiosk mode
   chromium-browser --noerrdialogs --disable-infobars --kiosk http://localhost --check-for-update-interval=1 --simulate-critical-update &
   EOF
   
   # Set up autologin to GUI
   sudo raspi-config
   # Choose: System Options > Boot / Auto Login > Desktop Autologin
   ```

## 2. Mini App Deployment (Vercel)

### Setup Vercel Project

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Configure Mini App**
   ```bash
   cd mini-app
   
   # Create vercel.json configuration
   cat > vercel.json << EOF
   {
     "version": 2,
     "builds": [
       {
         "src": "package.json",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "dist"
         }
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/index.html"
       }
     ],
     "env": {
       "VITE_WORLD_APP_ID": "@world_app_id",
       "VITE_BACKEND_URL": "@backend_url"
     }
   }
   EOF
   ```

3. **Set Environment Variables**
   ```bash
   # Add secrets to Vercel
   vercel env add WORLD_APP_ID
   vercel env add BACKEND_URL
   ```

4. **Deploy**
   ```bash
   vercel --prod
   ```

### Alternative: Manual Deployment

1. **Build Mini App**
   ```bash
   cd mini-app
   npm run build
   ```

2. **Deploy to Static Host**
   - Upload `dist/` folder to any static hosting service
   - Configure environment variables in hosting platform
   - Set up custom domain and SSL certificate

## 3. Backend API Deployment (Optional Cloud)

For production scale, you may want to deploy the backend separately:

### Railway Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY server/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY server/ .
   
   EXPOSE 8000
   
   CMD ["python", "app.py"]
   ```

2. **Deploy to Railway**
   - Connect GitHub repository
   - Set environment variables
   - Deploy automatically

## 4. Database Setup (Neon.tech)

1. **Create Neon Project**
   - Sign up at neon.tech
   - Create new project
   - Copy connection string

2. **Initialize Database**
   ```bash
   # Run schema migration
   psql "your_neon_connection_string" -f schema.sql
   ```

## 5. World ID Configuration

1. **Create World App**
   - Go to developer.worldcoin.org
   - Create new app
   - Configure verification levels
   - Copy App ID and Client Secret

2. **Test Integration**
   ```bash
   # Test World ID verification
   python test_complete_flow.py
   ```

## 6. Monitoring and Maintenance

### System Monitoring

1. **Service Status**
   ```bash
   # Check service status
   sudo systemctl status roluatm-backend
   
   # View logs
   sudo journalctl -u roluatm-backend -f
   ```

2. **Hardware Monitoring**
   ```bash
   # Check T-Flex dispenser
   ls -la /dev/ttyUSB*
   
   # Test serial connection
   python -c "import serial; print(serial.Serial('/dev/ttyUSB0', 9600).readline())"
   ```

### Updates and Backup

1. **Application Updates**
   ```bash
   cd /home/pi/RoluATM
   git pull origin main
   
   # Rebuild kiosk app
   cd kiosk-app && npm run build && cd ..
   
   # Restart services
   sudo systemctl restart roluatm-backend
   ```

2. **Database Backup**
   ```bash
   # Backup transactions table
   pg_dump "your_neon_connection_string" -t transactions > backup.sql
   ```

## 7. Security Considerations

1. **Network Security**
   - Use HTTPS for all external communications
   - Configure firewall to only allow necessary ports
   - Use VPN for remote access

2. **Hardware Security**
   - Secure physical access to Raspberry Pi
   - Use hardware cases with locks
   - Monitor for tampering

3. **Application Security**
   - Regularly update dependencies
   - Monitor for security vulnerabilities
   - Use environment variables for secrets

## 8. Troubleshooting

### Common Issues

1. **T-Flex Dispenser Not Working**
   ```bash
   # Check USB connection
   lsusb
   ls -la /dev/ttyUSB*
   
   # Check permissions
   sudo usermod -a -G dialout pi
   ```

2. **Frontend Not Loading**
   ```bash
   # Check Nginx status
   sudo systemctl status nginx
   
   # Check Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Backend API Errors**
   ```bash
   # Check service logs
   sudo journalctl -u roluatm-backend -n 50
   
   # Test database connection
   python -c "import psycopg2; psycopg2.connect('your_db_url')"
   ```

### Performance Optimization

1. **Raspberry Pi Performance**
   - Use SSD instead of SD card for better I/O
   - Increase GPU memory split if using graphics
   - Monitor CPU temperature and add cooling

2. **Database Optimization**
   - Add indexes for frequently queried fields
   - Set up connection pooling
   - Monitor query performance

## Contact and Support

- **Documentation**: [README.md](./README.md)
- **Issues**: GitHub Issues
- **Testing**: Run `python test_complete_flow.py` to verify deployment 