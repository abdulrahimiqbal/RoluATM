#!/usr/bin/env python3
"""
RoluATM Raspberry Pi Backend Server
Handles T-Flex coin dispenser and database operations for Pi deployment
Uses PostgreSQL database and proper error handling
"""

import os
import sys
import json
import uuid
import time
import logging
import psycopg2
import psycopg2.extras
from decimal import Decimal
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configuration
PORT = int(os.environ.get('PORT', 8000))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://rolu:rolu123@localhost:5432/roluatm')
WORLD_CLIENT_SECRET = os.environ.get('WORLD_CLIENT_SECRET', 'sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19')
MINI_APP_URL = os.environ.get('MINI_APP_URL', 'https://mini-app-azure.vercel.app')
TFLEX_PORT = os.environ.get('TFLEX_PORT', '/dev/ttyUSB0')
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'

# T-Flex hardware integration
TFLEX_AVAILABLE = False
try:
    import serial
    if os.path.exists(TFLEX_PORT):
        TFLEX_AVAILABLE = True
        print(f"✅ T-Flex found on {TFLEX_PORT}")
    else:
        print(f"⚠️  T-Flex not found on {TFLEX_PORT}, using mock mode")
except ImportError:
    print("⚠️  PySerial not available, using mock mode")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🎰 RoluATM Pi Backend Starting...")
print(f"✅ Server: http://localhost:{PORT}")
print(f"✅ Mini App: {MINI_APP_URL}")
print(f"✅ T-Flex: {'Hardware Mode' if TFLEX_AVAILABLE else 'Mock Mode'}")

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat() + 'Z'
        return super().default(obj)

class TFlexDispenser:
    """T-Flex coin dispenser controller"""
    
    def __init__(self, port=TFLEX_PORT, mock_mode=not TFLEX_AVAILABLE):
        self.port = port
        self.mock_mode = mock_mode
        self.connection = None
        
        if not mock_mode:
            try:
                self.connection = serial.Serial(port, 9600, timeout=1)
                logger.info(f"T-Flex connected on {port}")
            except Exception as e:
                logger.error(f"Failed to connect to T-Flex: {e}")
                self.mock_mode = True
    
    def dispense_quarters(self, count):
        """Dispense specified number of quarters"""
        if self.mock_mode:
            print(f"🪙 Mock dispensing {count} quarters...")
            time.sleep(1)  # Simulate dispensing time
            return True
        
        try:
            # T-Flex command to dispense quarters
            # This is a simplified example - actual commands depend on your T-Flex model
            command = f"DISPENSE {count}\r\n"
            self.connection.write(command.encode())
            
            # Wait for acknowledgment
            response = self.connection.readline().decode().strip()
            if "OK" in response:
                logger.info(f"Dispensed {count} quarters successfully")
                return True
            else:
                logger.error(f"T-Flex error: {response}")
                return False
                
        except Exception as e:
            logger.error(f"T-Flex dispensing error: {e}")
            return False
    
    def get_status(self):
        """Get T-Flex status"""
        if self.mock_mode:
            return {"status": "mock", "quarters_available": 1000}
        
        try:
            self.connection.write(b"STATUS\r\n")
            response = self.connection.readline().decode().strip()
            # Parse response based on your T-Flex model
            return {"status": "connected", "response": response}
        except Exception as e:
            logger.error(f"T-Flex status error: {e}")
            return {"status": "error", "error": str(e)}

