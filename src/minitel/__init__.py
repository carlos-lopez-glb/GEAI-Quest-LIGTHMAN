"""
MiniTel-Lite Protocol Implementation

A minimalist TCP-based protocol implementation for educational purposes.
Implements MiniTel-Lite v3.0 with proper state management and security features.
Enhanced for LIGHTMAN mission operations.
"""

from .protocol import Frame, Command, ProtocolError, MiniTelProtocol
from .server import MiniTelServer, ConnectionState
from .client import MiniTelClient
from .enhanced_client import EnhancedMiniTelClient

__version__ = "3.0"
__all__ = [
    "Frame", 
    "Command", 
    "ProtocolError", 
    "MiniTelProtocol",
    "MiniTelServer", 
    "ConnectionState",
    "MiniTelClient",
    "EnhancedMiniTelClient"
]