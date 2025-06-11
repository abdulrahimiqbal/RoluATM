# 🎯 RoluATM - New Simplified Architecture

## 📋 **Overview**

RoluATM now uses a **simplified two-app architecture** that follows World ID Mini App best practices:

1. **Kiosk App** - Runs on Raspberry Pi touchscreen (amount selection + QR code generation)
2. **Mini App** - Runs in World App on customer's phone (payment + World ID verification)

## 🔄 **New Customer Journey**

### **Step 1: Amount Selection (Kiosk)**
- Customer approaches Pi kiosk
- Selects cash amount ($5, $10, $20, $50, or custom)
- Reviews transaction summary (amount + fee + quarters)
- Clicks "Generate QR Code"

### **Step 2: QR Code Display (Kiosk)**
- Kiosk generates transaction ID and QR code
- QR code links to: `mini-app.roluatm.com?transaction_id=xyz`
- Shows transaction details and countdown timer

### **Step 3: Payment (Customer's Phone)**
- Customer scans QR code with World App
- Opens RoluATM Mini App within World App
- Reviews transaction details
- Completes World ID verification + payment

### **Step 4: Dispensing (Kiosk)**
- Payment confirmed → status updates to "dispensing"
- T-Flex dispenser releases quarters
- Shows completion message
- Ready for next customer

---

## 🏗️ **Technical Architecture**

### **Components:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kiosk App     │    │   Backend API   │    │   Mini App      │
│   (React)       │    │   (Python)      │    │   (React +      │
│   Port: 3000    │◄──►│   Port: 8000    │◄──►│   MiniKit)      │
│                 │    │                 │    │   Port: 3001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  7" Touchscreen │    │   PostgreSQL    │    │   World App     │
│   (Pi Display)  │    │   + T-Flex      │    │   (Customer)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Data Flow:**

1. **Transaction Creation**: `Kiosk → Backend → Database → QR Code`
2. **Payment Processing**: `Mini App → World ID → Backend → T-Flex`
3. **Status Updates**: `Backend → Database → Kiosk Polling`

---

## 🛠️ **Development Setup**

### **Prerequisites:**
- Node.js 18+
- Python 3.8+
- PostgreSQL
- Raspberry Pi 4B + 7" display (for production)

### **Installation:**

```bash
# Clone repository
git clone https://github.com/your-org/rolu-atm.git
cd rolu-atm

# Install kiosk app dependencies
cd kiosk-app
npm install

# Install mini app dependencies  
cd ../mini-app
npm install

# Install backend dependencies
cd ../server
pip install -r requirements.txt

# Set up database
createdb roluatm
psql roluatm < ../schema.sql

# Configure environment
cp env.example .env.local
# Edit .env.local with your settings
```

### **Development Commands:**

```bash
# Terminal 1: Backend
cd server
python app.py

# Terminal 2: Kiosk App
cd kiosk-app  
npm run dev

# Terminal 3: Mini App
cd mini-app
npm run dev
```

**URLs:**
- Kiosk: http://localhost:3000
- Mini App: http://localhost:3001  
- Backend: http://localhost:8000

---

## 🔧 **API Endpoints**

### **Kiosk Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Hardware status for kiosk UI |
| `POST` | `/api/transaction/create` | Create new transaction + QR |
| `GET` | `/api/transaction/{id}/status` | Poll transaction status |

### **Mini App Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/transaction/{id}` | Get transaction details |
| `POST` | `/api/transaction/pay` | Process World ID payment |

### **Example Transaction Flow:**

```bash
# 1. Create transaction
curl -X POST http://localhost:8000/api/transaction/create \
  -H "Content-Type: application/json" \
  -d '{"amount": 10.00, "quarters": 40, "total": 10.50}'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 10.00,
  "quarters": 40, 
  "total": 10.50,
  "status": "pending",
  "mini_app_url": "http://localhost:3001?transaction_id=550e8400...",
  "expires_at": "2024-01-15T10:15:00Z"
}

# 2. Customer pays via mini app (World ID verification)
curl -X POST http://localhost:8000/api/transaction/pay \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "proof": "0x...",
    "nullifier_hash": "0x...", 
    "merkle_root": "0x..."
  }'

# 3. Kiosk polls for status updates
curl http://localhost:8000/api/transaction/550e8400-e29b-41d4-a716-446655440000/status

# Response: {"status": "complete", "progress": 100}
```

---

## 🔐 **Security Features**

- **World ID Verification**: Prevents Sybil attacks and ensures human users
- **Transaction Expiration**: 10-minute timeout prevents stale transactions  
- **Nullifier Hash Tracking**: Prevents double-spending attempts
- **Input Validation**: All amounts and calculations verified server-side
- **HTTPS Required**: All production traffic encrypted

---

## 🚀 **Deployment**

### **Raspberry Pi Setup:**

```bash
# Enable display and touch
sudo raspi-config
# Advanced Options → GL Driver → GL (Fake KMS)

# Install dependencies
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip postgresql chromium-browser

# Clone and setup project
git clone <your-repo>
cd rolu-atm

# Install Node.js apps
cd kiosk-app && npm install && npm run build
cd ../mini-app && npm install && npm run build

# Install Python backend
cd ../server && pip install -r requirements.txt

# Setup database
sudo -u postgres createdb roluatm
sudo -u postgres psql roluatm < schema.sql

# Configure autostart
sudo cp kiosk-startup.service /etc/systemd/system/
sudo systemctl enable kiosk-startup
```

### **Production Environment:**

- **Kiosk**: Runs fullscreen on Pi display
- **Mini App**: Deployed to CDN/hosting service  
- **Backend**: Runs as systemd service
- **Database**: PostgreSQL with automated backups

---

## 🧪 **Testing**

### **Mock Mode:**
Set `DEV_MODE=true` to simulate hardware:
- T-Flex dispenser responses
- World ID verification 
- Payment processing

### **Integration Tests:**
```bash
# Test complete flow
cd tests
python test_integration.py
```

---

## 📈 **Monitoring**

- **Transaction Logs**: All transactions logged to database
- **Hardware Status**: Regular health checks on T-Flex dispenser
- **Error Tracking**: Failed transactions and dispenser errors logged
- **Analytics**: Transaction volume, amounts, success rates

---

## 🔧 **Troubleshooting**

### **Common Issues:**

| Issue | Solution |
|-------|----------|
| QR code not generating | Check backend connection and database |
| Mini app not loading | Verify MINI_APP_URL and World App setup |
| Coins not dispensing | Check T-Flex connection and power |
| World ID verification fails | Verify WORLD_APP_ID and client secret |

### **Logs:**
```bash
# Backend logs
tail -f server/app.log

# Kiosk app logs  
cd kiosk-app && npm run dev

# System logs
journalctl -u kiosk-startup -f
```

---

## 📚 **Documentation Links**

- [World ID Documentation](https://docs.worldcoin.org)
- [MiniKit SDK Guide](https://docs.worldcoin.org/minikit)
- [T-Flex Dispenser Manual](./docs/tflex-manual.pdf)
- [Raspberry Pi Setup Guide](./RASPBERRY_PI_SETUP.md)

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 