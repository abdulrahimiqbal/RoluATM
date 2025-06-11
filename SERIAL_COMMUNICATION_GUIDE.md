# Serial Communication Guide for RoluATM

## 🔌 What Are Serial Commands?

**Serial commands are just text messages** that hardware devices understand. Think of it like texting your coin dispenser!

### Simple Analogy
```
You → Friend: "Can you give me 10 quarters?"
Friend → You: "Sure! Here are 10 quarters."

Computer → T-Flex: "DISPENSE 10\r\n"
T-Flex → Computer: "OK DISPENSED 10\r\n"
```

## 🖥️ Physical Connection

```
┌─────────────────┐    USB Cable    ┌─────────────────┐
│   Raspberry Pi  │ ←──────────────→ │  T-Flex Coin    │
│                 │                  │  Dispenser      │
│   USB Port      │                  │                 │
│   /dev/ttyUSB0  │                  │   Serial Port   │
└─────────────────┘                  └─────────────────┘
```

**What happens physically:**
1. USB cable carries electrical signals
2. Raspberry Pi converts text commands to electrical pulses
3. T-Flex receives pulses and converts them back to text
4. T-Flex processes the command and responds

## 📡 How Commands Travel

### Step 1: Python Code Creates Command
```python
command = "DISPENSE 40\r\n"
# This is just a text string in memory
```

### Step 2: Convert to Electrical Signals
```python
dispenser.write(command.encode('utf-8'))
# Converts text to electrical pulses:
# D = 01000100
# I = 01001001
# S = 01010011
# etc...
```

### Step 3: Travel Through USB Cable
```
Raspberry Pi USB → Electrical pulses → T-Flex Serial Port
   01000100 01001001 01010011...
```

### Step 4: T-Flex Converts Back to Text
```
T-Flex receives: 01000100 01001001 01010011...
T-Flex reads: "DISPENSE 40\r\n"
T-Flex understands: "Give out 40 coins"
```

## 🗣️ Command Language

The T-Flex "speaks" a simple command language:

### Basic Commands
```bash
DISPENSE [number]    # Give out X coins
STATUS              # How are you doing?
RESET               # Restart yourself
LEVEL               # How many coins left?
```

### Command Format
```
COMMAND PARAMETER\r\n
   ↑        ↑      ↑
 Action   Value   End
```

**The `\r\n` part:**
- `\r` = Carriage Return (like pressing Enter on old typewriters)
- `\n` = New Line (move to next line)
- Together = "I'm done talking, your turn!"

## 💬 Real Conversation Example

```
Computer → T-Flex: "DISPENSE 40\r\n"
T-Flex thinks: "They want 40 coins"
T-Flex: *mechanical whirring, coins dropping*
T-Flex → Computer: "OK DISPENSED 40\r\n"

Computer → T-Flex: "STATUS\r\n"
T-Flex → Computer: "STATUS READY LEVEL 85%\r\n"

Computer → T-Flex: "LEVEL\r\n"
T-Flex → Computer: "LEVEL 850 COINS\r\n"
```

## 🔧 Technical Settings

### Serial Port Configuration
```python
serial.Serial(
    port='/dev/ttyUSB0',    # Which USB port
    baudrate=9600,          # Speed: 9600 bits per second
    timeout=2,              # Wait 2 seconds for response
    bytesize=8,             # 8 bits per character
    parity='N',             # No parity checking
    stopbits=1              # 1 stop bit
)
```

**What these mean:**
- **Port**: Like a phone number - which connection to use
- **Baudrate**: How fast to talk (9600 = 9600 characters per second)
- **Timeout**: How long to wait before giving up
- **Other settings**: Technical details for reliable communication

## 🔍 Finding Your T-Flex

### On Raspberry Pi:
```bash
# List all connected devices
ls /dev/tty*

# Common T-Flex ports:
/dev/ttyUSB0    # USB-to-Serial adapter
/dev/ttyACM0    # Direct USB connection
/dev/ttyS0      # Built-in serial port

# Test which port works:
sudo minicom -D /dev/ttyUSB0 -b 9600
```

