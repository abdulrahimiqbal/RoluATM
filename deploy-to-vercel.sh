#!/bin/bash

echo "🚀 RoluATM Vercel Deployment Script"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if logged into Vercel
echo -e "${BLUE}Checking Vercel authentication...${NC}"
if ! vercel whoami > /dev/null 2>&1; then
    echo -e "${RED}Please login to Vercel first: vercel login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Vercel authentication confirmed${NC}"

# Environment variables
WORLD_CLIENT_SECRET="sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19"
VITE_WORLD_APP_ID="app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db"
DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

echo ""
echo -e "${BLUE}Step 1: Deploying Backend API...${NC}"
echo "=================================="

cd server

# Deploy backend
echo "Deploying to Vercel..."
vercel --prod --yes

# Set backend environment variables
echo "Setting environment variables..."
echo $WORLD_CLIENT_SECRET | vercel env add WORLD_CLIENT_SECRET production
echo $DATABASE_URL | vercel env add DATABASE_URL production
echo "false" | vercel env add DEV_MODE production
echo $VITE_WORLD_APP_ID | vercel env add VITE_WORLD_APP_ID production
echo "https://roluatm-mini.vercel.app" | vercel env add MINI_APP_URL production

echo -e "${GREEN}✅ Backend deployed${NC}"

echo ""
echo -e "${BLUE}Step 2: Deploying Mini App...${NC}"
echo "=============================="

cd ../mini-app

# Deploy mini app
echo "Deploying to Vercel..."
vercel --prod --yes

# Set mini app environment variables  
echo "Setting environment variables..."
echo "https://roluatm-backend.vercel.app" | vercel env add VITE_API_URL production
echo $VITE_WORLD_APP_ID | vercel env add VITE_WORLD_APP_ID production

echo -e "${GREEN}✅ Mini app deployed${NC}"

echo ""
echo -e "${BLUE}Step 3: Deploying Kiosk App...${NC}"
echo "==============================="

cd ../kiosk-app

# Deploy kiosk app
echo "Deploying to Vercel..."
vercel --prod --yes

# Set kiosk app environment variables
echo "Setting environment variables..."
echo "https://roluatm-backend.vercel.app" | vercel env add VITE_API_URL production

echo -e "${GREEN}✅ Kiosk app deployed${NC}"

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "======================="
echo ""
echo "Your RoluATM apps are now live:"
echo "• Backend API: https://roluatm-backend.vercel.app"
echo "• Mini App: https://roluatm-mini.vercel.app" 
echo "• Kiosk App: https://roluatm-kiosk.vercel.app"
echo ""
echo "Test the deployment:"
echo "curl https://roluatm-backend.vercel.app/health"
echo ""
echo "Manage your deployments at: https://vercel.com/dashboard"

cd .. 