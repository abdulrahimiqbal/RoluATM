#!/usr/bin/env python3
"""
RoluATM Backend for Vercel Deployment
Simplified version for Vercel serverless functions
"""

import os
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler
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
            if path in ['/health', '/api/status']:
                self.send_cors_response(200, {
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'hardware': {
                        'coinDispenser': 'ready',
                        'network': 'connected', 
                        'security': 'active',
                        'database': 'in-memory'
                    }
                })
                return
            
            # Create transaction
            if path == '/api/transaction/create' and method == 'POST':
                try:
                    # Read request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > 0:
                        body = self.rfile.read(content_length).decode('utf-8')
                        data = json.loads(body)
                    else:
                        data = {'amount': 5.0}
                    
                    fiat_amount = float(data.get('fiat_amount', data.get('amount', 5.0)))
                    transaction_id = str(uuid.uuid4())
                    quarters = int(fiat_amount / 0.25)
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
                    
                    # Create mini app URL
                    mini_app_url = f"https://mini-app-azure.vercel.app?transaction_id={transaction_id}"
                    
                    # Create transaction
                    transaction = {
                        'id': transaction_id,
                        'fiat_amount': fiat_amount,
                        'quarters': quarters,
                        'status': 'pending',
                        'mini_app_url': mini_app_url,
                        'progress': 0,
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'expires_at': expires_at.isoformat()
                    }
                    
                    transactions[transaction_id] = transaction
                    
                    print(f"✅ Created transaction {transaction_id} for ${fiat_amount} ({quarters} quarters)")
                    
                    self.send_cors_response(200, transaction)
                    return
                    
                except Exception as e:
                    print(f"❌ Transaction creation error: {e}")
                    self.send_cors_response(500, {'error': str(e)})
                    return
            
            # Get transaction
            if path.startswith('/api/transaction/') and method == 'GET':
                try:
                    transaction_id = path.split('/')[-1]
                    
                    transaction = transactions.get(transaction_id)
                    if transaction:
                        self.send_cors_response(200, transaction)
                    else:
                        self.send_cors_response(404, {'error': 'Transaction not found'})
                    return
                except Exception as e:
                    print(f"❌ Transaction lookup error: {e}")
                    self.send_cors_response(500, {'error': str(e)})
                    return
            
            # Process payment
            if path == '/api/transaction/pay' and method == 'POST':
                try:
                    # Read request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > 0:
                        body = self.rfile.read(content_length).decode('utf-8')
                        data = json.loads(body)
                    else:
                        self.send_cors_response(400, {'error': 'No request body'})
                        return
                    
                    transaction_id = data.get('transaction_id')
                    
                    if not transaction_id:
                        self.send_cors_response(400, {'error': 'Transaction ID required'})
                        return
                    
                    transaction = transactions.get(transaction_id)
                    if not transaction:
                        self.send_cors_response(404, {'error': 'Transaction not found'})
                        return
                    
                    # Check if expired
                    expires_at = datetime.fromisoformat(transaction['expires_at'].replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expires_at:
                        transaction['status'] = 'expired'
                        self.send_cors_response(400, {'error': 'Transaction expired'})
                        return
                    
                    # Check if already processed
                    if transaction['status'] != 'pending':
                        self.send_cors_response(400, {'error': f'Transaction already {transaction["status"]}'})
                        return
                    
                    # Mock World ID verification
                    print(f"🔒 Mock World ID verification for {transaction_id}")
                    
                    # Update status to dispensing
                    transaction['status'] = 'dispensing'
                    transaction['progress'] = 50
                    
                    # Mock dispense quarters
                    print(f"🪙 Mock dispensing {transaction['quarters']} quarters...")
                    time.sleep(1)
                    
                    # Complete transaction
                    transaction['status'] = 'complete'
                    transaction['progress'] = 100
                    transaction['paid_at'] = datetime.now(timezone.utc).isoformat()
                    
                    print(f"✅ Transaction {transaction_id} completed successfully")
                    
                    self.send_cors_response(200, transaction)
                    return
                    
                except Exception as e:
                    print(f"❌ Payment processing error: {e}")
                    self.send_cors_response(500, {'error': str(e)})
                    return
            
            # Default response
            self.send_cors_response(404, {'error': 'Not found', 'path': path, 'method': method})
            
        except Exception as e:
            print(f"❌ Handler error: {e}")
            self.send_cors_response(500, {'error': f'Internal server error: {str(e)}'})
    
    def send_cors_response(self, status_code, data):
        """Send response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_body = json.dumps(data, default=str)
        self.wfile.write(response_body.encode('utf-8'))

# Vercel entry point
def app(environ, start_response):
    """WSGI entry point for Vercel"""
    try:
        # Convert WSGI environ to event format
        event = {
            'httpMethod': environ['REQUEST_METHOD'],
            'path': environ.get('PATH_INFO', '/'),
            'queryStringParameters': {},
            'headers': {},
            'body': ''
        }
        
        # Read body if present
        if 'CONTENT_LENGTH' in environ and environ['CONTENT_LENGTH']:
            content_length = int(environ['CONTENT_LENGTH'])
            if content_length > 0:
                event['body'] = environ['wsgi.input'].read(content_length).decode('utf-8')
        
        response = handler(event)
        
        status = f"{response['statusCode']} OK"
        headers = [(k, v) for k, v in response['headers'].items()]
        
        start_response(status, headers)
        return [response['body'].encode()]
        
    except Exception as e:
        print(f"❌ WSGI error: {e}")
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [json.dumps({'error': str(e)}).encode()] 