# 🎰 RoluATM - Crypto-to-Cash Kiosk

A complete solution for converting cryptocurrency to physical quarters using World ID verification and T-Flex hardware dispensers.

## 🏗️ Architecture

### Frontend Apps
- **Kiosk App** (`/kiosk-app`) - React touchscreen interface for Raspberry Pi
- **Mini App** (`/mini-app`) - React Web App for World ID verification

### Backend
- **Pi Backend** (`/pi_backend.py`) - Python server with T-Flex hardware integration

### Deployment
- **Frontend Apps**: Auto-deployed to Vercel on every commit
- **Backend**: Runs locally on Raspberry Pi for hardware control

## 🚀 Quick Start

### Development Setup

1. **Install Dependencies**
   ```bash
   npm install
   cd kiosk-app && npm install
   cd ../mini-app && npm install
   ```

2. **Install Python Dependencies** (for Pi backend)
   ```bash
   pip install pyserial
   ```

3. **Environment Variables**
   Create `.env.local` files in each app:
   
   **kiosk-app/.env.local:**
   ```
   VITE_API_URL=http://localhost:8000
   ```
   
   **mini-app/.env.local:**
   ```
   VITE_API_URL=http://localhost:8000
   VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
   ```

4. **Run Development Servers**
   ```bash
   # Backend (T-Flex controller)
   python3 pi_backend.py
   
   # Frontend apps
   npm run dev
   ```

### Production Deployment

1. **Frontend**: Push to GitHub → Auto-deploys to Vercel
2. **Backend**: Copy `pi_backend.py` to Raspberry Pi and run

## 🔧 Hardware Integration

### T-Flex Coin Dispenser
- **Port**: `/dev/ttyUSB0` (configurable)
- **Baudrate**: 9600
- **Auto-fallback**: Mock mode if hardware not detected

### Raspberry Pi Setup
```bash
# On your Pi
git clone https://github.com/yourusername/RoluATM
cd RoluATM
pip install pyserial
python3 pi_backend.py
```

## 🌍 World ID Integration

- **App ID**: `app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db`
- **Verification**: Handled in mini app
- **Security**: Nullifier hash prevents replay attacks

## 📱 User Flow

1. **Customer selects amount** on Pi touchscreen (kiosk app)
2. **QR code generated** pointing to mini app
3. **Customer scans** with World App
4. **World ID verification** in mini app
5. **Quarters dispensed** automatically via T-Flex

## 🛠️ Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **UI Components**: shadcn/ui + Radix UI
- **Backend**: Python + HTTP Server
- **Hardware**: T-Flex Serial Communication
- **Authentication**: World ID + MiniKit
- **Database**: Neon PostgreSQL (optional)
- **Deployment**: Vercel + GitHub Actions

## 📊 Project Structure

```
RoluATM/
├── kiosk-app/           # Pi touchscreen interface
├── mini-app/            # World App integration
├── pi_backend.py        # Hardware controller
├── server/              # Legacy Flask backend
└── docs/                # Documentation
```

## 🔐 Security Features

- **World ID Verification**: Prevents fraud
- **Transaction Expiry**: 10-minute timeout
- **Replay Protection**: Nullifier hash storage
- **Hardware Control**: Local Pi execution only

## 🚧 Development Notes

- **Mock Mode**: Automatic fallback when T-Flex not connected
- **Local Testing**: All apps run locally for development
- **Hot Reload**: Frontend apps support live development
- **Error Handling**: Comprehensive transaction state management

## 📞 Support

For hardware setup, deployment issues, or integration questions, refer to the documentation or create an issue.

---

**Built for real-world crypto-to-cash conversion with enterprise-grade security and hardware integration.**
# Auto-deployment test - Wed Jun 11 10:52:26 PDT 2025
