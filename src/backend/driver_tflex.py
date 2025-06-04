"""
Telequip T-Flex Coin Dispenser Driver
Serial communication driver for T-Flex hardware
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from threading import Lock, Event
from contextlib import contextmanager

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logging.warning("pyserial not available - using mock mode")

logger = logging.getLogger(__name__)

@dataclass
class TFlexStatus:
    """T-Flex hardware status"""
    low_coin: bool = False
    lid_open: bool = False
    fault: bool = False
    coins_available: int = 0
    last_update: float = 0.0

class TFlexError(Exception):
    """T-Flex specific errors"""
    pass

class TFlexTimeoutError(TFlexError):
    """T-Flex communication timeout"""
    pass

class TFlexHardwareError(TFlexError):
    """T-Flex hardware fault"""
    pass

class TFlex:
    """
    Telequip T-Flex coin dispenser driver
    
    Communicates via USB CDC (ACM) interface at 9600 baud
    Protocol: Binary commands with CRC validation
    """
    
    # T-Flex command constants
    CMD_STATUS = 0x01
    CMD_DISPENSE = 0x02
    CMD_RESET = 0x03
    CMD_CALIBRATE = 0x04
    
    # Response codes
    RESP_OK = 0x00
    RESP_ERROR = 0x01
    RESP_BUSY = 0x02
    RESP_LOW_COIN = 0x03
    RESP_LID_OPEN = 0x04
    RESP_FAULT = 0x05
    
    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 9600, timeout: float = 5.0):
        """
        Initialize T-Flex driver
        
        Args:
            port: Serial port path (default: /dev/ttyACM0)
            baudrate: Communication speed (default: 9600)
            timeout: Command timeout in seconds (default: 5.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._lock = Lock()
        self._last_status = TFlexStatus()
        self._mock_mode = not SERIAL_AVAILABLE
        self._mock_coins = 1000  # Mock coin count for testing
        
        if not self._mock_mode:
            self._initialize_connection()
        else:
            logger.info("T-Flex driver running in mock mode")
    
    def _initialize_connection(self) -> None:
        """Initialize serial connection to T-Flex"""
        try:
            if SERIAL_AVAILABLE:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                
                # Wait for device to initialize
                time.sleep(2)
                
                # Clear any pending data
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                
                logger.info(f"T-Flex connected on {self.port}")
            else:
                raise TFlexError("Serial not available")
                
        except Exception as e:
            logger.error(f"Failed to connect to T-Flex: {e}")
            self._mock_mode = True
            logger.info("Falling back to mock mode")
    
    @contextmanager
    def _serial_lock(self):
        """Context manager for thread-safe serial access"""
        with self._lock:
            yield
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC-8 checksum for T-Flex protocol"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def _send_command(self, command: int, data: bytes = b"") -> bytes:
        """
        Send command to T-Flex and receive response
        
        Args:
            command: Command byte
            data: Additional command data
            
        Returns:
            Response data bytes
            
        Raises:
            TFlexTimeoutError: Communication timeout
            TFlexHardwareError: Hardware fault
            TFlexError: Other communication errors
        """
        if self._mock_mode:
            return self._mock_command(command, data)
        
        if not self._serial or not self._serial.is_open:
            raise TFlexError("Serial connection not available")
        
        # Build command packet: [STX][LEN][CMD][DATA...][CRC][ETX]
        packet = bytearray([0x02])  # STX
        packet.append(len(data) + 1)  # Length (command + data)
        packet.append(command)
        packet.extend(data)
        
        # Calculate and append CRC
        crc = self._calculate_crc(packet[1:-1] if len(packet) > 1 else packet[1:])
        packet.append(crc)
        packet.append(0x03)  # ETX
        
        with self._serial_lock():
            try:
                # Send command
                self._serial.write(packet)
                self._serial.flush()
                
                # Wait for response
                response = bytearray()
                start_time = time.time()
                
                while time.time() - start_time < self.timeout:
                    if self._serial.in_waiting > 0:
                        byte = self._serial.read(1)
                        if byte:
                            response.extend(byte)
                            
                            # Check for complete packet
                            if len(response) >= 2 and response[0] == 0x02:
                                expected_length = response[1] + 4  # STX + LEN + DATA + CRC + ETX
                                if len(response) >= expected_length and response[-1] == 0x03:
                                    break
                    time.sleep(0.01)
                else:
                    raise TFlexTimeoutError(f"Command timeout after {self.timeout}s")
                
                # Validate response
                if len(response) < 5:
                    raise TFlexError("Invalid response length")
                
                if response[0] != 0x02 or response[-1] != 0x03:
                    raise TFlexError("Invalid response framing")
                
                # Verify CRC
                data_bytes = response[1:-2]
                received_crc = response[-2]
                calculated_crc = self._calculate_crc(data_bytes)
                
                if received_crc != calculated_crc:
                    raise TFlexError("CRC mismatch in response")
                
                # Extract response data (skip STX, LEN, and ETX, CRC)
                response_data = response[2:-2]
                
                # Check for error responses
                if len(response_data) > 0:
                    status_code = response_data[0]
                    if status_code == self.RESP_ERROR:
                        raise TFlexHardwareError("T-Flex reported error")
                    elif status_code == self.RESP_FAULT:
                        raise TFlexHardwareError("T-Flex hardware fault")
                
                return bytes(response_data)
                
            except serial.SerialException as e:
                raise TFlexError(f"Serial communication error: {e}")
    
    def _mock_command(self, command: int, data: bytes = b"") -> bytes:
        """Mock command responses for testing"""
        time.sleep(0.1)  # Simulate communication delay
        
        if command == self.CMD_STATUS:
            # Return mock status
            status_byte = 0
            if self._mock_coins < 50:
                status_byte |= 0x01  # Low coin
            
            return bytes([self.RESP_OK, status_byte, (self._mock_coins >> 8) & 0xFF, self._mock_coins & 0xFF])
        
        elif command == self.CMD_DISPENSE:
            if len(data) >= 2:
                coins_requested = (data[0] << 8) | data[1]
                if coins_requested > self._mock_coins:
                    return bytes([self.RESP_LOW_COIN])
                
                self._mock_coins -= coins_requested
                logger.info(f"Mock dispensed {coins_requested} coins, {self._mock_coins} remaining")
                return bytes([self.RESP_OK])
            else:
                return bytes([self.RESP_ERROR])
        
        elif command == self.CMD_RESET:
            self._mock_coins = 1000  # Reset coin count
            return bytes([self.RESP_OK])
        
        else:
            return bytes([self.RESP_ERROR])
    
    def status(self) -> Dict[str, Any]:
        """
        Get current T-Flex status
        
        Returns:
            Dictionary with status information:
            - low_coin: bool - Coin level is low
            - lid_open: bool - Dispenser lid is open  
            - fault: bool - Hardware fault detected
            - coins_available: int - Estimated coins remaining
        """
        try:
            response = self._send_command(self.CMD_STATUS)
            
            if len(response) >= 4:
                status_code = response[0]
                status_flags = response[1]
                coins_high = response[2]
                coins_low = response[3]
                
                if status_code == self.RESP_OK:
                    self._last_status = TFlexStatus(
                        low_coin=(status_flags & 0x01) != 0,
                        lid_open=(status_flags & 0x02) != 0,
                        fault=(status_flags & 0x04) != 0,
                        coins_available=(coins_high << 8) | coins_low,
                        last_update=time.time()
                    )
                else:
                    self._last_status.fault = True
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            self._last_status.fault = True
        
        return {
            "low_coin": self._last_status.low_coin,
            "lid_open": self._last_status.lid_open,
            "fault": self._last_status.fault,
            "coins_available": self._last_status.coins_available
        }
    
    def dispense(self, coins: int) -> None:
        """
        Dispense specified number of coins
        
        Args:
            coins: Number of coins to dispense (1-255)
            
        Raises:
            TFlexError: Communication or hardware error
            ValueError: Invalid coin count
        """
        if not isinstance(coins, int) or coins < 1 or coins > 255:
            raise ValueError("Coin count must be between 1 and 255")
        
        logger.info(f"Dispensing {coins} coins")
        
        # Send dispense command with coin count
        data = bytes([(coins >> 8) & 0xFF, coins & 0xFF])
        
        try:
            response = self._send_command(self.CMD_DISPENSE, data)
            
            if len(response) > 0:
                status_code = response[0]
                
                if status_code == self.RESP_OK:
                    logger.info(f"Successfully dispensed {coins} coins")
                elif status_code == self.RESP_LOW_COIN:
                    raise TFlexHardwareError("Insufficient coins in dispenser")
                elif status_code == self.RESP_BUSY:
                    raise TFlexHardwareError("Dispenser is busy")
                elif status_code == self.RESP_LID_OPEN:
                    raise TFlexHardwareError("Dispenser lid is open")
                else:
                    raise TFlexHardwareError(f"Dispense failed with code: {status_code}")
            else:
                raise TFlexError("No response to dispense command")
                
        except TFlexError:
            raise
        except Exception as e:
            raise TFlexError(f"Dispense operation failed: {e}")
    
    def reset(self) -> None:
        """
        Reset T-Flex dispenser
        
        Raises:
            TFlexError: Communication or hardware error
        """
        logger.info("Resetting T-Flex dispenser")
        
        try:
            response = self._send_command(self.CMD_RESET)
            
            if len(response) > 0 and response[0] == self.RESP_OK:
                logger.info("T-Flex reset successful")
            else:
                raise TFlexHardwareError("Reset command failed")
                
        except TFlexError:
            raise
        except Exception as e:
            raise TFlexError(f"Reset operation failed: {e}")
    
    def close(self) -> None:
        """Close serial connection"""
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("T-Flex connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Convenience function for testing
def test_tflex(port: str = "/dev/ttyACM0") -> None:
    """Test T-Flex functionality"""
    print(f"Testing T-Flex on {port}")
    
    try:
        with TFlex(port=port) as tflex:
            # Check status
            status = tflex.status()
            print(f"Status: {status}")
            
            if not status["fault"] and not status["low_coin"]:
                # Test small dispense
                print("Testing dispense of 5 coins...")
                tflex.dispense(5)
                print("Dispense successful!")
            else:
                print("Cannot test dispense - hardware issue detected")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_tflex(sys.argv[1])
    else:
        test_tflex()