class DatabaseManager:
    """PostgreSQL database manager"""
    
    def __init__(self, database_url=DATABASE_URL):
        self.database_url = database_url
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def create_transaction(self, fiat_amount):
        """Create a new transaction"""
        try:
            transaction_id = str(uuid.uuid4())
            mini_app_url = f"{MINI_APP_URL}?transaction_id={transaction_id}"
            expires_at = datetime.utcnow() + timedelta(minutes=15)
            
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO transactions (
                        id, world_id, cryptocurrency, crypto_amount, 
                        fiat_amount, fiat_currency, exchange_rate, 
                        status, created_at, expires_at, mini_app_url, progress
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    transaction_id,
                    '',  # world_id (empty string instead of NULL)
                    'USD',  # cryptocurrency 
                    0.0,  # crypto_amount 
                    fiat_amount,
                    'USD',
                    1.0,  # exchange_rate
                    'pending',
                    datetime.utcnow(),
                    expires_at,
                    mini_app_url,
                    0  # progress
                ))
                
                row = cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                transaction = dict(zip(columns, row))
                
                # Calculate quarters for display (4 quarters per dollar)
                quarters = int(fiat_amount * 4)
                transaction['quarters'] = quarters
                
                conn.commit()
                logger.info(f"✅ Created transaction {transaction_id} for ${fiat_amount} ({quarters} quarters)")
                return transaction
                
        except Exception as e:
            logger.error(f"Database error creating transaction: {e}")
            raise
    
    def get_transaction(self, transaction_id):
        """Get transaction by ID"""
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
                row = cur.fetchone()
                
                if not row:
                    return None
                
                columns = [desc[0] for desc in cur.description]
                transaction = dict(zip(columns, row))
                
                return transaction
        except Exception as e:
            logger.error(f"Database error getting transaction: {e}")
            raise
    
    def update_transaction_status(self, transaction_id, status, nullifier_hash=None):
        """Update transaction status"""
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                
                updates = ["status = %s", "progress = %s"]
                params = [status, 100 if status == 'completed' else 50]
                
                if nullifier_hash:
                    updates.append("nullifier_hash = %s")
                    params.append(nullifier_hash)
                
                if status == 'completed':
                    updates.append("paid_at = %s")
                    params.append(datetime.utcnow())
                
                params.append(transaction_id)
                
                query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)
                conn.commit()
                
                logger.info(f"Updated transaction {transaction_id} status to {status}")
                return True
        except Exception as e:
            logger.error(f"Database error updating transaction: {e}")
            raise

# Initialize components
tflex = TFlexDispenser()
db = DatabaseManager()

class RoluATMHandler(BaseHTTPRequestHandler):
    """HTTP request handler for RoluATM Pi backend"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/health':
                self.send_json_response({
                    'status': 'healthy',
                    'hardware': {
                        'tflex': 'hardware' if TFLEX_AVAILABLE else 'mock'
                    },
                    'database': 'connected'
                })
            
            elif path == '/api/status':
                # Return hardware status for kiosk UI
                tflex_status = tflex.get_status()
                self.send_json_response({
                    'coinDispenser': 'ready' if tflex_status.get('status') != 'error' else 'fault',
                    'network': 'connected',
                    'security': 'active'
                })
            
            elif path.startswith('/api/transaction/'):
                transaction_id = path.split('/')[-1]
                transaction = db.get_transaction(transaction_id)
                
                if transaction:
                    self.send_json_response(transaction)
                else:
                    self.send_error_response(404, 'Transaction not found')
            
            else:
                self.send_error_response(404, 'Not found')
                
        except Exception as e:
            logger.error(f"GET error: {e}")
            self.send_error_response(500, str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
            else:
                data = {}
            
            if path == '/api/transaction/create':
                amount = data.get('amount')
                if not amount or amount <= 0:
                    self.send_error_response(400, 'Invalid amount')
                    return
                
                transaction = db.create_transaction(amount)
                self.send_json_response(transaction)
            
            elif path == '/api/transaction/pay':
                transaction_id = data.get('transaction_id')
                nullifier_hash = data.get('nullifier_hash', 'mock_hash')
                
                if not transaction_id:
                    self.send_error_response(400, 'Missing transaction_id')
                    return
                
                # Get transaction
                transaction = db.get_transaction(transaction_id)
                if not transaction:
                    self.send_error_response(404, 'Transaction not found')
                    return
                
                if transaction['status'] != 'pending':
                    self.send_error_response(400, 'Transaction already processed')
                    return
                
                # Mock World ID verification in dev mode
                if DEV_MODE:
                    print(f"🔒 Mock World ID verification for {transaction_id}")
                
                # Dispense quarters
                quarters_to_dispense = int(transaction['fiat_amount'] * 4)
                if tflex.dispense_quarters(quarters_to_dispense):
                    # Update transaction as completed
                    db.update_transaction_status(transaction_id, 'completed', nullifier_hash)
                    
                    # Get updated transaction
                    updated_transaction = db.get_transaction(transaction_id)
                    self.send_json_response(updated_transaction)
                else:
                    # Update as failed
                    db.update_transaction_status(transaction_id, 'failed')
                    self.send_error_response(500, 'Dispensing failed')
            
            else:
                self.send_error_response(404, 'Not found')
                
        except json.JSONDecodeError:
            self.send_error_response(400, 'Invalid JSON')
        except Exception as e:
            logger.error(f"POST error: {e}")
            self.send_error_response(500, str(e))
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, cls=DecimalEncoder, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_json_response({'error': message}, status_code)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(format % args)

if __name__ == '__main__':
    try:
        # Test database connection
        db.get_connection().close()
        logger.info("Database connection successful")
        
        # Start server
        server = HTTPServer(('0.0.0.0', PORT), RoluATMHandler)
        logger.info(f"Server starting on http://0.0.0.0:{PORT}")
        server.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1) 