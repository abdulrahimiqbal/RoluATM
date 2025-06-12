#!/usr/bin/env python3
"""
Final RoluATM Kiosk Server
Serves the React kiosk app and provides local API endpoints with payment page
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

# Payment page HTML
PAYMENT_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RoluATM Payment - Local Test</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .logo { font-size: 2.5em; margin-bottom: 20px; }
        h1 { color: #333; margin-bottom: 10px; }
        .status { padding: 15px; border-radius: 10px; margin: 20px 0; font-weight: bold; }
        .pending { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
        .processing { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .verified { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .completed { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .details { background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: left; }
        .detail-row { display: flex; justify-content: space-between; margin: 5px 0; }
        .btn { background: #007bff; color: white; border: none; padding: 12px 30px; border-radius: 8px; cursor: pointer; font-size: 16px; margin: 10px; }
        .btn:hover { background: #0056b3; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #007bff; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🏧</div>
        <h1>RoluATM Payment</h1>
        <p>Local Test Environment</p>
        
        <div id="status" class="status pending">
            <div class="spinner"></div>
            Loading transaction...
        </div>
        
        <div id="details" class="details" style="display: none;">
            <div class="detail-row"><span>Amount:</span><span id="amount">-</span></div>
            <div class="detail-row"><span>Quarters:</span><span id="quarters">-</span></div>
            <div class="detail-row"><span>Fee:</span><span>$0.50</span></div>
            <div class="detail-row"><strong>Total:</strong><strong id="total">-</strong></div>
        </div>
        
        <button id="simulateBtn" class="btn" onclick="simulatePayment()" style="display: none;">Simulate Payment</button>
        <button id="backBtn" class="btn" onclick="goBack()">Back to Kiosk</button>
        
        <p style="margin-top: 20px; color: #666; font-size: 14px;">🚧 This is a local test page.<br>In production, this would be the World ID verification flow.</p>
    </div>

    <script>
        let transactionId = null;
        let pollInterval = null;
        
        function getTransactionId() {
            const path = window.location.pathname;
            const parts = path.split('/');
            return parts[parts.length - 1];
        }
        
        function updateStatus(transaction) {
            const statusDiv = document.getElementById('status');
            const detailsDiv = document.getElementById('details');
            const simulateBtn = document.getElementById('simulateBtn');
            
            if (!transaction) {
                statusDiv.className = 'status error';
                statusDiv.innerHTML = '❌ Transaction not found';
                return;
            }
            
            document.getElementById('amount').textContent = `$${transaction.amount.toFixed(2)}`;
            document.getElementById('quarters').textContent = transaction.quarters;
            document.getElementById('total').textContent = `$${transaction.total.toFixed(2)}`;
            detailsDiv.style.display = 'block';
            
            const status = transaction.status;
            statusDiv.className = `status ${status}`;
            
            switch (status) {
                case 'pending':
                    statusDiv.innerHTML = '⏳ Waiting for payment...';
                    simulateBtn.style.display = 'block';
                    break;
                case 'processing':
                    statusDiv.innerHTML = '🔄 Processing payment...';
                    simulateBtn.style.display = 'none';
                    break;
                case 'verified':
                    statusDiv.innerHTML = '✅ Payment verified!';
                    simulateBtn.style.display = 'none';
                    break;
                case 'completed':
                    statusDiv.innerHTML = '🎉 Transaction completed!<br>Your quarters are being dispensed.';
                    simulateBtn.style.display = 'none';
                    clearInterval(pollInterval);
                    setTimeout(() => window.close(), 3000);
                    break;
                default:
                    statusDiv.innerHTML = `Status: ${status}`;
            }
        }
        
        function pollStatus() {
            if (!transactionId) return;
            fetch(`/api/transaction/${transactionId}/status`)
                .then(response => response.json())
                .then(transaction => updateStatus(transaction))
                .catch(error => console.error('Error polling status:', error));
        }
        
        function simulatePayment() {
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status processing';
            statusDiv.innerHTML = '🔄 Simulating payment...';
            setTimeout(() => pollStatus(), 2000);
        }
        
        function goBack() {
            window.location.href = '/';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            transactionId = getTransactionId();
            if (transactionId) {
                pollStatus();
                pollInterval = setInterval(pollStatus, 2000);
            } else {
                updateStatus(null);
            }
        });
    </script>
</body>
</html>"""

class FinalKioskHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Handle payment page routes /pay/{transaction_id}
        if parsed_path.path.startswith('/pay/'):
            self.send_payment_page()
        # Handle API endpoints
        elif parsed_path.path.startswith('/api/'):
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
    
    def send_payment_page(self):
        """Serve the payment page for QR code redirects"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(PAYMENT_PAGE_HTML.encode('utf-8'))
    
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
    print("🚀 Starting Final RoluATM Kiosk Server...")
    print(f"📁 Serving directory: {SERVE_DIR}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔧 API endpoints: /api/status, /api/transaction/create, /api/transaction/{{id}}/status")
    print(f"💳 Payment pages: /pay/{{transaction_id}}")
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
        with socketserver.TCPServer(("", PORT), FinalKioskHandler) as httpd:
            print(f"✅ Final server started successfully on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 