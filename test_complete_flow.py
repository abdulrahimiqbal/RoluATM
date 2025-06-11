#!/usr/bin/env python3
"""
RoluATM Complete Flow Test
Tests the full transaction flow from kiosk to payment to coin dispensing
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
KIOSK_URL = "http://localhost:3000"
MINI_APP_URL = "http://localhost:3001"

def print_step(step_num, description):
    print(f"\n=== STEP {step_num}: {description} ===")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def test_health_check():
    """Test if all services are running"""
    print_step(1, "Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is healthy - Dev mode: {data['dev_mode']}")
            print_success(f"Hardware status: {data['hardware']}")
            return True
        else:
            print_error(f"Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend is not running: {e}")
        return False

def test_transaction_creation():
    """Test creating a new transaction"""
    print_step(2, "Transaction Creation")
    
    amount = 5.00
    payload = {"amount": amount}
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/transaction/create",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            transaction = response.json()
            print_success(f"Transaction created: {transaction['id']}")
            print_success(f"Amount: ${transaction['fiat_amount']}")
            print_success(f"Quarters: {transaction['quarters']}")
            print_success(f"Total: ${transaction['total']}")
            print_success(f"Mini app URL: {transaction['mini_app_url']}")
            print_success(f"Expires at: {transaction['expires_at']}")
            return transaction
        else:
            print_error(f"Transaction creation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Transaction creation error: {e}")
        return None

def test_transaction_status(transaction_id):
    """Test getting transaction status"""
    print_step(3, "Transaction Status Check")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/transaction/{transaction_id}/status",
            timeout=10
        )
        
        if response.status_code == 200:
            status_data = response.json()
            print_success(f"Status: {status_data['status']}")
            print_success(f"Progress: {status_data['progress']}%")
            return status_data
        else:
            print_error(f"Status check failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Status check error: {e}")
        return None

def test_payment_processing(transaction_id):
    """Test payment processing with mock World ID"""
    print_step(4, "Payment Processing (Mock World ID)")
    
    # Mock World ID proof data
    payload = {
        "transaction_id": transaction_id,
        "proof": "mock_proof_12345",
        "nullifier_hash": "mock_nullifier_67890",
        "merkle_root": "mock_merkle_root_abcdef"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/transaction/pay",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # Coin dispensing might take time
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Payment processed successfully!")
            print_success(f"Message: {result['message']}")
            print_success(f"Quarters dispensed: {result['quarters_dispensed']}")
            return True
        else:
            print_error(f"Payment processing failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Payment processing error: {e}")
        return False

def test_final_status(transaction_id):
    """Test final transaction status after payment"""
    print_step(5, "Final Status Check")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/transaction/{transaction_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            transaction = response.json()
            print_success(f"Final status: {transaction['status']}")
            print_success(f"Progress: {transaction['progress']}%")
            if transaction.get('paid_at'):
                print_success(f"Paid at: {transaction['paid_at']}")
            if transaction.get('dispense_completed_at'):
                print_success(f"Dispensing completed at: {transaction['dispense_completed_at']}")
            if transaction.get('nullifier_hash'):
                print_success(f"World ID nullifier: {transaction['nullifier_hash']}")
            return transaction
        else:
            print_error(f"Final status check failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Final status check error: {e}")
        return None

def test_frontend_services():
    """Test that frontend services are running"""
    print_step(6, "Frontend Services Check")
    
    services = [
        ("Kiosk App", KIOSK_URL),
        ("Mini App", MINI_APP_URL)
    ]
    
    all_running = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{name} is running at {url}")
            else:
                print_error(f"{name} returned status {response.status_code}")
                all_running = False
        except Exception as e:
            print_error(f"{name} is not accessible: {e}")
            all_running = False
    
    return all_running

def main():
    """Run the complete flow test"""
    print("🎰 RoluATM Complete Flow Test")
    print("="*50)
    
    # Step 1: Health check
    if not test_health_check():
        print_error("Backend is not running. Please start the server first.")
        sys.exit(1)
    
    # Step 2: Create transaction
    transaction = test_transaction_creation()
    if not transaction:
        print_error("Transaction creation failed. Stopping test.")
        sys.exit(1)
    
    transaction_id = transaction['id']
    
    # Step 3: Check initial status
    status = test_transaction_status(transaction_id)
    if not status or status['status'] != 'pending':
        print_error("Transaction status is not as expected.")
        sys.exit(1)
    
    # Step 4: Process payment (mock)
    if not test_payment_processing(transaction_id):
        print_error("Payment processing failed.")
        sys.exit(1)
    
    # Step 5: Check final status
    final_transaction = test_final_status(transaction_id)
    if not final_transaction:
        print_error("Final status check failed.")
        sys.exit(1)
    
    # Step 6: Check frontend services
    frontend_ok = test_frontend_services()
    
    # Summary
    print("\n🎉 FLOW TEST SUMMARY")
    print("="*50)
    
    if final_transaction['status'] == 'complete':
        print_success("✅ Complete transaction flow PASSED!")
        print_success(f"   Transaction ID: {transaction_id}")
        print_success(f"   Amount processed: ${final_transaction['fiat_amount']}")
        print_success(f"   Quarters dispensed: {int(float(final_transaction['fiat_amount']) / 0.25)}")
        print_success(f"   Status: {final_transaction['status']}")
    else:
        print_error(f"❌ Transaction ended in unexpected status: {final_transaction['status']}")
    
    if frontend_ok:
        print_success("✅ Frontend services are running")
        print_success(f"   Kiosk App: {KIOSK_URL}")
        print_success(f"   Mini App: {MINI_APP_URL}")
    else:
        print_error("❌ Some frontend services are not accessible")
    
    print(f"\n📱 To test the complete user flow:")
    print(f"   1. Open kiosk app: {KIOSK_URL}")
    print(f"   2. Select amount and create transaction")
    print(f"   3. Scan QR code or open mini app URL")
    print(f"   4. Complete World ID verification in mini app")
    print(f"   5. Watch quarters being dispensed on kiosk")

if __name__ == "__main__":
    main() 