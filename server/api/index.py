from http.server import BaseHTTPRequestHandler
import json
import uuid
import os
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

# Environment variables
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://mini-app-azure.vercel.app')

# In-memory storage for transactions
transactions = {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_OPTIONS(self):
        self.send_cors_response(200, {'message': 'OK'})
    
    def handle_request(self, method):
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"📝 {method} {path}")
            
            # Health check
            if path in ['/health', '/api/health', '/api/status', '/']:
                self.send_cors_response(200, {
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'environment': 'vercel',
                    'dev_mode': DEV_MODE,
                    'message': 'RoluATM Backend is running on Vercel!'
                })
                return
            
            # Create transaction
            if path == '/api/transaction/create' and method == 'POST':
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > 0:
                        body = self.rfile.read(content_length).decode('utf-8')
                        data = json.loads(body)
                    else:
                        data = {}
                    
                    amount = float(data.get('amount', 5.0))
                    
                    # Create transaction
                    transaction_id = str(uuid.uuid4())
                    quarters = int(amount * 4)  # $1 = 4 quarters
                    
                    transaction = {
                        'id': transaction_id,
                        'amount': amount,
                        'quarters': quarters,
                        'status': 'pending',
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'mini_app_url': f"{MINI_APP_URL}?transaction_id={transaction_id}"
                    }
                    
                    transactions[transaction_id] = transaction
                    
                    print(f"✅ Created transaction {transaction_id} for ${amount} ({quarters} quarters)")
                    
                    self.send_cors_response(200, transaction)
                    return
                    
                except Exception as e:
                    print(f"❌ Error creating transaction: {e}")
                    self.send_cors_response(400, {'error': 'Invalid request data'})
                    return
            
            # Get transaction
            if path.startswith('/api/transaction/') and method == 'GET' and not path.endswith('/pay'):
                transaction_id = path.split('/')[-1]
                
                if transaction_id in transactions:
                    self.send_cors_response(200, transactions[transaction_id])
                else:
                    self.send_cors_response(404, {'error': 'Transaction not found'})
                return
            
            # Pay transaction (mock)
            if path.startswith('/api/transaction/') and path.endswith('/pay') and method == 'POST':
                transaction_id = path.split('/')[-2]
                
                if transaction_id in transactions:
                    # Mock World ID verification and payment
                    transactions[transaction_id]['status'] = 'completed'
                    transactions[transaction_id]['completed_at'] = datetime.now(timezone.utc).isoformat()
                    
                    print(f"🔒 Mock World ID verification for {transaction_id}")
                    print(f"🪙 Mock dispensing {transactions[transaction_id]['quarters']} quarters...")
                    
                    self.send_cors_response(200, {
                        'success': True,
                        'message': 'Payment completed',
                        'transaction': transactions[transaction_id]
                    })
                else:
                    self.send_cors_response(404, {'error': 'Transaction not found'})
                return
            
            # Default 404
            self.send_cors_response(404, {'error': 'Not found'})
            
        except Exception as e:
            print(f"❌ Server error: {e}")
            self.send_cors_response(500, {'error': 'Internal server error'})
    
    def send_cors_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_body = json.dumps(data).encode('utf-8')
        self.wfile.write(response_body) 