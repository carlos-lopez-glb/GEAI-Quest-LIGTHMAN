"""
MiniTel-Lite Client Implementation

Implements a TCP client that connects to MiniTel-Lite v3.0 servers.
Handles proper nonce sequencing and command/response flow.
Enhanced with session recording capabilities for mission analysis.
"""

import socket
import logging
import time
from typing import Optional
from .protocol import Frame, Command, ProtocolError, MiniTelProtocol

logger = logging.getLogger(__name__)


class MiniTelClient:
    """MiniTel-Lite v3.0 TCP Client"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.socket = None
        self.protocol = MiniTelProtocol()
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the MiniTel server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
            
        except socket.error as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        logger.info("Disconnected from server")
    
    def _send_frame(self, frame: Frame) -> Optional[Frame]:
        """Send frame and receive response"""
        if not self.connected:
            raise ProtocolError("Not connected to server")
        
        try:
            # Send frame
            data = frame.encode()
            self.socket.send(data)
            logger.debug(f"Sent: {frame}")
            
            # Receive response
            response_frame = self._receive_frame()
            logger.debug(f"Received: {response_frame}")
            
            return response_frame
            
        except socket.error as e:
            logger.error(f"Network error: {e}")
            self.connected = False
            raise ProtocolError(f"Network error: {e}")
    
    def _receive_frame(self) -> Frame:
        """Receive and decode a frame from the server"""
        # Read length prefix
        length_data = self._receive_exact(2)
        frame_length = int.from_bytes(length_data, 'big')
        
        # Read frame data
        frame_data = self._receive_exact(frame_length)
        
        # Decode frame
        return Frame.decode(length_data + frame_data)
    
    def _receive_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                raise ProtocolError("Connection closed by server")
            data += chunk
        return data
    
    def send_hello(self) -> bool:
        """Send HELLO command and handle response"""
        try:
            frame = self.protocol.create_hello_frame()
            response = self._send_frame(frame)
            
            self.protocol.validate_response(response, Command.HELLO_ACK)
            self.protocol.update_nonce(response.nonce)
            
            logger.info("HELLO handshake successful")
            return True
            
        except ProtocolError as e:
            logger.error(f"HELLO failed: {e}")
            return False
    
    def send_dump(self) -> Optional[str]:
        """Send DUMP command and return secret if successful"""
        try:
            frame = self.protocol.create_dump_frame()
            response = self._send_frame(frame)
            
            if response.cmd == Command.DUMP_FAILED:
                self.protocol.update_nonce(response.nonce)
                logger.info("DUMP failed (expected on first attempt)")
                return None
                
            elif response.cmd == Command.DUMP_OK:
                self.protocol.update_nonce(response.nonce)
                secret = response.payload.decode('utf-8')
                logger.info("DUMP successful!")
                return secret
                
            else:
                raise ProtocolError(f"Unexpected DUMP response: 0x{response.cmd:02x}")
                
        except ProtocolError as e:
            logger.error(f"DUMP failed: {e}")
            return None
    
    def send_stop(self) -> bool:
        """Send STOP_CMD command"""
        try:
            frame = self.protocol.create_stop_frame()
            response = self._send_frame(frame)
            
            self.protocol.validate_response(response, Command.STOP_OK)
            self.protocol.update_nonce(response.nonce)
            
            logger.info("STOP_CMD successful")
            return True
            
        except ProtocolError as e:
            logger.error(f"STOP_CMD failed: {e}")
            return False
    
    def run_full_sequence(self) -> Optional[str]:
        """Run the complete protocol sequence to get the secret"""
        if not self.connected:
            logger.error("Not connected to server")
            return None
        
        # Step 1: HELLO
        if not self.send_hello():
            return None
        
        # Step 2: First DUMP (should fail)
        self.send_dump()
        
        # Step 3: Second DUMP (should succeed)
        secret = self.send_dump()
        
        # Step 4: STOP_CMD
        self.send_stop()
        
        return secret


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = MiniTelClient()
    
    try:
        if client.connect():
            secret = client.run_full_sequence()
            if secret:
                print(f"🎉 Secret retrieved: {secret}")
            else:
                print("❌ Failed to retrieve secret")
        else:
            print("❌ Failed to connect to server")
            
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    finally:
        client.disconnect()