# 🥧 RoluATM Raspberry Pi Deployment Plan

## 📋 **Overview**

This plan outlines the complete process for moving your working RoluATM system from your Mac to the Raspberry Pi for the final kiosk setup.

## 🎯 **Current Status**
- ✅ **Mac Development**: Fully functional system
- ✅ **Transaction Flow**: Working end-to-end
- ✅ **Phone Integration**: Mini app connects successfully
- ✅ **Database**: Neon PostgreSQL operational
- 🎯 **Target**: Production deployment on Raspberry Pi

## 📦 **Phase 1: Pre-Deployment Preparation**

### **1.1 Verify Current System**
```bash
# On your Mac - ensure everything is working
./start-system.sh
./check-status.sh

# Test complete flow:
# 1. Open http://localhost:3000
# 2. Create transaction
# 3. Scan QR with phone
# 4. Verify mini app loads
```

### **1.2 Prepare Pi Connection**
```bash
# Test Pi connectivity
ssh rahiim@192.168.1.250

# Check Pi system info
uname -a
df -h
free -h
```

## 🚀 **Phase 2: Deployment Execution**

### **2.1 Full Deployment to Pi**
```bash
# Run the deployment script
./deploy-to-pi.sh

# Choose option 1: Full deployment
# This will:
# - Sync all code to Pi
# - Set up Python environment
# - Install dependencies
# - Build kiosk app
# - Configure environment variables
```

### **2.2 Pi Environment Setup**
```bash
# SSH to Pi and run setup
ssh rahiim@192.168.1.250
cd ~/RoluATM
./pi-setup.sh

# This will:
# - Install system packages
# - Create systemd services
# - Set up autostart
# - Create management scripts
```

## 🔧 **Phase 3: Service Configuration**

### **3.1 Start Services**
```bash
# On Pi
./start-pi-services.sh

# Or manually:
sudo systemctl start rolu-backend.service
sudo systemctl start rolu-kiosk.service
```

### **3.2 Verify Services**
```bash
# Check service status
./check-pi-status.sh

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000

# Check from your Mac
curl http://192.168.1.250:8000/health
curl http://192.168.1.250:3000
```

## 🧪 **Phase 4: Testing & Validation**

### **4.1 Backend API Testing**
```bash
# Test transaction creation
curl -X POST http://192.168.1.250:8000/api/transaction/create \
     -H "Content-Type: application/json" \
     -d '{"amount": 5}'

# Test transaction retrieval
curl http://192.168.1.250:8000/api/transaction/{transaction_id}
```

### **4.2 Complete Flow Testing**
1. **Kiosk Access**: Open `http://192.168.1.250:3000` on Pi or external device
2. **Transaction Creation**: Select amount and generate QR
3. **Mobile Testing**: Scan QR with phone
4. **Mini App Loading**: Verify mini app loads with transaction
5. **Payment Flow**: Test World ID verification (mock mode)
6. **Coin Dispensing**: Verify T-Flex simulation

### **4.3 Network Testing**
```bash
# Test from different devices on network
# Phone browser: http://192.168.1.250:3000
# Laptop browser: http://192.168.1.250:3000
# API calls from external: http://192.168.1.250:8000/health
```

## 🖥️ **Phase 5: Kiosk Mode Setup**

### **5.1 Display Configuration**
```bash
# On Pi - configure display for kiosk
sudo raspi-config
# Advanced Options > Resolution > Choose appropriate resolution

# Install chromium if not present
sudo apt install chromium-browser

# Test kiosk mode manually
chromium-browser --kiosk --no-sandbox http://localhost:3000
```

### **5.2 Autostart Configuration**
The `pi-setup.sh` script creates autostart configuration:
- Kiosk app launches automatically on boot
- Services start automatically
- Full-screen browser mode

### **5.3 Hardware Integration**
```bash
# Test T-Flex connection (if hardware available)
ls -la /dev/ttyUSB*

# Check USB permissions
sudo usermod -a -G dialout rahiim
```

## 🔄 **Phase 6: Production Operations**

### **6.1 Service Management**
```bash
# Start services
./start-pi-services.sh

# Stop services  
./stop-pi-services.sh

# Check status
./check-pi-status.sh

# View logs
sudo journalctl -u rolu-backend.service -f
sudo journalctl -u rolu-kiosk.service -f
```

### **6.2 Updates & Maintenance**
```bash
# From your Mac - deploy updates
./deploy-to-pi.sh
# Choose option 2: Code sync only

# On Pi - restart services after updates
sudo systemctl restart rolu-backend.service
sudo systemctl restart rolu-kiosk.service
```

### **6.3 Monitoring**
```bash
# System health
htop
df -h
free -h

# Service status
systemctl status rolu-backend.service
systemctl status rolu-kiosk.service

# Network connectivity
ping google.com
curl http://localhost:8000/health
```

## 🚨 **Phase 7: Troubleshooting**

### **7.1 Common Issues**

**Backend Not Starting:**
```bash
# Check logs
sudo journalctl -u rolu-backend.service -n 50

# Common fixes
sudo systemctl restart rolu-backend.service
source venv/bin/activate && python3 pi_backend.py  # Manual test
```

**Kiosk Not Loading:**
```bash
# Check kiosk service
sudo systemctl status rolu-kiosk.service

# Test manually
cd ~/RoluATM/kiosk-app/dist
python3 -m http.server 3000
```

**Database Connection Issues:**
```bash
# Test database connectivity
python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require'); print('Connected!')"
```

**Network Issues:**
```bash
# Check IP address
hostname -I

# Test connectivity
ping 8.8.8.8
curl http://google.com
```

### **7.2 Recovery Procedures**
```bash
# Full service restart
sudo systemctl restart rolu-backend.service rolu-kiosk.service

# Reboot Pi
sudo reboot

# Re-deploy from Mac
./deploy-to-pi.sh  # Option 1: Full deployment
```

## 📊 **Phase 8: Performance Optimization**

### **8.1 System Optimization**
```bash
# Increase GPU memory for better browser performance
sudo raspi-config
# Advanced Options > Memory Split > 128

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave
```

### **8.2 Application Optimization**
- Kiosk app is pre-built for optimal performance
- Backend uses efficient database connections
- Static file serving for fast load times

## 🎯 **Success Criteria**

✅ **Backend Service**: Running on http://192.168.1.250:8000  
✅ **Kiosk App**: Accessible on http://192.168.1.250:3000  
✅ **Transaction Flow**: Complete end-to-end functionality  
✅ **Mobile Integration**: QR codes work from any device  
✅ **Auto-start**: Services start automatically on boot  
✅ **Stability**: Services restart automatically on failure  
✅ **Monitoring**: Easy status checking and log access  

## 📞 **Support Commands**

```bash
# Quick deployment
./deploy-to-pi.sh

# Service management on Pi
./start-pi-services.sh
./stop-pi-services.sh  
./check-pi-status.sh

# Manual service control
sudo systemctl start/stop/restart rolu-backend.service
sudo systemctl start/stop/restart rolu-kiosk.service

# Logs
sudo journalctl -u rolu-backend.service -f
sudo journalctl -u rolu-kiosk.service -f

# System status
htop
df -h
free -h
```

---

**🎉 Ready to deploy? Start with: `./deploy-to-pi.sh`** 