"""
Tests for Enhanced MiniTel-Lite Client

Comprehensive test suite covering connection handling, session recording,
error recovery, and mission-specific functionality.
"""

import unittest
import threading
import time
import tempfile
import json
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from minitel import MiniTelServer
from minitel.enhanced_client import EnhancedMiniTelClient
from session.recorder import SessionRecorder


class TestEnhancedClient(unittest.TestCase):
    """Test Enhanced MiniTel-Lite Client functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.server = MiniTelServer(host='localhost', port=8889)
        self.server_thread = None
        self.temp_dir = tempfile.mkdtemp()
        
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
    
    def test_basic_connection(self):
        """Test basic connection functionality"""
        self.start_server()
        
        client = EnhancedMiniTelClient(host='localhost', port=8889)
        
        try:
            self.assertTrue(client.connect())
            self.assertTrue(client.connected)
        finally:
            client.disconnect()
    
    def test_connection_retry(self):
        """Test connection retry logic"""
        # Don't start server - should fail and retry
        client = EnhancedMiniTelClient(host='localhost', port=8889, max_retries=2)
        
        start_time = time.time()
        success = client.connect()
        duration = time.time() - start_time
        
        self.assertFalse(success)
        # Should have taken time for retries (exponential backoff)
        self.assertGreater(duration, 2.0)  # At least 2 seconds for retries
    
    def test_session_recording(self):
        """Test session recording functionality"""
        self.start_server()
        
        # Create session recorder
        recorder = SessionRecorder(enabled=True, output_dir=self.temp_dir)
        client = EnhancedMiniTelClient(
            host='localhost', 
            port=8889, 
            session_recorder=recorder
        )
        
        try:
            self.assertTrue(client.connect())
            
            # Execute mission sequence
            override_codes = client.retrieve_override_codes()
            self.assertIsNotNone(override_codes)
            self.assertIn("FLAG", override_codes)
            
            # Verify recording was created
            recordings = list(Path(self.temp_dir).glob("*.json"))
            self.assertGreater(len(recordings), 0)
            
            # Verify recording content
            with open(recordings[0], 'r') as f:
                session_data = json.load(f)
            
            self.assertIn('records', session_data)
            self.assertGreater(len(session_data['records']), 0)
            
            # Should have request/response pairs
            commands = [record['command'] for record in session_data['records']]
            self.assertIn('HELLO', commands)
            self.assertIn('HELLO_ACK', commands)
            self.assertIn('DUMP', commands)
            
        finally:
            client.disconnect()
    
    def test_mission_sequence(self):
        """Test complete mission sequence"""
        self.start_server()
        
        client = EnhancedMiniTelClient(host='localhost', port=8889)
        
        try:
            self.assertTrue(client.connect())
            
            # Test individual steps
            self.assertTrue(client.send_hello())
            
            # First DUMP should fail
            success, secret = client.send_dump()
            self.assertFalse(success)
            self.assertIsNone(secret)
            
            # Second DUMP should succeed
            success, secret = client.send_dump()
            self.assertTrue(success)
            self.assertIsNotNone(secret)
            self.assertIn("FLAG", secret)
            
            # STOP should succeed
            self.assertTrue(client.send_stop())
            
        finally:
            client.disconnect()
    
    def test_retrieve_override_codes(self):
        """Test complete override code retrieval"""
        self.start_server()
        
        client = EnhancedMiniTelClient(host='localhost', port=8889)
        
        try:
            self.assertTrue(client.connect())
            
            override_codes = client.retrieve_override_codes()
            self.assertIsNotNone(override_codes)
            self.assertIn("FLAG{MINITEL_MASTER_2025}", override_codes)
            
        finally:
            client.disconnect()
    
    def test_connection_test(self):
        """Test connection testing functionality"""
        self.start_server()
        
        client = EnhancedMiniTelClient(host='localhost', port=8889)
        
        self.assertTrue(client.test_connection())
        self.assertFalse(client.connected)  # Should disconnect after test
    
    def test_disconnection_handling(self):
        """Test graceful handling of server disconnections"""
        self.start_server()
        
        client = EnhancedMiniTelClient(host='localhost', port=8889)
        
        try:
            self.assertTrue(client.connect())
            self.assertTrue(client.send_hello())
            
            # Stop server to simulate disconnection
            self.server.stop()
            time.sleep(0.1)
            
            # Subsequent operations should fail gracefully
            success, secret = client.send_dump()
            self.assertFalse(success)
            self.assertIsNone(secret)
            
        finally:
            client.disconnect()
    
    def test_command_name_mapping(self):
        """Test command code to name mapping"""
        client = EnhancedMiniTelClient()
        
        self.assertEqual(client._get_command_name(0x01), "HELLO")
        self.assertEqual(client._get_command_name(0x02), "DUMP")
        self.assertEqual(client._get_command_name(0x81), "HELLO_ACK")
        self.assertEqual(client._get_command_name(0x82), "DUMP_FAILED")
        self.assertEqual(client._get_command_name(0x83), "DUMP_OK")
        self.assertEqual(client._get_command_name(0xFF), "UNKNOWN_0xff")


class TestSessionRecording(unittest.TestCase):
    """Test session recording functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = SessionRecorder(enabled=True, output_dir=self.temp_dir)
    
    def test_recording_lifecycle(self):
        """Test complete recording lifecycle"""
        # Start session
        session_id = self.recorder.start_session()
        self.assertTrue(session_id)
        
        # Record some frames
        self.recorder.record_frame(
            direction="request",
            command="HELLO",
            nonce=0,
            payload=b"",
            frame_data=b"\x00\x01\x02"
        )
        
        self.recorder.record_frame(
            direction="response", 
            command="HELLO_ACK",
            nonce=1,
            payload=b"",
            frame_data=b"\x00\x01\x02\x03"
        )
        
        # Save session
        filepath = self.recorder.save_session(session_id)
        self.assertTrue(filepath)
        self.assertTrue(Path(filepath).exists())
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data['records']), 2)
        self.assertEqual(data['records'][0]['command'], 'HELLO')
        self.assertEqual(data['records'][1]['command'], 'HELLO_ACK')
    
    def test_disabled_recording(self):
        """Test that disabled recording doesn't create files"""
        recorder = SessionRecorder(enabled=False)
        session_id = recorder.start_session()
        self.assertEqual(session_id, "")
        
        recorder.record_frame("request", "HELLO", 0, b"", b"")
        filepath = recorder.save_session("test")
        self.assertEqual(filepath, "")
    
    def test_session_summary(self):
        """Test session summary functionality"""
        self.recorder.start_session()
        
        # Initially empty
        summary = self.recorder.get_session_summary()
        self.assertEqual(summary['total_steps'], 0)
        
        # Add some records
        self.recorder.record_frame("request", "HELLO", 0, b"", b"")
        self.recorder.record_frame("response", "HELLO_ACK", 1, b"", b"")
        
        summary = self.recorder.get_session_summary()
        self.assertEqual(summary['total_steps'], 2)
        self.assertEqual(summary['commands'], ['HELLO', 'HELLO_ACK'])


if __name__ == '__main__':
    # Setup logging to capture test output
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()