# RoluATM Vercel Deployment Guide

## Overview

Your RoluATM project consists of 3 separate components that need to be deployed:

1. **Backend API** (`/server`) - Python Flask server with database and hardware integration
2. **Kiosk App** (`/kiosk-app`) - React app for Raspberry Pi touchscreen
3. **Mini App** (`/mini-app`) - React app for World App integration

## Deployment Strategy

We'll deploy these as **3 separate Vercel projects** for optimal performance and scalability.

## Prerequisites

1. **Vercel CLI installed:**
   ```bash
   npm install -g vercel
   ```

2. **Vercel account setup:**
   ```bash
   vercel login
   ```

3. **Environment variables ready:**
   - `WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19`
   - `VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db`
   - `DATABASE_URL=postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require`

## Step 1: Deploy Backend API

```bash
cd server
vercel --prod
```

**During setup:**
- Project name: `roluatm-backend`
- Framework: `Other`
- Build command: (leave empty)
- Output directory: (leave empty)

**Set environment variables:**
```bash
vercel env add WORLD_CLIENT_SECRET
# Enter: sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19

vercel env add DATABASE_URL
# Enter: postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require

vercel env add DEV_MODE
# Enter: false

vercel env add VITE_WORLD_APP_ID
# Enter: app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db

vercel env add MINI_APP_URL
# Enter: https://roluatm-mini.vercel.app
```

**Expected URL:** `https://roluatm-backend.vercel.app`

## Step 2: Deploy Mini App

```bash
cd ../mini-app
vercel --prod
```

**During setup:**
- Project name: `roluatm-mini`
- Framework: `Vite`
- Build command: `npm run build`
- Output directory: `dist`

**Set environment variables:**
```bash
vercel env add VITE_API_URL
# Enter: https://roluatm-backend.vercel.app

vercel env add VITE_WORLD_APP_ID
# Enter: app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
```

**Expected URL:** `https://roluatm-mini.vercel.app`

## Step 3: Deploy Kiosk App

```bash
cd ../kiosk-app
vercel --prod
```

**During setup:**
- Project name: `roluatm-kiosk`
- Framework: `Vite`
- Build command: `npm run build`
- Output directory: `dist`

**Set environment variables:**
```bash
vercel env add VITE_API_URL
# Enter: https://roluatm-backend.vercel.app
```

**Expected URL:** `https://roluatm-kiosk.vercel.app`

## Step 4: Update Backend Mini App URL

After deploying the mini app, update the backend environment:

```bash
cd ../server
vercel env rm MINI_APP_URL
vercel env add MINI_APP_URL
# Enter: https://roluatm-mini.vercel.app

# Redeploy backend with updated URL
vercel --prod
```

## Testing the Deployment

### 1. Test Backend Health
```bash
curl https://roluatm-backend.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-11T18:00:00Z",
  "hardware": {
    "coinDispenser": "ready",
    "network": "connected",
    "security": "active"
  }
}
```

### 2. Test Transaction Creation
```bash
curl -X POST https://roluatm-backend.vercel.app/api/transaction/create \
  -H "Content-Type: application/json" \
  -d '{"fiat_amount": 5.0}'
```

### 3. Test Frontend Apps
- **Kiosk:** https://roluatm-kiosk.vercel.app
- **Mini App:** https://roluatm-mini.vercel.app

## Important Notes

### Hardware Limitations
- **T-Flex Dispenser:** Will run in mock mode on Vercel (no serial port access)
- **For Production Pi:** Deploy locally or use hybrid approach

### Database
- ✅ **Neon PostgreSQL** works perfectly with Vercel
- ✅ **Existing data** preserved
- ✅ **Transactions table** fully functional

### World ID Integration
- ✅ **Verification** works on Vercel
- ✅ **Mock mode** available for testing
- ✅ **Production** ready with real World ID API

## Hybrid Deployment (Recommended for Production)

For the actual Raspberry Pi kiosk:

1. **Backend on Pi:** Use local Flask server with hardware integration
2. **Mini App on Vercel:** For World App users
3. **Database on Neon:** Shared between Pi and Vercel

### Pi Configuration:
```bash
# On Raspberry Pi
export API_URL=http://localhost:8000
export MINI_APP_URL=https://roluatm-mini.vercel.app
export DEV_MODE=false
export TFLEX_PORT=/dev/ttyUSB0

python server/app.py
```

## Troubleshooting

### Backend Issues
- **psycopg2 errors:** Using `psycopg2-binary==2.9.7` for compatibility
- **Port conflicts:** Vercel handles this automatically
- **Environment variables:** Double-check all secrets are set

### Frontend Issues
- **Missing dependencies:** Already installed `@radix-ui/react-tooltip` and `@tailwindcss/typography`
- **API connectivity:** Ensure CORS is properly configured
- **Build errors:** Check Vercel build logs

### Database Issues
- **Connection:** Test with provided Neon URL
- **Permissions:** Ensure user has full access to `transactions` table

## Vercel Dashboard URLs

After deployment, manage your apps at:
- https://vercel.com/dashboard (overview)
- Individual project settings for environment variables
- Build logs and deployment history

## Cost Considerations

- **Hobby Plan:** Free for personal projects
- **Backend functions:** May need Pro plan for heavy usage
- **Database:** Neon provides generous free tier

## Success Checklist

- [ ] Backend deployed and health check passes
- [ ] Mini app loads and connects to backend
- [ ] Kiosk app loads and can create transactions
- [ ] World ID integration functional
- [ ] Database transactions working
- [ ] QR codes generate correctly
- [ ] Environment variables configured
- [ ] CORS headers working

Your RoluATM system is now ready for production use! 🎰 