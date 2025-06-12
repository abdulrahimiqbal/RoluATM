#!/bin/bash

# RoluATM Pi Status Check
echo "🍓 RoluATM Raspberry Pi Status"
echo "=============================="

# Check services
echo "📋 Service Status:"
echo "Backend:  $(systemctl is-active rolu-backend.service)"
echo "Kiosk:    $(systemctl is-active rolu-kiosk.service)"
echo ""

# Check network endpoints
echo "🌐 Network Endpoints:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API: http://192.168.1.250:8000 (healthy)"
else
    echo "❌ Backend API: http://192.168.1.250:8000 (down)"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Kiosk App:   http://192.168.1.250:3000 (serving)"
else
    echo "❌ Kiosk App:   http://192.168.1.250:3000 (down)"
fi
echo ""

# Check hardware
echo "🔧 Hardware Status:"
if [ -e /dev/ttyUSB0 ]; then
    echo "✅ T-Flex:     Connected (/dev/ttyUSB0)"
else
    echo "⚠️  T-Flex:     Mock Mode (no hardware)"
fi
echo ""

# Show recent logs
echo "📝 Recent Backend Logs:"
sudo journalctl -u rolu-backend.service --no-pager -n 3 --since "5 minutes ago" 2>/dev/null || echo "No recent logs"
echo ""

echo "🎯 Quick Test:"
echo "Transaction creation test..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/transaction/create -H "Content-Type: application/json" -d '{"amount": 5}' 2>/dev/null)
if echo "$RESPONSE" | grep -q '"id"'; then
    TRANSACTION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "✅ Transaction created: $TRANSACTION_ID"
else
    echo "❌ Transaction creation failed"
fi
echo ""

echo "🔗 Access URLs:"
echo "Kiosk Interface: http://192.168.1.250:3000"
echo "Backend API:     http://192.168.1.250:8000"
echo "Mini App:        https://mini-app-azure.vercel.app" 
 