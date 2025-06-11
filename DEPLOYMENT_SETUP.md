# 🚀 RoluATM Deployment Setup Guide

## Overview
This guide sets up automatic deployment from GitHub to Vercel for both the kiosk and mini apps, completely independent of your local development environment.

## Prerequisites
- ✅ GitHub CLI installed and authenticated
- ✅ Vercel account 
- ✅ Local repository with all changes committed
- ✅ Your Pi's public IP address or domain name

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

**Environment Variables for Kiosk (Production):**
```
VITE_API_URL=https://your-pi-domain.com:8000
```
*Replace `your-pi-domain.com` with your actual Pi's public IP or domain*

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

**Environment Variables for Mini App (Production):**
```
VITE_API_URL=https://your-pi-domain.com:8000
VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db
```
*Replace `your-pi-domain.com` with your actual Pi's public IP or domain*

## 📱 Production URLs

After deployment, you'll get URLs like:
- **Kiosk App**: `https://rolu-atm-kiosk.vercel.app`
- **Mini App**: `https://rolu-atm-mini.vercel.app`

## 🔄 Environment Separation

### 🏠 Local Development (Your Mac)
- **Backend**: `http://localhost:8000` (pi_backend.py)
- **Kiosk**: `http://localhost:3000` (points to localhost backend)
- **Mini**: `http://localhost:3001` (points to localhost backend)
- **Environment**: Uses localhost for all API calls

### 🌍 Production (Vercel + Pi)
- **Backend**: Your Pi's public domain/IP (e.g., `https://your-pi.com:8000`)
- **Kiosk**: `https://rolu-atm-kiosk.vercel.app` (points to Pi backend)
- **Mini**: `https://rolu-atm-mini.vercel.app` (points to Pi backend)
- **Environment**: Uses your Pi's public URL for API calls

## 🏗️ Pi Setup for Production

### 1. Make Pi Backend Accessible
Your Pi needs to be accessible from the internet. Options:

**Option A: Port Forwarding (Recommended)**
```bash
# Forward port 8000 on your router to your Pi's local IP
# Router settings: External 8000 → Internal Pi-IP:8000
```

**Option B: Use ngrok (Testing)**
```bash
# On your Pi
ngrok http 8000
# Use the ngrok URL in Vercel environment variables
```

**Option C: Custom Domain (Advanced)**
```bash
# Set up dynamic DNS + SSL certificates
# Point your domain to your public IP
```

### 2. Update Pi Backend for Production
```python
# In pi_backend.py, update MINI_APP_URL
MINI_APP_URL = "https://rolu-atm-mini.vercel.app"
```

### 3. Enable CORS for Production
The Pi backend needs to allow requests from Vercel domains:
```python
# Add to pi_backend.py
ALLOWED_ORIGINS = [
    "https://rolu-atm-kiosk.vercel.app",
    "https://rolu-atm-mini.vercel.app",
    "http://localhost:3000",  # Keep for local dev
    "http://localhost:3001"   # Keep for local dev
]
```

## 🚦 Testing Production Deployment

### Test Kiosk App:
1. Visit `https://rolu-atm-kiosk.vercel.app`
2. Should connect to your Pi's backend
3. QR codes should point to production mini app

### Test Mini App:
1. Visit `https://rolu-atm-mini.vercel.app?transaction_id=test`
2. Should connect to your Pi's backend
3. World ID verification should work

## 🔄 Development Workflow

### Local Development:
```bash
# Everything runs locally
npm run dev          # Starts all services on localhost
python3 pi_backend.py # Backend on localhost:8000
```

### Production Updates:
```bash
# Make changes locally and test
git add .
git commit -m "Update features"
git push  # Automatically deploys to Vercel with production URLs
```

## 🎰 Complete Architecture (Independent)

```
Local Development          Production Deployment
┌─────────────────┐        ┌─────────────────┐    ┌─────────────────┐
│   Your Mac      │        │   Raspberry Pi  │    │     Vercel      │
│                 │        │                 │    │                 │
│ ┌─────────────┐ │        │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ localhost   │ │        │ │pi_backend   │ │◄───┤ │ Kiosk App   │ │
│ │   :8000     │ │        │ │   :8000     │ │    │ │(Global CDN) │ │
│ └─────────────┘ │        │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │        │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │localhost    │ │        │ │  T-Flex     │ │    │ │  Mini App   │ │
│ │ :3000/:3001 │ │        │ │ Dispenser   │ │    │ │(Global CDN) │ │
│ └─────────────┘ │        │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘        └─────────────────┘    └─────────────────┘
        │                           │                       │
        └─── Local Testing ─────────┼───── Production ──────┘
                                    │
                              Hardware Control
                               (Serial/USB)
```

## 🎉 Benefits of Independent Deployment

- **🏠 Local Development**: Fast iteration, no internet required
- **🌍 Production**: Global CDN, works from anywhere
- **🔒 Security**: Pi backend only accepts requests from known domains
- **⚡ Performance**: Vercel CDN serves frontend instantly worldwide
- **🛡️ Isolation**: Local development doesn't affect production
- **🔄 Auto-deploy**: Push to GitHub → Instant production updates

## 📋 Next Steps

1. **Get your Pi's public IP/domain**
2. **Deploy to Vercel with production environment variables**
3. **Update Pi backend CORS and MINI_APP_URL**
4. **Test complete flow from anywhere in the world**

---

**Your deployment will be completely independent - develop locally, deploy globally!** 🚀 