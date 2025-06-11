#!/usr/bin/env python3
"""
Simple RoluATM Backend for Raspberry Pi with T-Flex Hardware
"""

import os
import json
import time
import uuid
import serial
import requests
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configuration
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://mini-app-azure.vercel.app")
DATABASE_URL = "postgresql://neondb_owner:npg_BwRjLZD4Qp0V@ep-crimson-meadow-a81cmjla-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
TFLEX_PORT = "/dev/ttyUSB0"  # Your T-Flex serial port
PORT = 8000

# CORS allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",                    # Local kiosk dev
    "http://localhost:3001",                    # Local mini dev
    "https://kiosk-app-xi.vercel.app",         # Production kiosk
    "https://mini-app-azure.vercel.app",       # Production mini
]

# In-memory transactions (you can add database later)
transactions = {}

class TFlexController:
    def __init__(self):
        try:
            self.serial = serial.Serial(TFLEX_PORT, 9600, timeout=2)
            print(f"✅ T-Flex connected on {TFLEX_PORT}")
            self.connected = True
        except:
            print(f"⚠️  T-Flex not found on {TFLEX_PORT}, using mock mode")
            self.connected = False
    
    def dispense_quarters(self, num_quarters):
        if not self.connected:
            print(f"🪙 MOCK: Dispensing {num_quarters} quarters")
            time.sleep(3)
            return True
        
        try:
            # Send command to T-Flex
            command = f"DISPENSE {num_quarters}\r\n"
            self.serial.write(command.encode())
            response = self.serial.readline().decode().strip()
            
            if "OK" in response:
                print(f"✅ Dispensed {num_quarters} quarters")
                return True
            else:
                print(f"❌ T-Flex error: {response}")
                return False
        except Exception as e:
            print(f"❌ Dispense error: {e}")
            return False

tflex = TFlexController()

class RoluATMHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/health":
            self.send_json({"status": "healthy", "hardware": {"tflex": "connected" if tflex.connected else "mock"}})
        
        elif path.startswith("/api/transaction/"):
            transaction_id = path.split("/")[-1]
            if transaction_id in transactions:
                self.send_json(transactions[transaction_id])
            else:
                self.send_error(404, "Transaction not found")
        
        else:
            self.send_error(404, "Not found")
    
    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        data = json.loads(body) if body else {}
        
        if path == "/api/transaction/create":
            # Create transaction
            fiat_amount = data.get('fiat_amount', 5.0)
            transaction_id = str(uuid.uuid4())
            quarters = int(fiat_amount / 0.25)
            
            transaction = {
                'id': transaction_id,
                'fiat_amount': fiat_amount,
                'quarters': quarters,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                'mini_app_url': f"{MINI_APP_URL}?transaction_id={transaction_id}",
                'progress': 0
            }
            
            transactions[transaction_id] = transaction
            print(f"✅ Created transaction {transaction_id} for ${fiat_amount} ({quarters} quarters)")
            self.send_json(transaction)
        
        elif path == "/api/transaction/pay":
            # Process payment and dispense
            transaction_id = data.get('transaction_id')
            
            if transaction_id in transactions:
                transaction = transactions[transaction_id]
                
                # Update status
                transaction['status'] = 'dispensing'
                transaction['progress'] = 50
                transaction['paid_at'] = datetime.now(timezone.utc).isoformat()
                
                # Dispense quarters with T-Flex
                if tflex.dispense_quarters(transaction['quarters']):
                    transaction['status'] = 'complete'
                    transaction['progress'] = 100
                    print(f"✅ Transaction {transaction_id} completed")
                else:
                    transaction['status'] = 'failed'
                    print(f"❌ Transaction {transaction_id} failed")
                
                self.send_json(transaction)
            else:
                self.send_error(404, "Transaction not found")
        
        else:
            self.send_error(404, "Not found")
    
    def send_cors_headers(self):
        origin = self.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            allowed_origin = origin
        else:
            allowed_origin = ALLOWED_ORIGINS[0]  # Default to localhost for development
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
    
    def send_json(self, data):
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == '__main__':
    print("🎰 RoluATM Pi Backend Starting...")
    print(f"✅ Server: http://localhost:{PORT}")
    print(f"✅ Mini App: {MINI_APP_URL}")
    print(f"✅ T-Flex: {'Connected' if tflex.connected else 'Mock Mode'}")
    
    server = HTTPServer(('0.0.0.0', PORT), RoluATMHandler)
    server.serve_forever() 