#!/usr/bin/env python3
"""
Simple example showing how serial communication works with T-Flex dispenser
This demonstrates the basic concepts without the complexity of the full app
"""

import serial
import time

def simple_serial_example():
    """
    Simple example of how serial communication works
    """
    print("=== How Serial Communication Works ===\n")
    
    # Step 1: Open connection to the device
    print("1. Opening connection to T-Flex dispenser...")
    try:
        # This creates a "phone line" to the hardware
        dispenser = serial.Serial(
            port='/dev/ttyUSB0',    # The "phone number" (USB port)
            baudrate=9600,          # How fast to talk (9600 words per second)
            timeout=2               # How long to wait for answer (2 seconds)
        )
        print("   ✅ Connected successfully!")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("   (This is normal if no T-Flex is connected)")
        return
    
    # Step 2: Send a command
    print("\n2. Sending command to dispense 10 coins...")
    
    # Create the command message
    command = "DISPENSE 10\r\n"
    print(f"   Command to send: '{command.strip()}' (plus \\r\\n)")
    
    # Convert text to bytes and send it
    dispenser.write(command.encode('utf-8'))
    print("   📤 Command sent!")
    
    # Step 3: Wait for response
    print("\n3. Waiting for response...")
    try:
        # Read the response (like waiting for someone to answer the phone)
        response = dispenser.readline().decode('utf-8').strip()
        print(f"   📥 Response received: '{response}'")
        
        # Interpret the response
        if "OK" in response:
            print("   ✅ Success! Coins were dispensed")
        elif "ERROR" in response:
            print("   ❌ Error occurred")
        else:
            print(f"   ❓ Unknown response: {response}")
            
    except Exception as e:
        print(f"   ❌ Failed to read response: {e}")
    
    # Step 4: Check status
    print("\n4. Checking dispenser status...")
    dispenser.write(b"STATUS\r\n")
    try:
        status = dispenser.readline().decode('utf-8').strip()
        print(f"   📥 Status: '{status}'")
    except:
        print("   ❌ Could not read status")
    
    # Step 5: Close connection
    print("\n5. Closing connection...")
    dispenser.close()
    print("   ✅ Connection closed")

def explain_serial_basics():
    """
    Explain the basic concepts
    """
    print("\n=== Serial Communication Basics ===\n")
    
    print("🔌 PHYSICAL CONNECTION:")
    print("   Raspberry Pi USB Port ←→ USB Cable ←→ T-Flex Dispenser")
    print("   (Just like plugging in a keyboard or mouse)")
    
    print("\n💬 HOW DEVICES 'TALK':")
    print("   1. Computer: 'Hey dispenser, give me 10 coins'")
    print("   2. Dispenser: *dispenses coins* 'OK, done!'")
    print("   3. Computer: 'Thanks!' *logs the transaction*")
    
    print("\n📝 COMMAND FORMAT:")
    print("   COMMAND PARAMETER\\r\\n")
    print("   DISPENSE 10\\r\\n     ← Give me 10 coins")
    print("   STATUS\\r\\n          ← How are you doing?")
    print("   RESET\\r\\n           ← Restart yourself")
    
    print("\n⚙️  SERIAL SETTINGS:")
    print("   Port: /dev/ttyUSB0    ← Which USB port")
    print("   Baudrate: 9600        ← Speed (9600 bits per second)")
    print("   Timeout: 2            ← Wait 2 seconds for response")
    
    print("\n🔄 TYPICAL CONVERSATION:")
    print("   Computer → Dispenser: 'DISPENSE 40\\r\\n'")
    print("   Dispenser → Computer: 'OK DISPENSED 40\\r\\n'")
    print("   Computer → Dispenser: 'STATUS\\r\\n'")
    print("   Dispenser → Computer: 'STATUS READY LEVEL 85%\\r\\n'")

def show_rolu_implementation():
    """
    Show how RoluATM actually uses this
    """
    print("\n=== How RoluATM Uses Serial Commands ===\n")
    
    print("📱 USER INTERACTION:")
    print("   1. User selects $10.00 withdrawal on touch screen")
    print("   2. User completes World ID verification")
    print("   3. Frontend sends request to backend")
    
    print("\n🧮 BACKEND CALCULATION:")
    print("   1. Backend calculates: $10.00 ÷ $0.25 = 40 quarters")
    print("   2. Backend verifies World ID proof")
    print("   3. Backend checks withdrawal limits")
    
    print("\n🪙 HARDWARE CONTROL:")
    print("   1. Backend sends: 'DISPENSE 40\\r\\n'")
    print("   2. T-Flex counts out 40 quarters")
    print("   3. T-Flex responds: 'OK DISPENSED 40\\r\\n'")
    print("   4. Backend logs transaction to database")
    
    print("\n✅ COMPLETION:")
    print("   1. User collects 40 quarters ($10.00)")
    print("   2. Crypto is deducted from user's wallet")
    print("   3. Transaction is complete!")

def show_error_handling():
    """
    Show what happens when things go wrong
    """
    print("\n=== Error Handling ===\n")
    
    print("🚫 COMMON ERRORS:")
    print("   Dispenser: 'ERROR JAM'        → Coins are stuck")
    print("   Dispenser: 'ERROR EMPTY'      → No coins left")
    print("   Dispenser: 'ERROR TIMEOUT'    → Taking too long")
    print("   No response                   → Dispenser disconnected")
    
    print("\n🔧 ROLU'S RESPONSE:")
    print("   1. Stop the transaction immediately")
    print("   2. Don't deduct crypto from user")
    print("   3. Show error message on screen")
    print("   4. Log error for maintenance")
    print("   5. Alert operator if needed")

if __name__ == "__main__":
    explain_serial_basics()
    show_rolu_implementation()
    show_error_handling()
    
    print("\n" + "="*50)
    print("Want to see it in action? Run:")
    print("python3 serial_example.py")
    print("(Note: Only works with actual T-Flex connected)")
    
    # Uncomment the next line to try the actual serial communication
    # simple_serial_example() 