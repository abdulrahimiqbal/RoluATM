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

def handler(request, context):
    """Main Vercel handler function"""
    try:
        # Get request method and path
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        print(f"📝 {method} {path}")
        
        # CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Health check
        if path in ['/health', '/api/health', '/api/status', '/']:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'environment': 'vercel',
                    'dev_mode': DEV_MODE,
                    'message': 'RoluATM Backend is running on Vercel!'
                })
            }
        
        # Create transaction
        if path == '/api/transaction/create' and method == 'POST':
            try:
                body = json.loads(request.get('body', '{}'))
                amount = float(body.get('amount', 5.0))
                
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
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(transaction)
                }
                
            except Exception as e:
                print(f"❌ Error creating transaction: {e}")
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid request data'})
                }
        
        # Get transaction
        if path.startswith('/api/transaction/') and method == 'GET' and not path.endswith('/pay'):
            transaction_id = path.split('/')[-1]
            
            if transaction_id in transactions:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(transactions[transaction_id])
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Transaction not found'})
                }
        
        # Pay transaction (mock)
        if path.startswith('/api/transaction/') and path.endswith('/pay') and method == 'POST':
            transaction_id = path.split('/')[-2]
            
            if transaction_id in transactions:
                # Mock World ID verification and payment
                transactions[transaction_id]['status'] = 'completed'
                transactions[transaction_id]['completed_at'] = datetime.now(timezone.utc).isoformat()
                
                print(f"🔒 Mock World ID verification for {transaction_id}")
                print(f"🪙 Mock dispensing {transactions[transaction_id]['quarters']} quarters...")
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'message': 'Payment completed',
                        'transaction': transactions[transaction_id]
                    })
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Transaction not found'})
                }
        
        # Default 404
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Internal server error'})
        } 