### Testing Connection:
```bash
# Open serial terminal
sudo minicom -D /dev/ttyUSB0 -b 9600

# Type commands:
STATUS          # Press Enter
DISPENSE 1      # Press Enter (test with 1 coin)

# Expected responses:
STATUS READY LEVEL 85%
OK DISPENSED 1
```

## 🚨 Error Messages

### Common T-Flex Responses:
```bash
"OK DISPENSED 40"           # Success!
"ERROR JAM"                 # Coins stuck
"ERROR EMPTY"               # No coins left
"ERROR INVALID COMMAND"     # Don't understand
"ERROR TIMEOUT"             # Taking too long
"ERROR SENSOR"              # Hardware problem
```

### RoluATM Error Handling:
```python
if "OK" in response:
    # Success - continue transaction
    return {"success": True, "coins_dispensed": num_coins}
    
elif "ERROR" in response:
    # Problem - stop transaction, don't charge user
    return {"success": False, "error": response}
    
else:
    # Unknown response - be safe, stop transaction
    return {"success": False, "error": "Unknown response"}
```

## 🏗️ How RoluATM Uses This

### Complete Transaction Flow:

1. **User Input**: "I want $10.00"
2. **Calculation**: $10.00 ÷ $0.25 = 40 quarters
3. **Verification**: World ID check passes
4. **Serial Command**: Send "DISPENSE 40\r\n"
5. **Hardware Response**: "OK DISPENSED 40\r\n"
6. **Database**: Log transaction
7. **User**: Collect 40 quarters

### In Python Code:
```python
def dispense_coins(self, amount_usd):
    # Calculate coins needed
    coin_value = 0.25  # Quarter value
    num_coins = int(amount_usd / coin_value)
    
    # Send command to hardware
    command = f"DISPENSE {num_coins}\r\n"
    self.serial_conn.write(command.encode())
    
    # Wait for response
    response = self.serial_conn.readline().decode().strip()
    
    # Check if successful
    if "OK" in response:
        return {"success": True, "coins_dispensed": num_coins}
    else:
        return {"success": False, "error": response}
```

## 🧪 Testing Without Hardware

For development, RoluATM can simulate the T-Flex:

```python
if DEV_MODE:
    # Pretend to dispense coins
    logger.info(f"MOCK: Dispensing {num_coins} coins")
    time.sleep(2)  # Simulate dispense time
    return {"success": True, "coins_dispensed": num_coins}
```

This lets you test everything except the actual coin dispensing!

## 🔧 Troubleshooting

### Connection Issues:
```bash
# Check if device is detected
lsusb                    # Should show T-Flex or USB-Serial adapter
ls /dev/tty*            # Should show ttyUSB0 or ttyACM0

# Permission issues
sudo usermod -a -G dialout pi    # Add user to serial group
sudo reboot                      # Restart to apply
```

### Communication Issues:
```bash
# Test with simple terminal
sudo minicom -D /dev/ttyUSB0 -b 9600

# If no response, try different settings:
sudo minicom -D /dev/ttyUSB0 -b 19200   # Different speed
sudo minicom -D /dev/ttyACM0 -b 9600     # Different port
```

### Python Issues:
```python
# Add error checking
try:
    dispenser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
    dispenser.write(b"STATUS\r\n")
    response = dispenser.readline()
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
```

## 🎯 Key Takeaways

1. **Serial commands are just text messages** sent over a USB cable
2. **Commands end with `\r\n`** to tell the device "I'm done talking"
3. **The T-Flex responds with text** like "OK DISPENSED 40"
4. **RoluATM converts user actions** into these simple commands
5. **Everything is logged and error-checked** for safety

Think of it like having a conversation with your coin dispenser - you ask it to do something, it tells you if it worked!

## 📞 Next Steps

1. **Get a T-Flex dispenser** compatible with your coin type
2. **Connect it to your Raspberry Pi** via USB
3. **Test basic commands** with minicom
4. **Configure RoluATM** with the correct port
5. **Test the complete flow** with mock transactions

The serial communication is actually the simplest part - it's just sending text messages back and forth! 