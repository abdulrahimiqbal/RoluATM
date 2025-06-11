# 🚀 RoluATM Deployment Setup Guide

## Overview
This guide sets up automatic deployment from GitHub to Vercel for both the kiosk and mini apps.

## Prerequisites
- ✅ GitHub CLI installed and authenticated
- ✅ Vercel account 
- ✅ Local repository with all changes committed

## 🔧 GitHub Repository Setup

### 1. Repository Created
```bash
✅ Repository: https://github.com/abdulrahimiqbal/RoluATM
✅ Code pushed to main branch
✅ All files committed
```

## 🌐 Vercel Deployment Setup

### Step 1: Deploy Kiosk App
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import `abdulrahimiqbal/RoluATM` 
4. **Select root directory: `kiosk-app`**
5. **Project name: `rolu-atm-kiosk`**
6. **Framework: Vite**
7. **Build command: `npm run build`**
8. **Output directory: `dist`**
9. **Install command: `npm install`**

**Environment Variables for Kiosk:**
```
VITE_API_URL=http://localhost:8000
```

### Step 2: Deploy Mini App  
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import `abdulrahimiqbal/RoluATM` again
4. **Select root directory: `mini-app`**
5. **Project name: `rolu-atm-mini`**
6. **Framework: Vite**
7. **Build command: `npm run build`**
8. **Output directory: `dist`**
9. **Install command: `npm install`**

**Environment Variables for Mini App:**
```
VITE_API_URL=http://localhost:8000
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
```

## 📱 Production URLs

After deployment, you'll get URLs like:
- **Kiosk App**: `https://rolu-atm-kiosk.vercel.app`
- **Mini App**: `https://rolu-atm-mini.vercel.app`

## 🔄 Automatic Deployments

Every commit to the `main` branch will automatically:
1. Trigger Vercel builds for both apps
2. Deploy updated versions
3. Update production URLs

## 🏗️ Local Development vs Production

### Local Development (Current Setup)
- **Backend**: `http://localhost:8000` (pi_backend.py)
- **Kiosk**: `http://localhost:3000`
- **Mini**: `http://localhost:3001`

### Production Setup
- **Backend**: Raspberry Pi running `pi_backend.py`
- **Kiosk**: Vercel CDN (global distribution)
- **Mini**: Vercel CDN (global distribution)

## 🔧 Updating Environment Variables

### For Production Deployment:
You'll need to update the `VITE_API_URL` in both Vercel projects to point to your Pi's public IP or domain:

**Kiosk App Environment:**
```
VITE_API_URL=https://your-pi-domain.com:8000
```

**Mini App Environment:**
```
VITE_API_URL=https://your-pi-domain.com:8000
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
```

## 🎯 QR Code Configuration

Once deployed, update the Pi backend to generate QR codes pointing to your production mini app:

```python
# In pi_backend.py, update MINI_APP_URL
MINI_APP_URL = "https://rolu-atm-mini.vercel.app"
```

## 🚦 Testing Deployment

### Test Kiosk App:
1. Visit `https://rolu-atm-kiosk.vercel.app`
2. Should load the amount selection interface
3. QR codes should point to production mini app

### Test Mini App:
1. Visit `https://rolu-atm-mini.vercel.app?transaction_id=test`
2. Should load World ID verification interface
3. Should attempt to connect to backend API

## 🔄 Development Workflow

1. **Make changes locally**
2. **Test with `npm run dev`**
3. **Commit changes: `git add . && git commit -m "Update"`**
4. **Push to GitHub: `git push`**
5. **Vercel automatically deploys both apps**
6. **Check deployment status in Vercel dashboard**

## 🎰 Complete Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Raspberry Pi  │    │     Vercel      │
│                 │    │                 │
│  ┌───────────┐  │    │ ┌─────────────┐ │
│  │pi_backend │  │    │ │ Kiosk App   │ │
│  │   :8000   │  │◄───┤ │(Global CDN) │ │
│  └───────────┘  │    │ └─────────────┘ │
│                 │    │                 │
│  ┌───────────┐  │    │ ┌─────────────┐ │
│  │  T-Flex   │  │    │ │  Mini App   │ │
│  │ Dispenser │  │    │ │(Global CDN) │ │
│  └───────────┘  │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘
        │                       │
        └── Hardware Control ───┘
            (Serial/USB)
```

## 🎉 Benefits

- **Global CDN**: Fast loading worldwide
- **Auto-deployment**: Push code → Instant updates
- **Scalability**: Handle millions of requests
- **Security**: Frontend isolated from hardware
- **Reliability**: 99.9% uptime
- **Version Control**: Easy rollbacks

---

**Next Steps**: Deploy to Vercel following the steps above, then test the complete flow from QR generation to payment processing! 