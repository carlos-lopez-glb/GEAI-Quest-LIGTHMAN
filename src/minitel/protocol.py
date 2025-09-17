"""
MiniTel-Lite Protocol Implementation

This module implements the MiniTel-Lite v3.0 protocol specification.
Handles frame encoding/decoding, command structures, and protocol validation.
"""

import struct
import hashlib
import base64
from typing import Tuple, Optional
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class Command(IntEnum):
    """MiniTel-Lite command codes"""
    HELLO = 0x01
    DUMP = 0x02
    STOP_CMD = 0x04
    HELLO_ACK = 0x81
    DUMP_FAILED = 0x82
    DUMP_OK = 0x83
    STOP_OK = 0x84


class ProtocolError(Exception):
    """Base exception for protocol-related errors"""
    pass


class Frame:
    """Represents a MiniTel-Lite protocol frame"""
    
    def __init__(self, cmd: int, nonce: int, payload: bytes = b''):
        self.cmd = cmd
        self.nonce = nonce
        self.payload = payload
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> bytes:
        """Calculate SHA-256 hash of CMD + NONCE + PAYLOAD"""
        data = struct.pack('B', self.cmd) + struct.pack('>I', self.nonce) + self.payload
        return hashlib.sha256(data).digest()
    
    def encode(self) -> bytes:
        """Encode frame to wire format: LEN (2 bytes) | DATA_B64"""
        binary_frame = (
            struct.pack('B', self.cmd) +
            struct.pack('>I', self.nonce) +
            self.payload +
            self.hash
        )
        
        b64_data = base64.b64encode(binary_frame)
        length = len(b64_data)
        
        if length > 65535:
            raise ProtocolError(f"Frame too large: {length} bytes")
        
        return struct.pack('>H', length) + b64_data
    
    @classmethod
    def decode(cls, data: bytes) -> 'Frame':
        """Decode frame from wire format"""
        if len(data) < 2:
            raise ProtocolError("Frame too short for length prefix")
        
        length = struct.unpack('>H', data[:2])[0]
        
        if len(data) < 2 + length:
            raise ProtocolError(f"Incomplete frame: expected {length} bytes, got {len(data) - 2}")
        
        try:
            b64_data = data[2:2 + length]
            binary_frame = base64.b64decode(b64_data)
        except Exception as e:
            raise ProtocolError(f"Base64 decode error: {e}")
        
        if len(binary_frame) < 37:  # 1 + 4 + 32 minimum
            raise ProtocolError("Binary frame too short")
        
        cmd = struct.unpack('B', binary_frame[:1])[0]
        nonce = struct.unpack('>I', binary_frame[1:5])[0]
        payload = binary_frame[5:-32]
        received_hash = binary_frame[-32:]
        
        frame = cls(cmd, nonce, payload)
        
        if frame.hash != received_hash:
            raise ProtocolError("Hash validation failed")
        
        return frame
    
    def __repr__(self) -> str:
        return f"Frame(cmd=0x{self.cmd:02x}, nonce={self.nonce}, payload_len={len(self.payload)})"


class MiniTelProtocol:
    """MiniTel-Lite protocol handler"""
    
    def __init__(self):
        self.nonce = 0
        logger.debug("Initialized MiniTel protocol handler")
    
    def create_hello_frame(self) -> Frame:
        """Create HELLO command frame"""
        frame = Frame(Command.HELLO, self.nonce)
        logger.debug(f"Created HELLO frame with nonce {self.nonce}")
        return frame
    
    def create_dump_frame(self) -> Frame:
        """Create DUMP command frame"""
        frame = Frame(Command.DUMP, self.nonce)
        logger.debug(f"Created DUMP frame with nonce {self.nonce}")
        return frame
    
    def create_stop_frame(self) -> Frame:
        """Create STOP_CMD command frame"""
        frame = Frame(Command.STOP_CMD, self.nonce)
        logger.debug(f"Created STOP_CMD frame with nonce {self.nonce}")
        return frame
    
    def update_nonce(self, received_nonce: int) -> None:
        """Update local nonce based on server response"""
        expected_nonce = self.nonce + 1
        if received_nonce != expected_nonce:
            raise ProtocolError(f"Nonce mismatch: expected {expected_nonce}, got {received_nonce}")
        
        self.nonce = received_nonce + 1
        logger.debug(f"Updated nonce to {self.nonce}")
    
    def validate_response(self, frame: Frame, expected_cmd: Command) -> None:
        """Validate server response frame"""
        if frame.cmd != expected_cmd:
            raise ProtocolError(f"Unexpected command: expected 0x{expected_cmd:02x}, got 0x{frame.cmd:02x}")
        
        logger.debug(f"Validated response: cmd=0x{frame.cmd:02x}, nonce={frame.nonce}")