"""
Session Recording Module

Provides functionality to record MiniTel-Lite protocol sessions
for later analysis and replay.
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SessionRecord:
    """Represents a single protocol interaction"""
    timestamp: float
    step_number: int
    direction: str  # 'request' or 'response'
    command: str
    nonce: int
    payload_hex: str
    payload_text: Optional[str]
    frame_hex: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionRecord':
        """Create from dictionary"""
        return cls(**data)


class SessionRecorder:
    """Records MiniTel-Lite protocol sessions"""
    
    def __init__(self, enabled: bool = False, output_dir: str = "recordings"):
        self.enabled = enabled
        self.output_dir = Path(output_dir)
        self.session_records: List[SessionRecord] = []
        self.session_start_time = None
        self.step_counter = 0
        
        if self.enabled:
            self.output_dir.mkdir(exist_ok=True)
            logger.info(f"Session recording enabled, output dir: {self.output_dir}")
    
    def start_session(self) -> str:
        """Start a new recording session"""
        if not self.enabled:
            return ""
            
        self.session_start_time = time.time()
        self.session_records.clear()
        self.step_counter = 0
        
        # Generate session filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        
        logger.info(f"Started recording session: {session_id}")
        return session_id
    
    def record_frame(self, direction: str, command: str, nonce: int, 
                    payload: bytes, frame_data: bytes) -> None:
        """Record a protocol frame"""
        if not self.enabled or self.session_start_time is None:
            return
        
        self.step_counter += 1
        
        # Convert payload to text if possible
        payload_text = None
        try:
            if payload:
                payload_text = payload.decode('utf-8')
        except UnicodeDecodeError:
            payload_text = None
        
        record = SessionRecord(
            timestamp=time.time(),
            step_number=self.step_counter,
            direction=direction,
            command=command,
            nonce=nonce,
            payload_hex=payload.hex() if payload else "",
            payload_text=payload_text,
            frame_hex=frame_data.hex()
        )
        
        self.session_records.append(record)
        logger.debug(f"Recorded {direction}: {command} (step {self.step_counter})")
    
    def save_session(self, session_id: str) -> str:
        """Save the current session to file"""
        if not self.enabled or not self.session_records:
            return ""
        
        filename = f"{session_id}.json"
        filepath = self.output_dir / filename
        
        session_data = {
            "session_id": session_id,
            "start_time": self.session_start_time,
            "end_time": time.time(),
            "total_steps": len(self.session_records),
            "records": [record.to_dict() for record in self.session_records]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Session saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return ""
    
    def load_session(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load a session from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded session: {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.session_records:
            return {"total_steps": 0, "commands": []}
        
        commands = [record.command for record in self.session_records]
        return {
            "total_steps": len(self.session_records),
            "commands": commands,
            "start_time": self.session_start_time,
            "duration": time.time() - self.session_start_time if self.session_start_time else 0
        }