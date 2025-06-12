#!/usr/bin/env python3
"""
RoluATM Flask Backend for Raspberry Pi
Handles transaction creation, World ID verification, and T-Flex coin dispenser control
"""

import os
import json
import time
import logging
import requests
import uuid
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import serial
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WORLD_APP_ID = os.getenv('VITE_WORLD_APP_ID')
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')
TFLEX_PORT = os.getenv('TFLEX_PORT', '/dev/ttyUSB0')
DEV_MODE = os.getenv('DEV_MODE', 'true').lower() == 'true'
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://mini-app.roluatm.com')
WORLD_API_URL = os.getenv('WORLD_API_URL', 'https://developer.worldcoin.org/api/v2')

# Transaction constants
COIN_VALUE = 0.25
TRANSACTION_FEE = 0.50
TRANSACTION_TIMEOUT_MINUTES = 10

class TFlexController:
    """T-Flex coin dispenser controller"""
    
    def __init__(self, port=None, mock=False):
        self.port = port or TFLEX_PORT
        self.mock = mock or DEV_MODE
        self.serial_conn = None
        
        if not self.mock:
            try:
                self.serial_conn = serial.Serial(
                    self.port, 
                    baudrate=9600, 
                    timeout=2
                )
                logger.info(f"T-Flex connected on {self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to T-Flex: {e}")
                self.mock = True
    
    def dispense_coins(self, num_quarters, transaction_id):
        """Dispense specified number of quarters"""
        if self.mock:
            logger.info(f"MOCK: Dispensing {num_quarters} quarters for transaction {transaction_id}")
            time.sleep(3)  # Simulate dispense time
            return {"success": True, "quarters_dispensed": num_quarters}
        
        try:
            # Send dispense command to T-Flex
            command = f"DISPENSE {num_quarters}\r\n"
            self.serial_conn.write(command.encode())
            
            # Wait for response
            response = self.serial_conn.readline().decode().strip()
            
            if "OK" in response:
                logger.info(f"Dispensed {num_quarters} quarters successfully")
                return {"success": True, "quarters_dispensed": num_quarters}
            else:
                logger.error(f"T-Flex error: {response}")
                return {"success": False, "error": response}
                
        except Exception as e:
            logger.error(f"Dispense error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self):
        """Get T-Flex status"""
        if self.mock:
            return {
                "coinDispenser": "ready",
                "network": "connected", 
                "security": "active"
            }
        
        try:
            self.serial_conn.write(b"STATUS\r\n")
            response = self.serial_conn.readline().decode().strip()
            # Parse T-Flex response and return standardized status
            return {
                "coinDispenser": "ready",
                "network": "connected",
                "security": "active",
                "raw_response": response
            }
        except Exception as e:
            return {
                "coinDispenser": "fault",
                "network": "disconnected",
                "security": "inactive",
                "error": str(e)
            }

# Initialize hardware
tflex = TFlexController()

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.db_url = DATABASE_URL
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def create_transaction(self, fiat_amount):
        """Create a new transaction"""
        transaction_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=TRANSACTION_TIMEOUT_MINUTES)
        mini_app_url = f"{MINI_APP_URL}?transaction_id={transaction_id}"
        
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO transactions 
                    (id, world_id, cryptocurrency, crypto_amount, fiat_amount, fiat_currency, 
                     exchange_rate, status, created_at, expires_at, mini_app_url, progress)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    transaction_id,
                    'pending',  # world_id - will be updated after payment
                    'WLD',      # cryptocurrency
                    0,          # crypto_amount - will be calculated during payment
                    fiat_amount,
                    'USD',      # fiat_currency
                    1,          # exchange_rate - will be updated during payment
                    'pending',  # status
                    datetime.now(timezone.utc),
                    expires_at,
                    mini_app_url,
                    0           # progress
                ))
                
                transaction = cur.fetchone()
            conn.commit()
            conn.close()
            return dict(transaction)
        except Exception as e:
            logger.error(f"Transaction creation error: {e}")
            conn.close()
            return None
    
    def get_transaction(self, transaction_id):
        """Get transaction by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
                transaction = cur.fetchone()
            conn.close()
            return dict(transaction) if transaction else None
        except Exception as e:
            logger.error(f"Transaction fetch error: {e}")
            conn.close()
            return None
    
    def update_transaction_status(self, transaction_id, status, **kwargs):
        """Update transaction status and additional fields"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            # Build dynamic update query
            update_fields = ["status = %s"]
            values = [status]
            
            for key, value in kwargs.items():
                update_fields.append(f"{key} = %s")
                values.append(value)
            
            values.append(transaction_id)
            
            with conn.cursor() as cur:
                query = f"UPDATE transactions SET {', '.join(update_fields)} WHERE id = %s"
                cur.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Transaction update error: {e}")
            conn.close()
            return False

db = DatabaseManager()

