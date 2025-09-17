"""
MiniTel-Lite Server Implementation

Implements a TCP server that handles MiniTel-Lite v3.0 protocol with:
- Connection state management
- 2-second connection timeout
- Nonce sequence validation
- HELLO, DUMP, STOP_CMD command handling
"""

import socket
import threading
import time
import logging
from typing import Dict, Optional
from .protocol import Frame, Command, ProtocolError, MiniTelProtocol

logger = logging.getLogger(__name__)


class ConnectionState:
    """Manages state for a single client connection"""
    
    def __init__(self):
        self.expected_client_nonce = 0  # First client message should have nonce 0
        self.server_nonce = 1  # Server starts responses with nonce 1
        self.last_command = None
        self.dump_count = 0
        self.connected_at = time.time()
        self.last_activity = time.time()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def is_expired(self, timeout: float = 2.0) -> bool:
        """Check if connection has exceeded timeout"""
        return time.time() - self.last_activity > timeout


class MiniTelServer:
    """MiniTel-Lite v3.0 TCP Server"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.connections: Dict[str, ConnectionState] = {}
        self.secret = "FLAG{MINITEL_MASTER_2025}"
        
    def start(self):
        """Start the server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            logger.info(f"MiniTel-Lite server started on {self.host}:{self.port}")
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self._cleanup_connections, daemon=True)
            cleanup_thread.start()
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    logger.info(f"New connection from {address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                        
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Server stopped")
    
    def _cleanup_connections(self):
        """Background thread to clean up expired connections"""
        while self.running:
            try:
                expired_keys = []
                for key, state in self.connections.items():
                    if state.is_expired():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.connections[key]
                    logger.debug(f"Cleaned up expired connection: {key}")
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        client_key = f"{address[0]}:{address[1]}"
        state = ConnectionState()
        self.connections[client_key] = state
        
        try:
            while self.running:
                # Check for timeout
                if state.is_expired():
                    logger.info(f"Connection {client_key} timed out")
                    break
                
                # Read frame length
                try:
                    client_socket.settimeout(0.1)  # Non-blocking with short timeout
                    length_data = client_socket.recv(2)
                    if not length_data:
                        break
                    
                    if len(length_data) < 2:
                        logger.warning(f"Incomplete length from {client_key}")
                        break
                    
                    # Read frame data
                    frame_length = int.from_bytes(length_data, 'big')
                    frame_data = b''
                    
                    while len(frame_data) < frame_length:
                        chunk = client_socket.recv(frame_length - len(frame_data))
                        if not chunk:
                            break
                        frame_data += chunk
                    
                    if len(frame_data) < frame_length:
                        logger.warning(f"Incomplete frame from {client_key}")
                        break
                    
                    # Decode and process frame
                    try:
                        frame = Frame.decode(length_data + frame_data)
                        response = self._process_command(frame, state)
                        
                        if response:
                            client_socket.send(response.encode())
                            state.update_activity()
                        
                    except ProtocolError as e:
                        logger.warning(f"Protocol error from {client_key}: {e}")
                        break
                        
                except socket.timeout:
                    continue  # Check timeout and try again
                except socket.error:
                    break
                    
        except Exception as e:
            logger.error(f"Client handler error for {client_key}: {e}")
        finally:
            client_socket.close()
            if client_key in self.connections:
                del self.connections[client_key]
            logger.info(f"Disconnected {client_key}")
    
    def _process_command(self, frame: Frame, state: ConnectionState) -> Optional[Frame]:
        """Process received command and return response"""
        
        # Validate nonce sequence
        if frame.nonce != state.expected_client_nonce:
            logger.warning(f"Nonce mismatch: expected {state.expected_client_nonce}, got {frame.nonce}")
            raise ProtocolError("Invalid nonce sequence")
        
        if frame.cmd == Command.HELLO:
            logger.debug("Processing HELLO command")
            state.last_command = Command.HELLO
            state.dump_count = 0  # Reset DUMP counter
            response = Frame(Command.HELLO_ACK, state.server_nonce)
            state.expected_client_nonce += 2  # Client will send next with nonce 2
            state.server_nonce += 2  # Server will respond with nonce 3
            return response
            
        elif frame.cmd == Command.DUMP:
            logger.debug(f"Processing DUMP command (count: {state.dump_count})")
            
            if state.last_command != Command.HELLO:
                logger.warning("DUMP without prior HELLO")
                raise ProtocolError("DUMP requires HELLO first")
            
            state.dump_count += 1
            
            # First DUMP fails, subsequent ones succeed
            if state.dump_count == 1:
                response = Frame(Command.DUMP_FAILED, state.server_nonce)
            else:
                response = Frame(Command.DUMP_OK, state.server_nonce, self.secret.encode())
            
            state.expected_client_nonce += 2
            state.server_nonce += 2
            return response
            
        elif frame.cmd == Command.STOP_CMD:
            logger.debug("Processing STOP_CMD command")
            response = Frame(Command.STOP_OK, state.server_nonce)
            state.expected_client_nonce += 2
            state.server_nonce += 2
            return response
            
        else:
            logger.warning(f"Unknown command: 0x{frame.cmd:02x}")
            raise ProtocolError(f"Unknown command: 0x{frame.cmd:02x}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = MiniTelServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        server.stop()