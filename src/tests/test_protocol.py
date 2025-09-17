"""
Basic tests for MiniTel-Lite protocol implementation
"""

import unittest
import threading
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from minitel import MiniTelServer, MiniTelClient, Frame, Command


class TestMiniTelProtocol(unittest.TestCase):
    """Test MiniTel-Lite protocol implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.server = MiniTelServer(host='localhost', port=8888)
        self.server_thread = None
        
    def tearDown(self):
        """Clean up test environment"""
        if self.server:
            self.server.stop()
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1)
    
    def start_server(self):
        """Start server in background thread"""
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        time.sleep(0.1)  # Give server time to start
    
    def test_frame_encoding_decoding(self):
        """Test frame encoding and decoding"""
        original_frame = Frame(Command.HELLO, 42, b"test payload")
        encoded_data = original_frame.encode()
        decoded_frame = Frame.decode(encoded_data)
        
        self.assertEqual(original_frame.cmd, decoded_frame.cmd)
        self.assertEqual(original_frame.nonce, decoded_frame.nonce)
        self.assertEqual(original_frame.payload, decoded_frame.payload)
        self.assertEqual(original_frame.hash, decoded_frame.hash)
    
    def test_empty_payload_frame(self):
        """Test frame with empty payload"""
        original_frame = Frame(Command.HELLO, 0)
        encoded_data = original_frame.encode()
        decoded_frame = Frame.decode(encoded_data)
        
        self.assertEqual(original_frame.cmd, decoded_frame.cmd)
        self.assertEqual(original_frame.nonce, decoded_frame.nonce)
        self.assertEqual(original_frame.payload, b'')
    
    def test_client_server_interaction(self):
        """Test complete client-server interaction"""
        self.start_server()
        
        client = MiniTelClient(host='localhost', port=8888)
        
        try:
            # Test connection
            self.assertTrue(client.connect())
            
            # Test full sequence
            secret = client.run_full_sequence()
            self.assertIsNotNone(secret)
            self.assertIn("FLAG", secret)
            
        finally:
            client.disconnect()
    
    def test_hello_handshake(self):
        """Test HELLO handshake specifically"""
        self.start_server()
        
        client = MiniTelClient(host='localhost', port=8888)
        
        try:
            self.assertTrue(client.connect())
            self.assertTrue(client.send_hello())
            
        finally:
            client.disconnect()


if __name__ == '__main__':
    unittest.main()