def verify_world_id_proof(proof_data):
    """Verify World ID proof with Worldcoin API"""
    if DEV_MODE:
        # Mock verification for development
        logger.info("MOCK: World ID verification passed")
        return {"success": True, "nullifier_hash": "mock_nullifier"}
    
    try:
        verify_url = f"{WORLD_API_URL}/verify/{WORLD_APP_ID}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {WORLD_CLIENT_SECRET}'
        }
        
        response = requests.post(verify_url, json=proof_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            logger.error(f"World ID verification failed: {response.text}")
            return {"success": False, "error": "Verification failed"}
            
    except Exception as e:
        logger.error(f"World ID API error: {e}")
        return {"success": False, "error": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "backend": "Python Flask",
        "hardware": tflex.get_status(),
        "dev_mode": DEV_MODE
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status for kiosk"""
    return jsonify(tflex.get_status())

@app.route('/api/transaction/create', methods=['POST'])
def create_transaction():
    """Create a new transaction and return QR code URL"""
    try:
        data = request.get_json()
        
        # Validate request
        if 'amount' not in data:
            return jsonify({"error": "Missing field: amount"}), 400
        
        amount = float(data['amount'])
        
        # Validate amount
        if amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        # Create transaction in database
        transaction = db.create_transaction(amount)
        if not transaction:
            return jsonify({"error": "Failed to create transaction"}), 500
        
        # Add calculated fields for frontend
        quarters = int(amount / COIN_VALUE)
        total = amount + TRANSACTION_FEE
        
        response_data = dict(transaction)
        response_data.update({
            'quarters': quarters,
            'total': total,
            'amount': amount  # Ensure amount is in response
        })
        
        logger.info(f"Created transaction {transaction['id']} for ${amount}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Transaction creation error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/transaction/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get transaction details"""
    try:
        transaction = db.get_transaction(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        
        # Check if transaction expired
        if transaction['expires_at'] < datetime.now(timezone.utc):
            if transaction['status'] == 'pending':
                db.update_transaction_status(transaction_id, 'expired')
                transaction['status'] = 'expired'
        
        return jsonify(transaction)
        
    except Exception as e:
        logger.error(f"Transaction fetch error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/transaction/<transaction_id>/status', methods=['GET'])
def get_transaction_status(transaction_id):
    """Get transaction status for polling"""
    try:
        transaction = db.get_transaction(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        
        # Check if transaction expired
        if transaction['expires_at'] < datetime.now(timezone.utc) and transaction['status'] == 'pending':
            db.update_transaction_status(transaction_id, 'expired')
            transaction['status'] = 'expired'
        
        return jsonify({
            "status": transaction['status'],
            "progress": transaction.get('progress', 0)
        })
        
    except Exception as e:
        logger.error(f"Status fetch error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/transaction/pay', methods=['POST'])
def process_payment():
    """Process payment from mini app"""
    try:
        data = request.get_json()
        
        # Validate request
        required_fields = ['transaction_id', 'proof', 'nullifier_hash', 'merkle_root']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        transaction_id = data['transaction_id']
        
        # Get transaction
        transaction = db.get_transaction(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        
        # Check transaction status
        if transaction['status'] != 'pending':
            return jsonify({"error": "Transaction not available for payment"}), 400
        
        # Check if expired
        if transaction['expires_at'] < datetime.now(timezone.utc):
            db.update_transaction_status(transaction_id, 'expired')
            return jsonify({"error": "Transaction expired"}), 400
        
        # Verify World ID proof
        proof_data = {
            'proof': data['proof'],
            'nullifier_hash': data['nullifier_hash'],
            'merkle_root': data['merkle_root']
        }
        
        verification = verify_world_id_proof(proof_data)
        if not verification['success']:
            return jsonify({"error": "World ID verification failed"}), 401
        
        # Update transaction to paid
        db.update_transaction_status(
            transaction_id, 
            'paid',
            nullifier_hash=data['nullifier_hash'],
            paid_at=datetime.now(timezone.utc)
        )
        
        # Start dispensing process (in background)
        logger.info(f"Starting coin dispensing for transaction {transaction_id}")
        
        # Calculate quarters to dispense from fiat amount
        quarters_to_dispense = int(transaction['fiat_amount'] / COIN_VALUE)
        
        # Update status to dispensing
        db.update_transaction_status(transaction_id, 'dispensing', progress=0)
        
        # Dispense coins
        dispense_result = tflex.dispense_coins(quarters_to_dispense, transaction_id)
        
        if dispense_result['success']:
            # Mark as complete
            db.update_transaction_status(
                transaction_id, 
                'complete',
                progress=100,
                dispense_completed_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"Transaction {transaction_id} completed successfully")
            
            return jsonify({
                "success": True,
                "message": "Payment processed and coins dispensed",
                "quarters_dispensed": dispense_result['quarters_dispensed']
            })
        else:
            # Mark as failed
            db.update_transaction_status(
                transaction_id, 
                'failed',
                error_message=dispense_result.get('error', 'Dispenser error')
            )
            
            return jsonify({"error": "Coin dispensing failed"}), 500
        
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting RoluATM backend on {host}:{port}")
    logger.info(f"Dev mode: {DEV_MODE}")
    logger.info(f"T-Flex port: {TFLEX_PORT}")
    logger.info(f"Mini app URL: {MINI_APP_URL}")
    
    app.run(host=host, port=port, debug=DEV_MODE) 