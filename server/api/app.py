#!/usr/bin/env python3
"""
RoluATM Backend for Vercel Deployment
Full-featured backend with database support, World ID integration, and T-Flex simulation
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error

# Database import
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("⚠️ psycopg2 not available, using in-memory storage")

# Environment variables
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://mini-app-azure.vercel.app')

# Fallback in-memory storage
transactions = {}

class Database:
    def __init__(self):
        self.conn = None
        if HAS_PSYCOPG2 and DATABASE_URL:
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                self.conn.autocommit = True
                self.create_tables()
                print("✅ Database connected")
            except Exception as e:
                print(f"⚠️ Database connection failed: {e}")
                self.conn = None
        else:
            print("⚠️ Using in-memory storage")

    def create_tables(self):
        if not self.conn:
            return
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id UUID PRIMARY KEY,
                    fiat_amount DECIMAL(10,2) NOT NULL,
                    quarters INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    mini_app_url TEXT,
                    progress INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    paid_at TIMESTAMP WITH TIME ZONE,
                    nullifier_hash TEXT,
                    user_id TEXT
                )
            """)

    def create_transaction(self, transaction_id, fiat_amount, quarters, mini_app_url, expires_at):
        transaction_data = {
            'id': transaction_id,
            'fiat_amount': fiat_amount,
            'quarters': quarters,
            'status': 'pending',
            'mini_app_url': mini_app_url,
            'progress': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        if self.conn:
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO transactions (id, fiat_amount, quarters, status, mini_app_url, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (transaction_id, fiat_amount, quarters, 'pending', mini_app_url, expires_at))
                return transaction_data
            except Exception as e:
                print(f"Database error: {e}")
                
        # Fallback to in-memory
        transactions[transaction_id] = transaction_data
        return transaction_data

    def get_transaction(self, transaction_id):
        if self.conn:
            try:
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
                    row = cursor.fetchone()
                    if row:
                        transaction = dict(row)
                        # Convert datetime objects to ISO strings
                        for field in ['created_at', 'expires_at', 'paid_at']:
                            if transaction.get(field):
                                transaction[field] = transaction[field].isoformat()
                        return transaction
            except Exception as e:
                print(f"Database error: {e}")
        
        # Fallback to in-memory
        return transactions.get(transaction_id)

    def update_transaction_status(self, transaction_id, status, progress=None, nullifier_hash=None):
        if self.conn:
            try:
                with self.conn.cursor() as cursor:
                    if status == 'complete':
                        cursor.execute("""
                            UPDATE transactions 
                            SET status = %s, progress = %s, paid_at = NOW(), nullifier_hash = %s
                            WHERE id = %s
                        """, (status, progress or 100, nullifier_hash, transaction_id))
                    else:
                        cursor.execute("""
                            UPDATE transactions 
                            SET status = %s, progress = %s, nullifier_hash = %s
                            WHERE id = %s
                        """, (status, progress or 0, nullifier_hash, transaction_id))
                return True
            except Exception as e:
                print(f"Database error: {e}")
        
        # Fallback to in-memory
        if transaction_id in transactions:
            transactions[transaction_id]['status'] = status
            if progress is not None:
                transactions[transaction_id]['progress'] = progress
            if nullifier_hash:
                transactions[transaction_id]['nullifier_hash'] = nullifier_hash
            if status == 'complete':
                transactions[transaction_id]['paid_at'] = datetime.now(timezone.utc).isoformat()
        return True

# Initialize database
db = Database()

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

def verify_world_id(proof, action_id="pay-quarters"):
    """Verify World ID proof"""
    if not WORLD_CLIENT_SECRET:
        print("🔒 Mock World ID verification (no secret configured)")
        return True, None
    
    try:
        verify_url = "https://developer.worldcoin.org/api/v1/verify/app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db"
        
        data = {
            "nullifier_hash": proof.get("nullifier_hash"),
            "merkle_root": proof.get("merkle_root"),
            "proof": proof.get("proof"),
            "verification_level": proof.get("verification_level", "orb"),
            "action": action_id
        }
        
        req = urllib.request.Request(
            verify_url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {WORLD_CLIENT_SECRET}'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get("success"):
            print(f"✅ World ID verification successful")
            return True, result.get("nullifier_hash")
        else:
            print(f"❌ World ID verification failed: {result}")
            return False, None
            
    except Exception as e:
        print(f"❌ World ID verification error: {e}")
        return False, None

def dispense_quarters_mock(num_quarters, transaction_id):
    """Mock quarter dispensing"""
    print(f"🪙 Mock dispensing {num_quarters} quarters for {transaction_id}...")
    time.sleep(2)  # Simulate dispense time
    return True

def handler(event, context=None):
    """Main Vercel handler"""
    # Handle both API Gateway and direct invocation formats
    if isinstance(event, dict) and 'httpMethod' in event:
        # API Gateway format
        method = event['httpMethod']
        path = event.get('path', '/')
        query_string = event.get('queryStringParameters') or {}
        body = event.get('body', '')
        headers = event.get('headers', {})
    else:
        # Direct invocation or other format
        method = os.getenv('REQUEST_METHOD', 'GET')
        path = os.getenv('REQUEST_PATH_INFO', os.getenv('VERCEL_URL_PATH', '/'))
        query_string = os.getenv('QUERY_STRING', '')
        body = ''
        headers = {}
    
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
                'database': 'connected' if db.conn else 'in-memory'
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
                data = {'fiat_amount': 5.0}  # Default
            
            fiat_amount = float(data.get('fiat_amount', data.get('amount', 5.0)))
            transaction_id = str(uuid.uuid4())
            quarters = int(fiat_amount / 0.25)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            
            # Create mini app URL - always use vercel backend for deployed version
            mini_app_url = f"{MINI_APP_URL}?transaction_id={transaction_id}"
            
            # Create transaction
            transaction = db.create_transaction(transaction_id, fiat_amount, quarters, mini_app_url, expires_at)
            
            print(f"✅ Created transaction {transaction_id} for ${fiat_amount} ({quarters} quarters)")
            
            return create_response(200, transaction)
            
        except Exception as e:
            print(f"❌ Transaction creation error: {e}")
            return create_response(500, {'error': str(e)})
    
    # Get transaction
    if path.startswith('/api/transaction/') and method == 'GET':
        try:
            transaction_id = path.split('/')[-1]
            
            transaction = db.get_transaction(transaction_id)
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
            world_id_proof = data.get('proof', {})
            
            if not transaction_id:
                return create_response(400, {'error': 'Transaction ID required'})
            
            transaction = db.get_transaction(transaction_id)
            if not transaction:
                return create_response(404, {'error': 'Transaction not found'})
            
            # Check if expired
            expires_at = datetime.fromisoformat(transaction['expires_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                db.update_transaction_status(transaction_id, 'expired')
                return create_response(400, {'error': 'Transaction expired'})
            
            # Check if already processed
            if transaction['status'] != 'pending':
                return create_response(400, {'error': f'Transaction already {transaction["status"]}'})
            
            # Verify World ID
            world_id_valid, nullifier_hash = verify_world_id(world_id_proof)
            if not world_id_valid:
                db.update_transaction_status(transaction_id, 'failed')
                return create_response(400, {'error': 'World ID verification failed'})
            
            # Update status to dispensing
            db.update_transaction_status(transaction_id, 'dispensing', 50, nullifier_hash)
            
            # Mock dispense quarters
            if dispense_quarters_mock(transaction['quarters'], transaction_id):
                db.update_transaction_status(transaction_id, 'complete', 100)
                print(f"✅ Transaction {transaction_id} completed successfully")
                
                # Get updated transaction
                updated_transaction = db.get_transaction(transaction_id)
                return create_response(200, updated_transaction)
            else:
                db.update_transaction_status(transaction_id, 'failed', 0)
                print(f"❌ Transaction {transaction_id} failed")
                return create_response(500, {'error': 'Dispensing failed'})
            
        except Exception as e:
            print(f"❌ Payment processing error: {e}")
            return create_response(500, {'error': str(e)})
    
    # Default response
    return create_response(404, {'error': 'Not found', 'path': path, 'method': method})

# Vercel entry point
def app(environ, start_response):
    """WSGI entry point for Vercel"""
    # Set environment variables from WSGI environ
    os.environ['REQUEST_METHOD'] = environ['REQUEST_METHOD']
    os.environ['REQUEST_PATH_INFO'] = environ.get('PATH_INFO', '/')
    os.environ['QUERY_STRING'] = environ.get('QUERY_STRING', '')
    
    if 'CONTENT_LENGTH' in environ and environ['CONTENT_LENGTH']:
        os.environ['CONTENT_LENGTH'] = environ['CONTENT_LENGTH']
    
    response = handler(None)
    
    status = f"{response['statusCode']} OK"
    headers = [(k, v) for k, v in response['headers'].items()]
    
    start_response(status, headers)
    return [response['body'].encode()]

# For local testing
if __name__ == '__main__':
    print("🎰 RoluATM Backend for Vercel")
    print("============================")
    print("Running locally on port 8000...")
    
    import http.server
    import socketserver
    
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            os.environ['REQUEST_METHOD'] = 'GET'
            os.environ['REQUEST_PATH_INFO'] = self.path.split('?')[0]
            os.environ['QUERY_STRING'] = self.path.split('?')[1] if '?' in self.path else ''
            
            response = handler(None)
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
        
        def do_POST(self):
            os.environ['REQUEST_METHOD'] = 'POST'
            os.environ['REQUEST_PATH_INFO'] = self.path.split('?')[0]
            os.environ['QUERY_STRING'] = self.path.split('?')[1] if '?' in self.path else ''
            
            content_length = int(self.headers['Content-Length'])
            os.environ['CONTENT_LENGTH'] = str(content_length)
            
            # Read body
            import sys
            import io
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(self.rfile.read(content_length).decode('utf-8'))
            
            response = handler(None)
            
            sys.stdin = old_stdin
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
        
        def do_OPTIONS(self):
            os.environ['REQUEST_METHOD'] = 'OPTIONS'
            os.environ['REQUEST_PATH_INFO'] = self.path.split('?')[0]
            
            response = handler(None)
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
    
    with socketserver.TCPServer(("", 8000), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n Server stopped") 