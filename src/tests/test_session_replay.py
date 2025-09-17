"""
Tests for Session Replay Functionality

Tests the session recording and replay components used for
mission analysis and debugging.
"""

import unittest
import tempfile
import json
import time
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from session.recorder import SessionRecorder, SessionRecord
from session.replay import SessionReplayer


class TestSessionRecord(unittest.TestCase):
    """Test SessionRecord data class"""
    
    def test_record_creation(self):
        """Test creating session records"""
        record = SessionRecord(
            timestamp=time.time(),
            step_number=1,
            direction="request",
            command="HELLO",
            nonce=0,
            payload_hex="",
            payload_text=None,
            frame_hex="010000000000"
        )
        
        self.assertEqual(record.command, "HELLO")
        self.assertEqual(record.direction, "request")
        self.assertEqual(record.nonce, 0)
    
    def test_record_serialization(self):
        """Test record to/from dict conversion"""
        original = SessionRecord(
            timestamp=1234567890.0,
            step_number=1,
            direction="request",
            command="HELLO",
            nonce=0,
            payload_hex="48656c6c6f",
            payload_text="Hello",
            frame_hex="010000000048656c6c6f"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = SessionRecord.from_dict(data)
        
        self.assertEqual(original.command, reconstructed.command)
        self.assertEqual(original.payload_text, reconstructed.payload_text)
        self.assertEqual(original.frame_hex, reconstructed.frame_hex)


class TestSessionRecorder(unittest.TestCase):
    """Test session recording functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = SessionRecorder(enabled=True, output_dir=self.temp_dir)
    
    def test_session_lifecycle(self):
        """Test complete session recording lifecycle"""
        # Start session
        session_id = self.recorder.start_session()
        self.assertTrue(session_id)
        self.assertEqual(self.recorder.step_counter, 0)
        
        # Record some interactions
        self.recorder.record_frame(
            direction="request",
            command="HELLO",
            nonce=0,
            payload=b"",
            frame_data=b"\x01\x00\x00\x00\x00"
        )
        
        self.recorder.record_frame(
            direction="response",
            command="HELLO_ACK", 
            nonce=1,
            payload=b"",
            frame_data=b"\x81\x00\x00\x00\x01"
        )
        
        # Verify records
        self.assertEqual(len(self.recorder.session_records), 2)
        self.assertEqual(self.recorder.step_counter, 2)
        
        # Save session
        filepath = self.recorder.save_session(session_id)
        self.assertTrue(filepath)
        self.assertTrue(Path(filepath).exists())
        
        # Verify saved content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['session_id'], session_id)
        self.assertEqual(data['total_steps'], 2)
        self.assertEqual(len(data['records']), 2)
    
    def test_payload_encoding(self):
        """Test payload encoding (text and hex)"""
        self.recorder.start_session()
        
        # Test with text payload
        text_payload = "Hello World".encode('utf-8')
        self.recorder.record_frame(
            direction="request",
            command="TEST",
            nonce=1,
            payload=text_payload,
            frame_data=b"\x01\x00\x00\x00\x01" + text_payload
        )
        
        record = self.recorder.session_records[0]
        self.assertEqual(record.payload_text, "Hello World")
        self.assertEqual(record.payload_hex, text_payload.hex())
        
        # Test with binary payload
        binary_payload = b"\x00\x01\x02\xFF"
        self.recorder.record_frame(
            direction="response",
            command="TEST_RESP",
            nonce=2,
            payload=binary_payload,
            frame_data=b"\x82\x00\x00\x00\x02" + binary_payload
        )
        
        record = self.recorder.session_records[1]
        self.assertIsNone(record.payload_text)  # Should be None for binary
        self.assertEqual(record.payload_hex, binary_payload.hex())
    
    def test_disabled_recorder(self):
        """Test recorder when disabled"""
        disabled_recorder = SessionRecorder(enabled=False)
        
        session_id = disabled_recorder.start_session()
        self.assertEqual(session_id, "")
        
        disabled_recorder.record_frame("request", "HELLO", 0, b"", b"")
        self.assertEqual(len(disabled_recorder.session_records), 0)
        
        filepath = disabled_recorder.save_session("test")
        self.assertEqual(filepath, "")


class TestSessionReplayer(unittest.TestCase):
    """Test session replay functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = self.temp_dir + "/test_session.json"
        
        # Create test session data
        session_data = {
            "session_id": "test_session_123",
            "start_time": 1234567890.0,
            "end_time": 1234567900.0,
            "total_steps": 4,
            "records": [
                {
                    "timestamp": 1234567891.0,
                    "step_number": 1,
                    "direction": "request",
                    "command": "HELLO",
                    "nonce": 0,
                    "payload_hex": "",
                    "payload_text": None,
                    "frame_hex": "010000000000"
                },
                {
                    "timestamp": 1234567892.0,
                    "step_number": 2,
                    "direction": "response",
                    "command": "HELLO_ACK",
                    "nonce": 1,
                    "payload_hex": "",
                    "payload_text": None,
                    "frame_hex": "810000000001"
                },
                {
                    "timestamp": 1234567893.0,
                    "step_number": 3,
                    "direction": "request",
                    "command": "DUMP",
                    "nonce": 2,
                    "payload_hex": "",
                    "payload_text": None,
                    "frame_hex": "020000000002"
                },
                {
                    "timestamp": 1234567894.0,
                    "step_number": 4,
                    "direction": "response",
                    "command": "DUMP_OK",
                    "nonce": 3,
                    "payload_hex": "464c41477b544553547d",
                    "payload_text": "FLAG{TEST}",
                    "frame_hex": "83000000000346"
                }
            ]
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)
        
        self.replayer = SessionReplayer(self.session_file)
    
    def test_load_session(self):
        """Test loading session data"""
        self.assertTrue(self.replayer.load_session())
        self.assertEqual(self.replayer.total_steps, 4)
        self.assertEqual(len(self.replayer.records), 4)
    
    def test_session_info(self):
        """Test getting session information"""
        self.replayer.load_session()
        
        info = self.replayer.get_session_info()
        self.assertEqual(info['session_id'], 'test_session_123')
        self.assertEqual(info['total_steps'], 4)
        self.assertEqual(info['duration'], 10.0)  # end_time - start_time
    
    def test_navigation(self):
        """Test step navigation"""
        self.replayer.load_session()
        
        # Initial position
        self.assertEqual(self.replayer.current_step, 0)
        current_pos, total = self.replayer.get_step_position()
        self.assertEqual(current_pos, 1)  # 1-based for display
        self.assertEqual(total, 4)
        
        # Move forward
        self.assertTrue(self.replayer.next_step())
        self.assertEqual(self.replayer.current_step, 1)
        
        self.assertTrue(self.replayer.next_step())
        self.assertEqual(self.replayer.current_step, 2)
        
        # Move backward
        self.assertTrue(self.replayer.previous_step())
        self.assertEqual(self.replayer.current_step, 1)
        
        # Test boundaries
        self.replayer.goto_step(0)
        self.assertFalse(self.replayer.previous_step())  # Can't go before first
        
        self.replayer.goto_step(3)  # Last step (0-based)
        self.assertFalse(self.replayer.next_step())  # Can't go past last
    
    def test_goto_step(self):
        """Test direct step navigation"""
        self.replayer.load_session()
        
        # Valid steps
        self.assertTrue(self.replayer.goto_step(2))
        self.assertEqual(self.replayer.current_step, 2)
        
        # Invalid steps
        self.assertFalse(self.replayer.goto_step(-1))
        self.assertFalse(self.replayer.goto_step(10))
    
    def test_current_record(self):
        """Test getting current record"""
        self.replayer.load_session()
        
        # First record
        record = self.replayer.get_current_record()
        self.assertIsNotNone(record)
        self.assertEqual(record.command, "HELLO")
        self.assertEqual(record.direction, "request")
        
        # Navigate and test
        self.replayer.next_step()
        record = self.replayer.get_current_record()
        self.assertEqual(record.command, "HELLO_ACK")
        self.assertEqual(record.direction, "response")
    
    def test_format_current_step(self):
        """Test step formatting for display"""
        self.replayer.load_session()
        
        # Test request formatting
        formatted = self.replayer.format_current_step()
        self.assertEqual(formatted['step_info'], "Step 1/4")
        self.assertEqual(formatted['command'], "HELLO")
        self.assertIn("→", formatted['direction'])  # Request arrow
        
        # Navigate to response
        self.replayer.next_step()
        formatted = self.replayer.format_current_step()
        self.assertEqual(formatted['command'], "HELLO_ACK")
        self.assertIn("←", formatted['direction'])  # Response arrow
        
        # Navigate to step with payload
        self.replayer.goto_step(3)  # DUMP_OK with payload
        formatted = self.replayer.format_current_step()
        self.assertEqual(formatted['command'], "DUMP_OK")
        self.assertIn("FLAG{TEST}", formatted['payload'])
    
    def test_session_summary(self):
        """Test session summary generation"""
        self.replayer.load_session()
        
        summary = self.replayer.get_session_summary()
        self.assertEqual(len(summary), 4)
        
        # Check format
        self.assertIn("1. → HELLO", summary[0])
        self.assertIn("2. ← HELLO_ACK", summary[1])
        self.assertIn("3. → DUMP", summary[2])
        self.assertIn("4. ← DUMP_OK", summary[3])
        self.assertIn("FLAG{TEST}", summary[3])  # Payload preview


if __name__ == '__main__':
    # Setup minimal logging
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()