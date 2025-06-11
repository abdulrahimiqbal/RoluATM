#!/usr/bin/env python3
"""
RoluATM Crypto-to-Cash Kiosk Backend
Flask application for hardware control and API integration
"""

import os
import sys
import json
import logging
import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
import psycopg
from psycopg.rows import dict_row
import jwt
from marshmallow import ValidationError
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv

from driver_tflex import TFlex
from settings import Settings

# Import configuration from environment
# Load from .env.local first, then fallback to .env
load_dotenv('.env.local')
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*" if os.getenv("DEV_MODE", "false").lower() == "true" else ["https://localhost:5000"])

# Initialize settings and hardware
settings = Settings()
tflex = TFlex(port=settings.TFLEX_PORT)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
WORLD_CLIENT_SECRET = os.getenv('WORLD_CLIENT_SECRET')
WORLD_APP_ID = os.getenv('VITE_WORLD_APP_ID')
KIOSK_LOCATION = os.getenv('KIOSK_LOCATION', 'Development')

# Database connection
def get_db_connection():
    """Get database connection using psycopg3"""
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

@dataclass
class WithdrawRequest:
    proof: str
    nullifier_hash: str
    merkle_root: str
    amount_usd: float

class WorldIDVerifier:
    """Handle World ID proof verification"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def verify_proof(self, proof: str, merkle_root: str, nullifier_hash: str, action_id: str) -> bool:
        """Verify World ID proof against Worldcoin API"""
        try:
            payload = {
                "proof": proof,
                "merkle_root": merkle_root,
                "nullifier_hash": nullifier_hash,
                "action_id": action_id,
                "signal": "withdraw"
            }
            
            response = requests.post(
                f"{self.api_url}/verify",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            else:
                logger.error(f"World ID verification failed: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"World ID verification error: {e}")
            return False

class WalletManager:
    """Handle wallet operations (lock/unlock/settle)"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def lock_tokens(self, address: str, amount_usd: float) -> bool:
        """Lock user tokens for withdrawal"""
        try:
            payload = {
                "address": address,
                "amount_usd": amount_usd,
                "action": "lock"
            }
            
            response = requests.post(
                f"{self.api_url}/lock",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Token lock error: {e}")
            return False
    
    def unlock_tokens(self, address: str, amount_usd: float) -> bool:
        """Unlock user tokens (rollback)"""
        try:
            payload = {
                "address": address,
                "amount_usd": amount_usd,
                "action": "unlock"
            }
            
            response = requests.post(
                f"{self.api_url}/unlock",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Token unlock error: {e}")
            return False
    
    def settle_transaction(self, address: str, amount_usd: float, tx_id: str) -> bool:
        """Settle the transaction (finalize)"""
        try:
            payload = {
                "address": address,
                "amount_usd": amount_usd,
                "transaction_id": tx_id,
                "action": "settle"
            }
            
            response = requests.post(
                f"{self.api_url}/settle",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Transaction settle error: {e}")
            return False

class PriceProvider:
    """Get current crypto prices"""
    
    def __init__(self, fx_url: str):
        self.fx_url = fx_url
    
    def get_btc_price(self) -> Optional[float]:
        """Get current BTC price in USD"""
        try:
            response = requests.get(self.fx_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Kraken API format
                if "result" in data and "WBTCUSD" in data["result"]:
                    price_data = data["result"]["WBTCUSD"]
                    return float(price_data["c"][0])  # Current price
            return None
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            return None

# Initialize services
world_id_verifier = WorldIDVerifier(settings.WORLD_API_URL)
wallet_manager = WalletManager(settings.WALLET_API_URL)
price_provider = PriceProvider(settings.FX_URL)

@app.route("/api/balance")
def get_balance():
    """Get user balance in USD and crypto"""
    try:
        address = request.args.get("address")
        if not address:
            return jsonify({"error": "Address parameter required"}), 400
        
        # Get crypto balance from wallet API
        response = requests.get(
            f"{settings.WALLET_API_URL}/balance/{address}",
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch balance"}), 500
        
        balance_data = response.json()
        crypto_amount = balance_data.get("balance", 0)
        
        # Get current BTC price
        btc_price = price_provider.get_btc_price()
        if btc_price is None:
            return jsonify({"error": "Failed to get current price"}), 500
        
        usd_value = crypto_amount * btc_price
        
        return jsonify({
            "usd": round(usd_value, 2),
            "crypto": crypto_amount,
            "symbol": "BTC",
            "price_per_unit": btc_price
        })
        
    except Exception as e:
        logger.error(f"Balance fetch error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/status")
def get_hardware_status():
    """Get hardware and system status"""
    try:
        # Check coin dispenser status
        dispenser_status = tflex.status()
        
        if dispenser_status.get("fault", False):
            coin_status = "fault"
        elif dispenser_status.get("low_coin", False):
            coin_status = "low"
        else:
            coin_status = "ready"
        
        # Check network connectivity
        try:
            requests.get("https://api.worldcoin.org", timeout=5)
            network_status = "connected"
        except:
            network_status = "disconnected"
        
        return jsonify({
            "coinDispenser": coin_status,
            "network": network_status,
            "security": "active",  # Always active in this implementation
            "lastUpdate": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            "coinDispenser": "fault",
            "network": "disconnected", 
            "security": "inactive",
            "error": str(e)
        }), 500

@app.route("/api/withdraw", methods=["POST"])
def process_withdrawal():
    """Process crypto-to-cash withdrawal"""
    try:
        # Input validation - check content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Comprehensive field validation
        required_fields = ["proof", "nullifierHash", "merkleRoot", "amountUsd"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
            if not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                return jsonify({"error": f"Field {field} cannot be empty"}), 400
        
        # Type validation and sanitization
        try:
            amount_usd = float(data["amountUsd"])
        except (ValueError, TypeError):
            return jsonify({"error": "amountUsd must be a valid number"}), 400
            
        # String field validation
        proof = str(data["proof"]).strip()
        nullifier_hash = str(data["nullifierHash"]).strip()
        merkle_root = str(data["merkleRoot"]).strip()
        
        if len(proof) < 10 or len(nullifier_hash) < 10 or len(merkle_root) < 10:
            return jsonify({"error": "Invalid proof data format"}), 400
        
        withdraw_req = WithdrawRequest(
            proof=proof,
            nullifier_hash=nullifier_hash,
            merkle_root=merkle_root,
            amount_usd=amount_usd
        )
        
        # Amount validation with detailed error messages
        if withdraw_req.amount_usd <= 0:
            return jsonify({"error": "Withdrawal amount must be greater than $0"}), 400
        if withdraw_req.amount_usd > 500:
            return jsonify({"error": "Withdrawal amount cannot exceed $500"}), 400
        if withdraw_req.amount_usd < 1:
            return jsonify({"error": "Minimum withdrawal amount is $1.00"}), 400
        
        # Check for duplicate nullifier hash (prevent replay attacks)
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM transactions WHERE nullifier_hash = %s",
                    (withdraw_req.nullifier_hash,)
                )
                if cur.fetchone():
                    return jsonify({"error": "Transaction already processed"}), 400
            conn.close()
        except Exception as e:
            logger.error(f"Database validation error: {e}")
            return jsonify({"error": "Validation failed"}), 500
        
        # Generate transaction ID
        tx_id = f"WC-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"
        
        # Step 1: Verify World ID proof
        action_id = f"atm-demo-{int(datetime.now().timestamp())}"
        if not world_id_verifier.verify_proof(
            withdraw_req.proof,
            withdraw_req.merkle_root,
            withdraw_req.nullifier_hash,
            action_id
        ):
            return jsonify({"error": "World ID verification failed"}), 400
        
        # Step 2: Lock user tokens
        user_address = request.args.get("address", "mock_address")  # Get from session in production
        if not wallet_manager.lock_tokens(user_address, withdraw_req.amount_usd):
            return jsonify({"error": "Failed to lock tokens"}), 500
        
        # Step 3: Calculate coins and dispense
        coins_to_dispense = int(withdraw_req.amount_usd / 0.25)  # Convert to quarters
        if withdraw_req.amount_usd % 0.25 > 0:
            coins_to_dispense += 1  # Round up to nearest quarter
        
        try:
            tflex.dispense(coins_to_dispense)
        except RuntimeError as e:
            # Hardware failure - unlock tokens and return error
            wallet_manager.unlock_tokens(user_address, withdraw_req.amount_usd)
            logger.error(f"Coin dispenser error: {e}")
            return jsonify({"error": "Hardware failure during dispense"}), 500
        
        # Step 4: Settle transaction
        if not wallet_manager.settle_transaction(user_address, withdraw_req.amount_usd, tx_id):
            logger.error("Failed to settle transaction - manual intervention required")
            # Transaction already completed physically, log for manual review
        
        return jsonify({
            "success": True,
            "transactionId": tx_id,
            "coinsDispensed": coins_to_dispense,
            "actualAmount": coins_to_dispense * 0.25,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Withdrawal error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            # Return hardware status as JSON for Node.js integration
            try:
                status = tflex.status()
                print(json.dumps({
                    "coinDispenser": "fault" if status.get("fault") else ("low" if status.get("low_coin") else "ready"),
                    "network": "connected",
                    "security": "active"
                }))
            except Exception as e:
                print(json.dumps({
                    "coinDispenser": "fault",
                    "network": "disconnected", 
                    "security": "inactive",
                    "error": str(e)
                }))
        
        elif command == "withdraw":
            # Process withdrawal from command line
            try:
                withdraw_data = json.loads(sys.argv[2])
                # Process withdrawal logic here
                coins = int(withdraw_data["amountUsd"] / 0.25)
                if withdraw_data["amountUsd"] % 0.25 > 0:
                    coins += 1
                
                tflex.dispense(coins)
                
                print(json.dumps({
                    "success": True,
                    "transactionId": f"WC-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}",
                    "coinsDispensed": coins
                }))
            except Exception as e:
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                sys.exit(1)
    else:
        # Run Flask app
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        debug = os.getenv("DEV_MODE", "false").lower() == "true"
        
        logger.info(f"Starting WorldCash backend on {host}:{port}")
        app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
