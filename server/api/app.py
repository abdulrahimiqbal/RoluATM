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

# Environment variables
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://mini-app-azure.vercel.app')

# In-memory storage for now (will add database later)
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
        'body': json.dumps(data, default=str)
    }

def handler(event, context=None):
    """Main Vercel handler"""
    try:
        # Parse the event
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        body = event.get('body', '')
        
        print(f"📝 {method} {path}")
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # Health check
        if path in ['/health', '/api/status']:
            return create_response(200, {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'hardware': {
                    'coinDispenser': 'ready',
                    'network': 'connected', 
                    'security': 'active',
                    'database': 'in-memory'
                },
                'dev_mode': DEV_MODE
            })
        
        # Create transaction
        if path == '/api/transaction/create' and method == 'POST':
            try:
                # Parse request body
                if body:
                    data = json.loads(body) if isinstance(body, str) else body
                else:
                    data = {'amount': 5.0}  # Default
                
                fiat_amount = float(data.get('fiat_amount', data.get('amount', 5.0)))
                transaction_id = str(uuid.uuid4())
                quarters = int(fiat_amount / 0.25)
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
                
                # Create mini app URL
                mini_app_url = f"{MINI_APP_URL}?transaction_id={transaction_id}"
                
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
                
                return create_response(200, transaction)
                
            except Exception as e:
                print(f"❌ Transaction creation error: {e}")
                return create_response(500, {'error': str(e)})
        
        # Get transaction
        if path.startswith('/api/transaction/') and method == 'GET':
            try:
                transaction_id = path.split('/')[-1]
                
                transaction = transactions.get(transaction_id)
                if transaction:
                    return create_response(200, transaction)
                else:
                    return create_response(404, {'error': 'Transaction not found'})
            except Exception as e:
                print(f"❌ Transaction lookup error: {e}")
                return create_response(500, {'error': str(e)})
        
        # Process payment
        if path == '/api/transaction/pay' and method == 'POST':
            try:
                # Parse request body
                if body:
                    data = json.loads(body) if isinstance(body, str) else body
                else:
                    return create_response(400, {'error': 'No request body'})
                
                transaction_id = data.get('transaction_id')
                
                if not transaction_id:
                    return create_response(400, {'error': 'Transaction ID required'})
                
                transaction = transactions.get(transaction_id)
                if not transaction:
                    return create_response(404, {'error': 'Transaction not found'})
                
                # Check if expired
                expires_at = datetime.fromisoformat(transaction['expires_at'].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expires_at:
                    transaction['status'] = 'expired'
                    return create_response(400, {'error': 'Transaction expired'})
                
                # Check if already processed
                if transaction['status'] != 'pending':
                    return create_response(400, {'error': f'Transaction already {transaction["status"]}'})
                
                # Mock World ID verification (always pass for now)
                print(f"🔒 Mock World ID verification for {transaction_id}")
                
                # Update status to dispensing
                transaction['status'] = 'dispensing'
                transaction['progress'] = 50
                
                # Mock dispense quarters
                print(f"🪙 Mock dispensing {transaction['quarters']} quarters...")
                time.sleep(1)  # Simulate dispense time
                
                # Complete transaction
                transaction['status'] = 'complete'
                transaction['progress'] = 100
                transaction['paid_at'] = datetime.now(timezone.utc).isoformat()
                
                print(f"✅ Transaction {transaction_id} completed successfully")
                
                return create_response(200, transaction)
                
            except Exception as e:
                print(f"❌ Payment processing error: {e}")
                return create_response(500, {'error': str(e)})
        
        # Default response
        return create_response(404, {'error': 'Not found', 'path': path, 'method': method})
        
    except Exception as e:
        print(f"❌ Handler error: {e}")
        return create_response(500, {'error': f'Internal server error: {str(e)}'})

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