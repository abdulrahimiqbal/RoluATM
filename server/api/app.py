#!/usr/bin/env python3
"""
RoluATM Simple Backend for Vercel Deployment
Handles transaction creation, World ID verification, and mock T-Flex dispenser
"""

import os
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import urllib.request
import urllib.error

# Environment variables
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL') 
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://roluatm-mini.vercel.app')

# In-memory storage for demo (replace with real DB for production)
transactions = {}

def create_response(status_code, data):
    """Create HTTP response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }

def verify_world_id_mock(transaction_id):
    """Mock World ID verification for testing"""
    print(f"🔒 Mock World ID verification for {transaction_id}")
    return True

def dispense_quarters_mock(num_quarters, transaction_id):
    """Mock quarter dispensing"""
    print(f"🪙 Mock dispensing {num_quarters} quarters...")
    time.sleep(2)  # Simulate dispense time
    return True

def handler(request, context=None):
    """Main Vercel handler"""
    method = os.getenv('REQUEST_METHOD', 'GET')
    path = os.getenv('VERCEL_URL_PATH', '/')
    
    # Handle CORS preflight
    if method == 'OPTIONS':
        return create_response(200, {'message': 'OK'})
    
    # Health check
    if path == '/health':
        return create_response(200, {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'hardware': {
                'coinDispenser': 'ready',
                'network': 'connected', 
                'security': 'active'
            }
        })
    
    # Create transaction
    if path == '/api/transaction/create' and method == 'POST':
        try:
            # Parse request body
            content_length = int(os.getenv('CONTENT_LENGTH', 0))
            if content_length > 0:
                import sys
                body = sys.stdin.read(content_length)
                data = json.loads(body)
            else:
                data = {'fiat_amount': 5.0}  # Default
            
            fiat_amount = data.get('fiat_amount', 5.0)
            transaction_id = str(uuid.uuid4())
            quarters = int(fiat_amount / 0.25)
            
            # Create transaction
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
            print(f"✅ Created transaction {transaction_id} for ${fiat_amount}")
            
            return create_response(200, transaction)
            
        except Exception as e:
            print(f"❌ Transaction creation error: {e}")
            return create_response(500, {'error': str(e)})
    
    # Get transaction
    if path.startswith('/api/transaction/') and method == 'GET':
        transaction_id = path.split('/')[-1]
        
        if transaction_id in transactions:
            return create_response(200, transactions[transaction_id])
        else:
            return create_response(404, {'error': 'Transaction not found'})
    
    # Process payment
    if path == '/api/transaction/pay' and method == 'POST':
        try:
            # Parse request body
            content_length = int(os.getenv('CONTENT_LENGTH', 0))
            if content_length > 0:
                import sys
                body = sys.stdin.read(content_length)
                data = json.loads(body)
            else:
                return create_response(400, {'error': 'No request body'})
            
            transaction_id = data.get('transaction_id')
            
            if not transaction_id or transaction_id not in transactions:
                return create_response(404, {'error': 'Transaction not found'})
            
            transaction = transactions[transaction_id]
            
            # Check if expired
            expires_at = datetime.fromisoformat(transaction['expires_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                transaction['status'] = 'expired'
                return create_response(400, {'error': 'Transaction expired'})
            
            # Mock World ID verification
            if not verify_world_id_mock(transaction_id):
                return create_response(400, {'error': 'World ID verification failed'})
            
            # Update status
            transaction['status'] = 'dispensing'
            transaction['progress'] = 50
            transaction['paid_at'] = datetime.now(timezone.utc).isoformat()
            
            # Mock dispense quarters
            if dispense_quarters_mock(transaction['quarters'], transaction_id):
                transaction['status'] = 'complete'
                transaction['progress'] = 100
                print(f"✅ Transaction {transaction_id} completed successfully")
            else:
                transaction['status'] = 'failed'
                transaction['progress'] = 0
                print(f"❌ Transaction {transaction_id} failed")
            
            return create_response(200, transaction)
            
        except Exception as e:
            print(f"❌ Payment processing error: {e}")
            return create_response(500, {'error': str(e)})
    
    # Default response
    return create_response(404, {'error': 'Not found'})

# For local testing
if __name__ == '__main__':
    print("🎰 RoluATM Simple Backend")
    print("========================")
    print("Running locally on port 8000...")
    
    import http.server
    import socketserver
    
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            os.environ['REQUEST_METHOD'] = 'GET'
            os.environ['VERCEL_URL_PATH'] = self.path
            
            response = handler(None)
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
        
        def do_POST(self):
            os.environ['REQUEST_METHOD'] = 'POST'
            os.environ['VERCEL_URL_PATH'] = self.path
            
            content_length = int(self.headers['Content-Length'])
            os.environ['CONTENT_LENGTH'] = str(content_length)
            
            # Read body
            import sys
            old_stdin = sys.stdin
            from io import StringIO
            sys.stdin = StringIO(self.rfile.read(content_length).decode())
            
            response = handler(None)
            
            sys.stdin = old_stdin
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
        
        def do_OPTIONS(self):
            os.environ['REQUEST_METHOD'] = 'OPTIONS'
            response = handler(None)
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
    
    with socketserver.TCPServer(("", 8000), Handler) as httpd:
        httpd.serve_forever() 