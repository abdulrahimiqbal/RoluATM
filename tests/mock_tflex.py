#!/usr/bin/env python3
"""
Mock T-Flex Coin Dispenser Simulator
Asyncio TCP server that simulates T-Flex serial protocol for testing
"""

import asyncio
import argparse
import logging
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MockTFlexState:
    """Mock T-Flex hardware state"""
    coins_available: int = 1000
    low_coin_threshold: int = 50
    lid_open: bool = False
    fault: bool = False
    busy: bool = False
    total_dispensed: int = 0
    jam_simulation: bool = False
    
    @property
    def low_coin(self) -> bool:
        return self.coins_available <= self.low_coin_threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MockTFlexProtocol(asyncio.Protocol):
    """Mock T-Flex serial protocol handler"""
    
    # Command constants (same as real driver)
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
    
    def __init__(self, state: MockTFlexState):
        self.state = state
        self.transport: Optional[asyncio.Transport] = None
        self.buffer = bytearray()
        
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.info(f"Mock T-Flex connected from {peername}")
        self.transport = transport
    
    def data_received(self, data):
        self.buffer.extend(data)
        self._process_buffer()
    
    def connection_lost(self, exc):
        logger.info("Mock T-Flex connection lost")
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC-8 checksum"""
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
    
    def _process_buffer(self):
        """Process incoming data buffer for complete packets"""
        while len(self.buffer) >= 5:  # Minimum packet size
            # Look for packet start
            if self.buffer[0] != 0x02:  # STX
                self.buffer.pop(0)
                continue
            
            # Check if we have enough data for the packet
            if len(self.buffer) < 2:
                break
                
            packet_length = self.buffer[1] + 4  # STX + LEN + DATA + CRC + ETX
            if len(self.buffer) < packet_length:
                break
            
            # Extract packet
            packet = bytes(self.buffer[:packet_length])
            self.buffer = self.buffer[packet_length:]
            
            # Process packet
            self._handle_packet(packet)
    
    def _handle_packet(self, packet: bytes):
        """Handle a complete T-Flex packet"""
        if len(packet) < 5:
            logger.warning(f"Invalid packet length: {len(packet)}")
            return
        
        if packet[0] != 0x02 or packet[-1] != 0x03:
            logger.warning("Invalid packet framing")
            return
        
        # Verify CRC
        data_bytes = packet[1:-2]
        received_crc = packet[-2]
        calculated_crc = self._calculate_crc(data_bytes)
        
        if received_crc != calculated_crc:
            logger.warning("CRC mismatch")
            return
        
        # Extract command and data
        length = packet[1]
        if length > 0:
            command = packet[2]
            cmd_data = packet[3:2+length] if length > 1 else b""
            
            logger.info(f"Received command: 0x{command:02X} with {len(cmd_data)} bytes data")
            
            # Process command
            response = self._process_command(command, cmd_data)
            self._send_response(response)
    
    def _process_command(self, command: int, data: bytes) -> bytes:
        """Process T-Flex command and return response"""
        if command == self.CMD_STATUS:
            return self._handle_status()
        
        elif command == self.CMD_DISPENSE:
            return self._handle_dispense(data)
        
        elif command == self.CMD_RESET:
            return self._handle_reset()
        
        elif command == self.CMD_CALIBRATE:
            return self._handle_calibrate()
        
        else:
            logger.warning(f"Unknown command: 0x{command:02X}")
            return bytes([self.RESP_ERROR])
    
    def _handle_status(self) -> bytes:
        """Handle status command"""
        status_flags = 0
        
        if self.state.low_coin:
            status_flags |= 0x01
        if self.state.lid_open:
            status_flags |= 0x02
        if self.state.fault:
            status_flags |= 0x04
        if self.state.busy:
            status_flags |= 0x08
        
        coins_high = (self.state.coins_available >> 8) & 0xFF
        coins_low = self.state.coins_available & 0xFF
        
        logger.info(f"Status: coins={self.state.coins_available}, flags=0x{status_flags:02X}")
        
        return bytes([self.RESP_OK, status_flags, coins_high, coins_low])
    
    def _handle_dispense(self, data: bytes) -> bytes:
        """Handle dispense command"""
        if len(data) < 2:
            logger.warning("Dispense command missing coin count")
            return bytes([self.RESP_ERROR])
        
        coins_requested = (data[0] << 8) | data[1]
        
        logger.info(f"Dispense request: {coins_requested} coins")
        
        # Check for fault conditions
        if self.state.fault:
            return bytes([self.RESP_FAULT])
        
        if self.state.lid_open:
            return bytes([self.RESP_LID_OPEN])
        
        if self.state.busy:
            return bytes([self.RESP_BUSY])
        
        if coins_requested > self.state.coins_available:
            return bytes([self.RESP_LOW_COIN])
        
        # Simulate jam condition
        if self.state.jam_simulation and coins_requested > 10:
            logger.warning("Simulating coin jam")
            self.state.fault = True
            return bytes([self.RESP_FAULT])
        
        # Simulate dispense delay
        asyncio.create_task(self._simulate_dispense(coins_requested))
        
        return bytes([self.RESP_OK])
    
    async def _simulate_dispense(self, coins: int):
        """Simulate coin dispensing with delay"""
        self.state.busy = True
        
        # Simulate dispensing time (50ms per coin)
        dispense_time = min(coins * 0.05, 5.0)  # Max 5 seconds
        await asyncio.sleep(dispense_time)
        
        # Update state
        self.state.coins_available -= coins
        self.state.total_dispensed += coins
        self.state.busy = False
        
        logger.info(f"Dispensed {coins} coins, {self.state.coins_available} remaining")
    
    def _handle_reset(self) -> bytes:
        """Handle reset command"""
        logger.info("Reset command received")
        
        self.state.fault = False
        self.state.busy = False
        self.state.lid_open = False
        self.state.jam_simulation = False
        
        return bytes([self.RESP_OK])
    
    def _handle_calibrate(self) -> bytes:
        """Handle calibrate command"""
        logger.info("Calibrate command received")
        
        # Simulate calibration time
        asyncio.create_task(self._simulate_calibration())
        
        return bytes([self.RESP_OK])
    
    async def _simulate_calibration(self):
        """Simulate calibration process"""
        self.state.busy = True
        await asyncio.sleep(3.0)  # 3 second calibration
        self.state.busy = False
        logger.info("Calibration complete")
    
    def _send_response(self, response_data: bytes):
        """Send response packet to client"""
        if not self.transport:
            return
        
        # Build response packet: [STX][LEN][DATA...][CRC][ETX]
        packet = bytearray([0x02])  # STX
        packet.append(len(response_data))  # Length
        packet.extend(response_data)
        
        # Calculate and append CRC
        crc = self._calculate_crc(packet[1:])
        packet.append(crc)
        packet.append(0x03)  # ETX
        
        logger.debug(f"Sending response: {packet.hex()}")
        self.transport.write(packet)

class MockTFlexServer:
    """Mock T-Flex TCP server for testing"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.host = host
        self.port = port
        self.state = MockTFlexState()
        self.server: Optional[asyncio.Server] = None
        
    async def start(self):
        """Start the mock server"""
        logger.info(f"Starting Mock T-Flex server on {self.host}:{self.port}")
        
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"Mock T-Flex server listening on {addr[0]}:{addr[1]}")
        
        # Start status monitoring
        asyncio.create_task(self._status_monitor())
        
        async with self.server:
            await self.server.serve_forever()
    
    async def _handle_client(self, reader, writer):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected from {addr}")
        
        protocol = MockTFlexProtocol(self.state)
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Simulate protocol processing
                protocol.data_received(data)
                
                # Send any responses
                if hasattr(protocol, '_pending_response'):
                    writer.write(protocol._pending_response)
                    await writer.drain()
                    delattr(protocol, '_pending_response')
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client {addr} disconnected")
    
    async def _status_monitor(self):
        """Periodic status monitoring and logging"""
        while True:
            await asyncio.sleep(30)  # Log status every 30 seconds
            logger.info(f"T-Flex State: {self.state.to_dict()}")
    
    def stop(self):
        """Stop the mock server"""
        if self.server:
            self.server.close()
            logger.info("Mock T-Flex server stopped")

