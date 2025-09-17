"""
Enhanced MiniTel-Lite Client with Session Recording

Mission-critical client for LIGHTMAN operations with comprehensive
session recording and reconnection capabilities.
"""

import socket
import logging
import time
from typing import Optional, Tuple
from .protocol import Frame, Command, ProtocolError, MiniTelProtocol

logger = logging.getLogger(__name__)


class EnhancedMiniTelClient:
    """
    Enhanced MiniTel-Lite client with session recording capabilities.
    
    Features:
    - Automatic reconnection on disconnection
    - Session recording for analysis
    - Graceful error handling
    - Mission-specific override code retrieval
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8080, 
                 session_recorder=None, max_retries: int = 3):
        self.host = host
        self.port = port
        self.socket = None
        self.protocol = MiniTelProtocol()
        self.connected = False
        self.session_recorder = session_recorder
        self.max_retries = max_retries
        self.connection_attempts = 0
        
    def connect(self) -> bool:
        """Connect to the MiniTel server with retry logic"""
        self.connection_attempts = 0
        
        while self.connection_attempts < self.max_retries:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10.0)  # Increased timeout for remote connections
                self.socket.connect((self.host, self.port))
                self.connected = True
                
                logger.info(f"✅ Connected to {self.host}:{self.port} (attempt {self.connection_attempts + 1})")
                
                # Start session recording if enabled
                if self.session_recorder:
                    session_id = self.session_recorder.start_session()
                    logger.info(f"📝 Started recording session: {session_id}")
                
                return True
                
            except socket.error as e:
                self.connection_attempts += 1
                logger.warning(f"❌ Connection attempt {self.connection_attempts} failed: {e}")
                
                if self.connection_attempts < self.max_retries:
                    wait_time = 2 ** self.connection_attempts  # Exponential backoff
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"🚫 Max retries ({self.max_retries}) exceeded")
                    
        return False
    
    def disconnect(self):
        """Disconnect from the server and save session"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        
        # Save session recording if enabled
        if (self.session_recorder and 
            hasattr(self.session_recorder, 'session_start_time') and 
            self.session_recorder.session_start_time is not None and
            len(self.session_recorder.session_records) > 0):
            
            from datetime import datetime
            session_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filepath = self.session_recorder.save_session(session_id)
            if filepath:
                logger.info(f"💾 Session saved: {filepath}")
        
        logger.info("📴 Disconnected from server")
    
    def _send_frame_with_recording(self, frame: Frame) -> Optional[Frame]:
        """Send frame and receive response with session recording"""
        if not self.connected:
            raise ProtocolError("Not connected to server")
        
        try:
            # Encode frame
            data = frame.encode()
            
            # Record outgoing frame
            if self.session_recorder:
                command_name = self._get_command_name(frame.cmd)
                self.session_recorder.record_frame(
                    direction="request",
                    command=command_name,
                    nonce=frame.nonce,
                    payload=frame.payload,
                    frame_data=data
                )
            
            # Send frame
            self.socket.send(data)
            logger.debug(f"→ Sent: {frame}")
            
            # Receive response
            response_frame = self._receive_frame()
            
            # Record incoming frame
            if self.session_recorder:
                command_name = self._get_command_name(response_frame.cmd)
                response_data = response_frame.encode()
                self.session_recorder.record_frame(
                    direction="response",
                    command=command_name,
                    nonce=response_frame.nonce,
                    payload=response_frame.payload,
                    frame_data=response_data
                )
            
            logger.debug(f"← Received: {response_frame}")
            return response_frame
            
        except socket.error as e:
            logger.error(f"💥 Network error: {e}")
            self.connected = False
            raise ProtocolError(f"Network error: {e}")
    
    def _receive_frame(self) -> Frame:
        """Receive and decode a frame from the server"""
        try:
            # Read length prefix
            length_data = self._receive_exact(2)
            frame_length = int.from_bytes(length_data, 'big')
            
            # Read frame data
            frame_data = self._receive_exact(frame_length)
            
            # Decode frame
            return Frame.decode(length_data + frame_data)
            
        except socket.timeout:
            raise ProtocolError("Receive timeout - server may have disconnected")
        except socket.error as e:
            raise ProtocolError(f"Receive error: {e}")
    
    def _receive_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket"""
        data = b''
        start_time = time.time()
        timeout = 10.0  # 10 second timeout
        
        while len(data) < num_bytes:
            try:
                chunk = self.socket.recv(num_bytes - len(data))
                if not chunk:
                    raise ProtocolError("Connection closed by server")
                data += chunk
                
                # Check for timeout
                if time.time() - start_time > timeout:
                    raise ProtocolError("Receive timeout")
                    
            except socket.timeout:
                raise ProtocolError("Socket timeout")
                
        return data
    
    def _get_command_name(self, cmd_code: int) -> str:
        """Get human-readable command name"""
        command_names = {
            Command.HELLO: "HELLO",
            Command.DUMP: "DUMP", 
            Command.STOP_CMD: "STOP_CMD",
            Command.HELLO_ACK: "HELLO_ACK",
            Command.DUMP_FAILED: "DUMP_FAILED",
            Command.DUMP_OK: "DUMP_OK",
            Command.STOP_OK: "STOP_OK"
        }
        return command_names.get(cmd_code, f"UNKNOWN_0x{cmd_code:02x}")
    
    def send_hello(self) -> bool:
        """Send HELLO command and handle response"""
        try:
            frame = self.protocol.create_hello_frame()
            response = self._send_frame_with_recording(frame)
            
            self.protocol.validate_response(response, Command.HELLO_ACK)
            self.protocol.update_nonce(response.nonce)
            
            logger.info("✅ HELLO handshake successful")
            return True
            
        except ProtocolError as e:
            logger.error(f"❌ HELLO failed: {e}")
            return False
    
    def send_dump(self) -> Tuple[bool, Optional[str]]:
        """
        Send DUMP command and return (success, secret)
        Returns (True, secret) on success, (False, None) on failure
        """
        try:
            frame = self.protocol.create_dump_frame()
            response = self._send_frame_with_recording(frame)
            
            if response.cmd == Command.DUMP_FAILED:
                self.protocol.update_nonce(response.nonce)
                logger.info("ℹ️  DUMP failed (expected on first attempt)")
                return (False, None)
                
            elif response.cmd == Command.DUMP_OK:
                self.protocol.update_nonce(response.nonce)
                secret = response.payload.decode('utf-8')
                logger.info("🎉 DUMP successful - override code retrieved!")
                return (True, secret)
                
            else:
                raise ProtocolError(f"Unexpected DUMP response: 0x{response.cmd:02x}")
                
        except ProtocolError as e:
            logger.error(f"❌ DUMP failed: {e}")
            return (False, None)
    
    def send_stop(self) -> bool:
        """Send STOP_CMD command"""
        try:
            frame = self.protocol.create_stop_frame()
            response = self._send_frame_with_recording(frame)
            
            self.protocol.validate_response(response, Command.STOP_OK)
            self.protocol.update_nonce(response.nonce)
            
            logger.info("✅ STOP_CMD successful")
            return True
            
        except ProtocolError as e:
            logger.error(f"❌ STOP_CMD failed: {e}")
            return False
    
    def retrieve_override_codes(self) -> Optional[str]:
        """
        Execute the mission sequence to retrieve emergency override codes.
        
        Mission Protocol:
        1. HELLO handshake
        2. First DUMP (expected to fail)
        3. Second DUMP (should return override codes)
        4. STOP_CMD acknowledgment
        
        Returns:
            Override codes on success, None on failure
        """
        if not self.connected:
            logger.error("🚫 Not connected to server")
            return None
        
        logger.info("🎯 Initiating override code retrieval sequence...")
        
        try:
            # Step 1: HELLO handshake
            logger.info("🤝 Step 1: Authenticating with HELLO protocol...")
            if not self.send_hello():
                logger.error("💥 Authentication failed")
                return None
            
            # Step 2: First DUMP (expected to fail)
            logger.info("🔍 Step 2: First DUMP attempt (expecting failure)...")
            success, secret = self.send_dump()
            if success:
                logger.warning("⚠️  Unexpected: First DUMP succeeded")
            
            # Step 3: Second DUMP (should succeed with override codes)
            logger.info("🔍 Step 3: Second DUMP attempt (expecting override codes)...")
            success, override_codes = self.send_dump()
            
            if not success or not override_codes:
                logger.error("💥 Failed to retrieve override codes")
                return None
            
            # Step 4: STOP_CMD acknowledgment
            logger.info("🏁 Step 4: Sending STOP_CMD acknowledgment...")
            self.send_stop()
            
            logger.info("✅ Mission sequence completed successfully!")
            return override_codes
            
        except Exception as e:
            logger.error(f"💥 Mission sequence failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to server without protocol sequence"""
        try:
            if not self.connected and not self.connect():
                return False
            
            # Try a simple hello
            return self.send_hello()
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False