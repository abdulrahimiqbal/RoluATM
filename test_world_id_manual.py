#!/usr/bin/env python3
"""
Manual World ID Testing Guide for RoluATM
Step-by-step instructions for testing World ID integration
"""

import requests
import json
import webbrowser
import time

def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"🌍 {title}")
    print(f"{'='*60}")

def create_test_transaction():
    """Create a test transaction for World ID testing"""
    print_header("Creating Test Transaction for World ID")
    
    try:
        transaction_data = {"amount": 5.00}
        response = requests.post(
            "http://localhost:8000/api/transaction/create",
            json=transaction_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            transaction = response.json()
            transaction_id = transaction["id"]
            mini_app_url = transaction["mini_app_url"]
            
            print("✅ Transaction created successfully!")
            print(f"📄 Transaction ID: {transaction_id}")
            print(f"💰 Amount: ${transaction['amount']}")
            print(f"🪙 Quarters: {transaction['quarters']}")
            print(f"🔗 Mini App URL: {mini_app_url}")
            
            return transaction_id, mini_app_url
        else:
            print("❌ Failed to create transaction")
            print(f"Error: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error creating transaction: {e}")
        return None, None

def manual_world_id_testing():
    """Provide manual testing instructions"""
    print_header("Manual World ID Testing Instructions")
    
    print("🎯 **Testing Objectives:**")
    print("- Verify MiniKit integration in browser")
    print("- Test World ID verification flow")
    print("- Confirm payment processing")
    print("- Validate transaction completion")
    
    print("\n📱 **Device Requirements:**")
    print("- Mobile device with World App installed")
    print("- World ID verified (orb or device)")
    print("- Browser access to mini-app")
    
    print("\n🔄 **Testing Steps:**")
    
    # Step 1: Create transaction
    print("\n1️⃣ Creating test transaction...")
    transaction_id, mini_app_url = create_test_transaction()
    
    if not transaction_id:
        print("❌ Cannot proceed without valid transaction")
        return
    
    # Step 2: Open mini-app
    print("\n2️⃣ Opening mini-app...")
    print(f"🔗 URL: {mini_app_url}")
    print("   - Mini-app should display transaction details")
    print("   - Amount, quarters, and fee should be visible")
    print("   - World ID verification section should appear")
    
    try:
        # Attempt to open in browser
        webbrowser.open(mini_app_url)
        print("✅ Attempted to open mini-app in browser")
    except:
        print("⚠️ Could not auto-open browser. Please manually navigate to URL above")
    
    print("\n3️⃣ World ID Verification Process:")
    print("   a) Click 'Pay $5.50' button in mini-app")
    print("   b) MiniKit should initialize World ID verification")
    print("   c) World App should open (if on mobile)")
    print("   d) Complete verification with your World ID")
    print("   e) Return to mini-app after verification")
    
    print("\n4️⃣ Payment Processing:")
    print("   - Verification proof will be submitted to backend")
    print("   - Transaction status should change to 'paid'")
    print("   - Dispensing simulation will begin")
    print("   - Final status should be 'complete'")
    
    print("\n🔍 **What to Observe:**")
    print("✅ MiniKit Provider loads without errors")
    print("✅ World ID verification UI appears")
    print("✅ Verification completes successfully")
    print("✅ Payment processing works")
    print("✅ Transaction status updates in real-time")
    
    print("\n🐛 **Debugging Information:**")
    print("- Open browser developer tools (F12)")
    print("- Check Console tab for MiniKit errors")
    print("- Monitor Network tab for API calls")
    print("- Watch for World ID verification events")
    
    print("\n📊 **Backend Monitoring:**")
    print("Check backend terminal for logs:")
    print(f"- Transaction created: {transaction_id}")
    print("- World ID verification requests")
    print("- Payment processing status")
    print("- Dispensing simulation progress")
    
    return transaction_id

def verify_world_id_environment():
    """Verify World ID environment setup"""
    print_header("World ID Environment Verification")
    
    print("🔧 **Required Environment Variables:**")
    print("VITE_WORLD_APP_ID=app_staging_c6e6bc4b19c31866df3d9d02b6a5b4db")
    print("WORLD_CLIENT_SECRET=sk_c89f32b0b0d0e2fda1d8b93c40e3e6f3c01a5b19")
    
    print("\n📁 **Configuration Files:**")
    print("Create these files with the above variables:")
    print("- .env.local (project root)")
    print("- mini-app/.env.local (mini-app directory)")
    print("- kiosk-app/.env.local (kiosk-app directory)")
    
    print("\n🔄 **After creating env files:**")
    print("1. Restart all development servers")
    print("2. Clear browser cache")
    print("3. Reload applications")

def test_minikit_browser_compatibility():
    """Test MiniKit browser compatibility"""
    print_header("MiniKit Browser Compatibility Test")
    
    print("🌐 **Browser Testing:**")
    print("Test mini-app in different browsers:")
    print("- Chrome/Chromium (recommended)")
    print("- Firefox")
    print("- Safari (macOS)")
    print("- Mobile browsers")
    
    print("\n📱 **Mobile Testing:**")
    print("1. Open mini-app URL on mobile device")
    print("2. Ensure World App is installed")
    print("3. Test MiniKit integration")
    print("4. Verify World ID verification flow")
    
    print("\n🔧 **Common Issues:**")
    print("- MiniKit not detected: Check World App installation")
    print("- Verification fails: Ensure World ID is verified")
    print("- CORS errors: Check backend CORS configuration")
    print("- Environment errors: Verify .env.local files")

def production_testing_checklist():
    """Production testing checklist"""
    print_header("Production World ID Testing Checklist")
    
    print("✅ **Pre-Production Tests:**")
    checklist = [
        "Environment variables configured",
        "MiniKit provider properly initialized", 
        "World ID verification working in development",
        "Mock verification flow complete",
        "Real World App testing on mobile",
        "Orb verification tested",
        "Device verification tested", 
        "Error handling for failed verification",
        "Rate limiting implemented",
        "Security review completed",
        "Production World ID app configured",
        "SSL certificates for HTTPS",
        "Production API endpoints tested"
    ]
    
    for i, item in enumerate(checklist, 1):
        print(f"{i:2d}. [ ] {item}")
    
    print("\n🚀 **Deployment Steps:**")
    print("1. Configure production World ID app")
    print("2. Update environment variables")
    print("3. Deploy to production servers")
    print("4. Test with real World ID verification")
    print("5. Monitor verification success rates")
    print("6. Set up error logging and alerting")

def main():
    """Main testing function"""
    print("🌍 RoluATM World ID Manual Testing Guide")
    print("=" * 60)
    
    # Environment verification
    verify_world_id_environment()
    
    # Browser compatibility
    test_minikit_browser_compatibility()
    
    # Manual testing
    transaction_id = manual_world_id_testing()
    
    # Production checklist
    production_testing_checklist()
    
    print_header("Testing Summary")
    
    if transaction_id:
        print("🎉 Test transaction created successfully!")
        print(f"📄 Transaction ID: {transaction_id}")
        print("🔄 Follow the manual testing steps above")
        print("🐛 Use browser dev tools for debugging")
        print("📊 Monitor backend logs for verification")
    else:
        print("❌ Could not create test transaction")
        print("🔧 Check backend server and try again")
    
    print("\n📞 **Support:**")
    print("- Check RoluATM documentation")
    print("- Review World ID integration guide") 
    print("- Test in development mode first")
    print("- Verify all environment variables")

if __name__ == "__main__":
    main() 