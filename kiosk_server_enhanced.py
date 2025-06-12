#!/usr/bin/env python3
"""
Enhanced HTTP server for RoluATM Kiosk App
Serves the built React app and handles API routes
"""

import os
import sys
import json
import uuid
import http.server
import socketserver
import urllib.parse
from pathlib import Path

# Configuration
PORT = 3000
DIST_DIR = "/home/rahiim/RoluATM/kiosk-app/dist"
VERCEL_API_URL = "https://rolu-api.vercel.app/api/v2"

class KioskHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced handler for the kiosk app with API support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-kiosk-id')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for API routes"""
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # For non-API POST requests, return 405
            self.send_error(405, "Method Not Allowed")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # Serve static files
            super().do_GET()
    
    def handle_api_request(self):
        """Handle API requests with local fallback"""
        try:
            if self.path == '/api/status':
                self.handle_status_request()
            elif self.path == '/api/transaction/create':
                self.handle_create_transaction()
            else:
                self.send_error(404, f"API endpoint not found: {self.path}")
        except Exception as e:
            print(f"Error handling API request {self.path}: {e}")
            self.send_error(500, "Internal server error")
    
    def handle_status_request(self):
        """Handle status requests"""
        response = {
            "status": "ok",
            "backend": "local",
            "hardware": {"tflex": "mock"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_create_transaction(self):
        """Handle transaction creation (mock for local testing)"""
        if self.command != 'POST':
            self.send_error(405, "Method Not Allowed")
            return
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode())
            amount = request_data.get('amount', 0)
            
            if amount <= 0:
                self.send_error(400, "Invalid amount")
                return
            
            # Get kiosk ID
            kiosk_id = self.get_kiosk_id()
            
            # Create mock transaction
            transaction_id = str(uuid.uuid4())
            quarters = int(amount / 0.25)
            total = amount + 0.50  # Add fee
            
            response = {
                "id": transaction_id,
                "amount": amount,
                "quarters": quarters,
                "total": total,
                "mini_app_url": f"https://mini-app-azure.vercel.app/pay/{transaction_id}",
                "status": "pending",
                "expires_at": "2024-01-01T00:15:00Z"
            }
            
            print(f"📝 Mock transaction created: ${amount} -> {quarters} quarters (ID: {transaction_id[:8]}...)")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"Error creating transaction: {e}")
            self.send_error(500, "Transaction creation failed")
    
    def get_kiosk_id(self):
        """Get the kiosk ID from file"""
        try:
            kiosk_id_file = "/home/rahiim/.rolu_kiosk_id"
            if os.path.exists(kiosk_id_file):
                with open(kiosk_id_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        
        # Fallback
        return "local-kiosk-test"
    
    def log_message(self, format, *args):
        # Enhanced logging
        timestamp = self.log_date_time_string()
        print(f"[{timestamp}] [{self.address_string()}] {format % args}")

def main():
    """Start the enhanced kiosk HTTP server"""
    
    # Check if dist directory exists
    if not os.path.exists(DIST_DIR):
        print(f"❌ Error: Dist directory not found: {DIST_DIR}")
        print("Please build the kiosk app first with: npm run build")
        sys.exit(1)
    
    # Check if index.html exists
    index_file = os.path.join(DIST_DIR, "index.html")
    if not os.path.exists(index_file):
        print(f"❌ Error: index.html not found: {index_file}")
        sys.exit(1)
    
    print(f"🚀 Starting Enhanced RoluATM Kiosk Server...")
    print(f"📁 Serving directory: {DIST_DIR}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔧 API endpoints: /api/status, /api/transaction/create")
    print(f"🔄 Press Ctrl+C to stop")
    
    try:
        with socketserver.TCPServer(("", PORT), KioskHTTPRequestHandler) as httpd:
            print(f"✅ Enhanced server started successfully on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use")
            print("Please stop any existing server or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 