class MockTFlexCLI:
    """Command-line interface for mock T-Flex control"""
    
    def __init__(self, state: MockTFlexState):
        self.state = state
    
    async def run_interactive(self):
        """Run interactive CLI"""
        logger.info("Mock T-Flex Interactive CLI")
        logger.info("Commands: status, refill [n], jam, fault, lid [open|close], reset, quit")
        
        while True:
            try:
                command = input("\nT-Flex> ").strip().lower()
                
                if not command:
                    continue
                
                if command == "quit" or command == "exit":
                    break
                
                await self._process_cli_command(command)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    
    async def _process_cli_command(self, command: str):
        """Process CLI command"""
        parts = command.split()
        cmd = parts[0]
        
        if cmd == "status":
            print(f"State: {self.state.to_dict()}")
        
        elif cmd == "refill":
            coins = int(parts[1]) if len(parts) > 1 else 1000
            self.state.coins_available = coins
            print(f"Refilled to {coins} coins")
        
        elif cmd == "jam":
            self.state.jam_simulation = True
            print("Jam simulation enabled")
        
        elif cmd == "fault":
            self.state.fault = not self.state.fault
            print(f"Fault state: {'ON' if self.state.fault else 'OFF'}")
        
        elif cmd == "lid":
            if len(parts) > 1:
                self.state.lid_open = parts[1] == "open"
            else:
                self.state.lid_open = not self.state.lid_open
            print(f"Lid: {'OPEN' if self.state.lid_open else 'CLOSED'}")
        
        elif cmd == "reset":
            self.state.fault = False
            self.state.busy = False
            self.state.lid_open = False
            self.state.jam_simulation = False
            print("Reset complete")
        
        else:
            print(f"Unknown command: {cmd}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Mock T-Flex Coin Dispenser Simulator")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8001, help="Server port")
    parser.add_argument("--interactive", action="store_true", help="Run interactive CLI")
    parser.add_argument("--coins", type=int, default=1000, help="Initial coin count")
    parser.add_argument("--low-threshold", type=int, default=50, help="Low coin threshold")
    
    args = parser.parse_args()
    
    # Create server
    server = MockTFlexServer(args.host, args.port)
    server.state.coins_available = args.coins
    server.state.low_coin_threshold = args.low_threshold
    
    # Run server and CLI concurrently
    if args.interactive:
        cli = MockTFlexCLI(server.state)
        await asyncio.gather(
            server.start(),
            cli.run_interactive()
        )
    else:
        await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Mock T-Flex simulator stopped")
