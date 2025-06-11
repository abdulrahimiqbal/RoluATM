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

# In-memory storage for transactions (will be replaced with database)
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
            query_params = parse_qs(parsed_url.query)
            
            print(f"📝 {method} {path}")
            
            # Health check
            if path in ['/health', '/api/status']:
                self.send_cors_response(200, {
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'environment': 'vercel',
                    'database_configured': bool(DATABASE_URL),
                    'world_client_configured': bool(WORLD_CLIENT_SECRET)
                })
                return
            
            # Create transaction
            if path == '/api/transaction/create' and method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body)
                else:
                    data = {}
                
                amount = data.get('amount', 5.0)
                transaction_id = str(uuid.uuid4())
                
                # Calculate quarters (25 cents each)
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
                
                self.send_cors_response(200, {
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'quarters': quarters,
                    'mini_app_url': transaction['mini_app_url'],
                    'status': 'pending'
                })
                return
            
            # Get transaction
            if path.startswith('/api/transaction/') and method == 'GET':
                transaction_id = path.split('/')[-1]
                
                if transaction_id in transactions:
                    self.send_cors_response(200, transactions[transaction_id])
                else:
                    self.send_cors_response(404, {'error': 'Transaction not found'})
                return
            
            # Update transaction payment
            if path.startswith('/api/transaction/') and path.endswith('/payment') and method == 'POST':
                transaction_id = path.split('/')[-2]
                
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body)
                else:
                    data = {}
                
                if transaction_id in transactions:
                    # Update transaction status
                    transactions[transaction_id]['status'] = 'paid'
                    transactions[transaction_id]['payment_verified'] = True
                    transactions[transaction_id]['paid_at'] = datetime.now(timezone.utc).isoformat()
                    
                    self.send_cors_response(200, {
                        'success': True,
                        'transaction': transactions[transaction_id]
                    })
                else:
                    self.send_cors_response(404, {'error': 'Transaction not found'})
                return
            
            # Default 404
            self.send_cors_response(404, {'error': 'Not found'})
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.send_cors_response(500, {'error': 'Internal server error', 'details': str(e)})
    
    def send_cors_response(self, status_code, data):
        """Send JSON response with CORS headers"""
        response_data = json.dumps(data).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Length', str(len(response_data)))
        self.end_headers()
        
        self.wfile.write(response_data)

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