#!/bin/bash

echo "🚀 RoluATM Unified Deployment Script"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Environment variables
WORLD_CLIENT_SECRET="sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19"
VITE_WORLD_APP_ID="app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db"
DATABASE_URL="postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

echo -e "${YELLOW}Deployment Options:${NC}"
echo "1. Deploy to Vercel (cloud backend + frontend)"
echo "2. Local development (local backend + deployed frontend)"
echo "3. Status check"
echo ""
read -p "Choose option (1-3): " OPTION

case $OPTION in
    1)
        echo -e "${BLUE}Deploying to Vercel...${NC}"
        
        # Check if logged into Vercel
        if ! vercel whoami > /dev/null 2>&1; then
            echo -e "${RED}Please login to Vercel first: vercel login${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Vercel authentication confirmed${NC}"
        
        # Deploy backend first
        echo ""
        echo -e "${BLUE}Step 1: Deploying Backend...${NC}"
        cd server
        
        # Deploy and get URL
        echo "Deploying backend to Vercel..."
        vercel --prod --yes > /tmp/backend_deploy.log 2>&1
        
        # Extract the URL from the deployment
        BACKEND_URL=$(grep -o 'https://[^[:space:]]*\.vercel\.app' /tmp/backend_deploy.log | head -1)
        if [ -z "$BACKEND_URL" ]; then
            echo -e "${RED}Failed to get backend URL, using fallback${NC}"
            BACKEND_URL="https://rolu-atm-backend.vercel.app"
        fi
        
        echo -e "${GREEN}Backend deployed: $BACKEND_URL${NC}"
        
        # Set backend environment variables
        echo "Setting backend environment variables..."
        echo $WORLD_CLIENT_SECRET | vercel env add WORLD_CLIENT_SECRET production --yes 2>/dev/null || true
        echo $DATABASE_URL | vercel env add DATABASE_URL production --yes 2>/dev/null || true
        echo "false" | vercel env add DEV_MODE production --yes 2>/dev/null || true
        echo "https://mini-app-azure.vercel.app" | vercel env add MINI_APP_URL production --yes 2>/dev/null || true
        
        # Deploy mini-app
        echo ""
        echo -e "${BLUE}Step 2: Deploying Mini App...${NC}"
        cd ../mini-app
        
        # Set mini-app environment variables before deployment
        echo $BACKEND_URL | vercel env add VITE_API_BASE_URL production --yes 2>/dev/null || true
        echo $VITE_WORLD_APP_ID | vercel env add VITE_WORLD_APP_ID production --yes 2>/dev/null || true
        
        vercel --prod --yes > /tmp/mini_deploy.log 2>&1
        MINI_URL=$(grep -o 'https://[^[:space:]]*\.vercel\.app' /tmp/mini_deploy.log | head -1)
        if [ -z "$MINI_URL" ]; then
            MINI_URL="https://mini-app-azure.vercel.app"
        fi
        echo -e "${GREEN}Mini app deployed: $MINI_URL${NC}"
        
        # Deploy kiosk-app
        echo ""
        echo -e "${BLUE}Step 3: Deploying Kiosk App...${NC}"
        cd ../kiosk-app
        
        # Set kiosk environment variables
        echo $BACKEND_URL | vercel env add VITE_API_BASE_URL production --yes 2>/dev/null || true
        
        vercel --prod --yes > /tmp/kiosk_deploy.log 2>&1
        KIOSK_URL=$(grep -o 'https://[^[:space:]]*\.vercel\.app' /tmp/kiosk_deploy.log | head -1)
        if [ -z "$KIOSK_URL" ]; then
            KIOSK_URL="https://kiosk-app-xi.vercel.app"
        fi
        echo -e "${GREEN}Kiosk app deployed: $KIOSK_URL${NC}"
        
        cd ..
        
        echo ""
        echo -e "${GREEN}🎉 Full Vercel Deployment Complete!${NC}"
        echo "===================================="
        echo ""
        echo "Your RoluATM system is now live:"
        echo "• Backend API: $BACKEND_URL"
        echo "• Mini App: $MINI_URL"
        echo "• Kiosk App: $KIOSK_URL"
        echo ""
        echo "Testing URLs:"
        echo "• Health check: curl $BACKEND_URL/health"
        echo "• Create transaction: Use kiosk app at $KIOSK_URL"
        echo "• Complete transaction: Mini app will be opened from QR code"
        ;;
        
    2)
        echo -e "${BLUE}Setting up local development with deployed frontend...${NC}"
        
        echo ""
        echo -e "${YELLOW}Configuration for local backend:${NC}"
        echo "1. Start your local backend: python3 pi_backend.py"
        echo "2. Your local backend will be at: http://localhost:8000"
        echo "3. Mini app is deployed at: https://mini-app-azure.vercel.app"
        echo "4. When creating transactions locally, use DEV_MODE=true"
        echo ""
        echo "Environment variables for local backend:"
        echo "export WORLD_CLIENT_SECRET=$WORLD_CLIENT_SECRET"
        echo "export DATABASE_URL=\"$DATABASE_URL\""
        echo "export DEV_MODE=true"
        echo "export MINI_APP_URL=https://mini-app-azure.vercel.app"
        echo ""
        echo -e "${GREEN}Local development setup ready!${NC}"
        echo ""
        echo "Your local backend will generate URLs like:"
        echo "https://mini-app-azure.vercel.app?backend=local&transaction_id=XXXXX"
        echo ""
        echo "This allows the deployed mini-app to connect back to your local backend."
        ;;
        
    3)
        echo -e "${BLUE}Checking deployment status...${NC}"
        
        echo ""
        echo "Current deployments:"
        echo "• Mini App: https://mini-app-azure.vercel.app"
        echo "• Kiosk App: https://kiosk-app-xi.vercel.app"
        echo ""
        echo "Testing mini app..."
        curl -s https://mini-app-azure.vercel.app > /dev/null && echo -e "${GREEN}✅ Mini app is live${NC}" || echo -e "${RED}❌ Mini app is down${NC}"
        
        echo "Testing kiosk app..."
        curl -s https://kiosk-app-xi.vercel.app > /dev/null && echo -e "${GREEN}✅ Kiosk app is live${NC}" || echo -e "${RED}❌ Kiosk app is down${NC}"
        
        echo ""
        echo "Testing local backend..."
        curl -s http://localhost:8000/health > /dev/null && echo -e "${GREEN}✅ Local backend is running${NC}" || echo -e "${YELLOW}⚠️ Local backend not running${NC}"
        
        # Check if there's a Vercel backend
        if command -v vercel &> /dev/null; then
            echo ""
            echo "Checking Vercel deployments..."
            vercel ls 2>/dev/null | grep -E "(server|backend)" && echo -e "${GREEN}✅ Backend found on Vercel${NC}" || echo -e "${YELLOW}⚠️ No backend on Vercel${NC}"
        fi
        ;;
        
    *)
        echo -e "${RED}Invalid option. Please choose 1, 2, or 3.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Next steps:${NC}"
case $OPTION in
    1)
        echo "• Test the complete flow using the kiosk app"
        echo "• Monitor deployments at https://vercel.com/dashboard"
        echo "• All transactions will be stored in your Neon database"
        ;;
    2)
        echo "• Start your local backend: python3 pi_backend.py"
        echo "• Test with kiosk app at http://localhost:3000"
        echo "• QR codes will point to deployed mini-app with backend=local parameter"
        ;;
    3)
        echo "• Use option 1 to deploy everything to Vercel"
        echo "• Use option 2 to set up local development"
        ;;
esac 