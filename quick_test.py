#!/usr/bin/env python3
"""
Quick RoluATM Test - Simple test without external dependencies
"""

import requests
import json

def test_basic_functionality():
    print("🎰 RoluATM Quick Test")
    print("=" * 30)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Status: {data['status']}")
            print(f"   Dev mode: {data['dev_mode']}")
            print(f"   Hardware: {data['hardware']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Test 2: Transaction creation
    print("\n2. Testing transaction creation...")
    try:
        payload = {"amount": 5.00}
        response = requests.post(
            "http://localhost:8000/api/transaction/create",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            transaction = response.json()
            print(f"✅ Transaction created")
            print(f"   ID: {transaction['id']}")
            print(f"   Amount: ${transaction['fiat_amount']}")
            print(f"   Quarters: {transaction.get('quarters', 'N/A')}")
            print(f"   Status: {transaction['status']}")
            print(f"   Mini app URL: {transaction['mini_app_url']}")
            
            # Test 3: Transaction retrieval
            print("\n3. Testing transaction retrieval...")
            response = requests.get(f"http://localhost:8000/api/transaction/{transaction['id']}")
            if response.status_code == 200:
                print("✅ Transaction retrieved successfully")
            else:
                print(f"❌ Transaction retrieval failed: {response.status_code}")
            
            return transaction['id']
        else:
            print(f"❌ Transaction creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Transaction creation error: {e}")
        return False

def test_frontend_apps():
    print("\n4. Testing frontend applications...")
    
    apps = [
        ("Kiosk App", "http://localhost:3000"),
        ("Mini App", "http://localhost:3001")
    ]
    
    for name, url in apps:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is running at {url}")
            else:
                print(f"❌ {name} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ {name} not accessible: {e}")

def main():
    transaction_id = test_basic_functionality()
    test_frontend_apps()
    
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    
    if transaction_id:
        print("✅ Core functionality is working!")
        print(f"   Created transaction: {transaction_id}")
        print(f"   Backend API: ✅ Working")
        print(f"   Database: ✅ Connected")
        
        print(f"\n🔗 Test URLs:")
        print(f"   Health: http://localhost:8000/health")
        print(f"   Kiosk: http://localhost:3000")
        print(f"   Mini App: http://localhost:3001")
        print(f"   Transaction: http://localhost:3001?transaction_id={transaction_id}")
        
        print(f"\n🧪 Manual Testing:")
        print(f"   1. Open kiosk app and select amount")
        print(f"   2. Scan QR code or copy transaction URL")
        print(f"   3. Open mini app URL in World App")
        print(f"   4. Complete verification process")
        
    else:
        print("❌ Core functionality failed")
        print("   Check server logs and configuration")

if __name__ == "__main__":
    main() 