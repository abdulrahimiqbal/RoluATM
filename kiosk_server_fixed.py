#!/usr/bin/env python3
"""
Enhanced RoluATM Kiosk Server
Serves the React kiosk app and provides local API endpoints
"""

import http.server
import socketserver
import json
import os
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta
import socket

PORT = 3000
SERVE_DIR = "/home/rahiim/RoluATM/kiosk-app/dist"

# In-memory storage for transactions (temporary)
transactions = {}

class EnhancedKioskHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Handle API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api_get(parsed_path)
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_post(parsed_path)
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_get(self, parsed_path):
        if parsed_path.path == '/api/status':
            self.send_api_response({
                "status": "ok",
                "backend": "local",
                "hardware": {"tflex": "mock"},
                "timestamp": "2024-01-01T00:00:00Z"
            })
        elif parsed_path.path.startswith('/api/transaction/') and parsed_path.path.endswith('/status'):
            # Extract transaction ID from path: /api/transaction/{id}/status
            path_parts = parsed_path.path.split('/')
            if len(path_parts) >= 4:
                transaction_id = path_parts[3]
                self.handle_transaction_status(transaction_id)
            else:
                self.send_error(400, "Invalid transaction ID")
        else:
            self.send_error(404, "API endpoint not found: " + parsed_path.path)
    
    def handle_api_post(self, parsed_path):
        if parsed_path.path == '/api/transaction/create':
            self.handle_transaction_create()
        else:
            self.send_error(404, "API endpoint not found: " + parsed_path.path)
    
    def handle_transaction_status(self, transaction_id):
        """Handle transaction status requests"""
        if transaction_id in transactions:
            transaction = transactions[transaction_id]
            
            # Simulate transaction progression for demo
            now = datetime.now()
            created_time = transaction.get('created_at', now)
            elapsed = (now - created_time).total_seconds()
            
            if elapsed < 30:  # First 30 seconds - pending
                status = "pending"
            elif elapsed < 60:  # Next 30 seconds - processing  
                status = "processing"
            elif elapsed < 90:  # Next 30 seconds - verified
                status = "verified"
            else:  # After 90 seconds - completed
                status = "completed"
            
            response = {
                "id": transaction["id"],
                "amount": transaction["amount"],
                "quarters": transaction["quarters"],
                "total": transaction["total"],
                "status": status,
                "mini_app_url": transaction["mini_app_url"],
                "expires_at": transaction["expires_at"],
                "updated_at": now.isoformat()
            }
            self.send_api_response(response)
        else:
            # Return a default response to prevent app crashes
            self.send_api_response({
                "id": transaction_id,
                "status": "not_found",
                "error": "Transaction not found"
            }, status=404)
    
    def handle_transaction_create(self):
        """Handle transaction creation"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            amount = float(data.get('amount', 0))
            quarters = int(amount * 4)  # $0.25 per quarter
            fee = 0.50  # $0.50 fee
            total = amount + fee
            
            transaction_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(minutes=15)
            
            transaction = {
                "id": transaction_id,
                "amount": amount,
                "quarters": quarters,
                "total": total,
                "mini_app_url": f"http://localhost:3000/pay/{transaction_id}",  # Local URL for testing
                "status": "pending",
                "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "created_at": datetime.now()
            }
            
            # Store transaction
            transactions[transaction_id] = transaction
            
            # Return response without created_at
            response = {k: v for k, v in transaction.items() if k != 'created_at'}
            
            self.send_api_response(response)
            
        except Exception as e:
            self.send_error(500, f"Error creating transaction: {str(e)}")
    
    def send_api_response(self, data, status=200):
        """Send JSON API response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Enhanced logging with timestamp
        timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        client_ip = self.address_string()
        print(f"[{timestamp}] [{client_ip}] {format % args}")

def check_port_available(port):
    """Check if port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False

def main():
    print("🚀 Starting Fixed RoluATM Kiosk Server...")
    print(f"📁 Serving directory: {SERVE_DIR}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔧 API endpoints: /api/status, /api/transaction/create, /api/transaction/{{id}}/status")
    print("🔄 Press Ctrl+C to stop")
    
    # Check if port is available
    if not check_port_available(PORT):
        print(f"❌ Error: Port {PORT} is already in use")
        print("Please stop any existing server or use a different port")
        return 1
    
    # Check if serve directory exists
    if not os.path.exists(SERVE_DIR):
        print(f"❌ Error: Serve directory does not exist: {SERVE_DIR}")
        return 1
    
    try:
        with socketserver.TCPServer(("", PORT), EnhancedKioskHandler) as httpd:
            print(f"✅ Fixed server started successfully on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 