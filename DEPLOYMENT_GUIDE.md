# RoluATM Deployment Guide

## Quick Start

### 1. Start the System
```bash
./start-system.sh
```

### 2. Check Status
```bash
./check-status.sh
```

### 3. Stop the System
```bash
./stop-system.sh
```

## System Architecture

### Local Development (Current Setup)
- **Backend**: `pi_backend.py` on http://localhost:8000
- **Kiosk App**: React app on http://localhost:3000
- **Mini App**: React app on http://localhost:3001
- **Database**: Neon PostgreSQL (cloud)

### Production Deployments
- **Kiosk App**: https://kiosk-app-xi.vercel.app
- **Mini App**: https://mini-app-azure.vercel.app
- **Backend**: Can be deployed to Vercel or run on Raspberry Pi

## Testing the Flow

1. **Open Kiosk**: http://localhost:3000
2. **Select Amount**: Choose $5, $10, or $20
3. **Get QR Code**: System generates QR with transaction ID
4. **Scan QR**: Opens mini app with `?backend=local&transaction_id=...`
5. **Mini App**: Connects to local backend, shows transaction details
6. **World ID**: Verify identity (mock mode enabled)
7. **Payment**: Complete transaction and dispense coins

## Environment Variables

```bash
WORLD_CLIENT_SECRET="sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19"
DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
DEV_MODE="true"
MINI_APP_URL="https://mini-app-azure.vercel.app"
```

## Troubleshooting

### Port Conflicts
```bash
./stop-system.sh
./start-system.sh
```

### Check Logs
- Backend logs appear in terminal when running `start-system.sh`
- Frontend logs appear in browser console

### Manual Testing
```bash
# Test backend health
curl http://localhost:8000/health

# Create test transaction
curl -X POST http://localhost:8000/api/transaction/create \
  -H "Content-Type: application/json" \
  -d '{"amount": 5}'
```

## Deployment Options

### Option 1: Hybrid (Current)
- Local backend for development
- Deployed frontends on Vercel
- Best for testing and development

### Option 2: Full Cloud
- Deploy backend to Vercel
- Use deployed frontends
- Best for production without Pi

### Option 3: Full Local
- Run everything locally
- Best for Pi deployment

### Option 4: Pi Production
- Backend on Raspberry Pi
- Frontends on Vercel
- Best for actual kiosk deployment 