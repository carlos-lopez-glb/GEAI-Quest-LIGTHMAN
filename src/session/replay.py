"""
Session Replay Module

Provides functionality to replay recorded MiniTel-Lite protocol sessions
with step-by-step navigation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from .recorder import SessionRecord

logger = logging.getLogger(__name__)


class SessionReplayer:
    """Replays recorded MiniTel-Lite protocol sessions"""
    
    def __init__(self, session_file: str):
        self.session_file = session_file
        self.session_data: Optional[Dict[str, Any]] = None
        self.records: List[SessionRecord] = []
        self.current_step = 0
        self.total_steps = 0
        
    def load_session(self) -> bool:
        """Load session data from file"""
        try:
            with open(self.session_file, 'r') as f:
                self.session_data = json.load(f)
            
            # Convert records to SessionRecord objects
            self.records = [
                SessionRecord.from_dict(record_data) 
                for record_data in self.session_data['records']
            ]
            
            self.total_steps = len(self.records)
            self.current_step = 0
            
            logger.info(f"Loaded session with {self.total_steps} steps")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session metadata"""
        if not self.session_data:
            return {}
        
        return {
            "session_id": self.session_data.get("session_id", "unknown"),
            "start_time": self.session_data.get("start_time", 0),
            "end_time": self.session_data.get("end_time", 0),
            "total_steps": self.total_steps,
            "duration": self.session_data.get("end_time", 0) - self.session_data.get("start_time", 0)
        }
    
    def get_current_record(self) -> Optional[SessionRecord]:
        """Get the current step record"""
        if 0 <= self.current_step < len(self.records):
            return self.records[self.current_step]
        return None
    
    def next_step(self) -> bool:
        """Move to next step"""
        if self.current_step < len(self.records) - 1:
            self.current_step += 1
            return True
        return False
    
    def previous_step(self) -> bool:
        """Move to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            return True
        return False
    
    def goto_step(self, step_number: int) -> bool:
        """Go to specific step"""
        if 0 <= step_number < len(self.records):
            self.current_step = step_number
            return True
        return False
    
    def get_step_position(self) -> tuple[int, int]:
        """Get current position (current_step, total_steps)"""
        return (self.current_step + 1, self.total_steps)  # 1-based for display
    
    def format_current_step(self) -> Dict[str, str]:
        """Format current step for display"""
        record = self.get_current_record()
        if not record:
            return {"error": "No record at current step"}
        
        # Format timestamp
        from datetime import datetime
        timestamp_str = datetime.fromtimestamp(record.timestamp).strftime("%H:%M:%S.%f")[:-3]
        
        # Determine arrow direction
        arrow = "→" if record.direction == "request" else "←"
        
        # Format payload
        payload_display = ""
        if record.payload_text:
            payload_display = f' "{record.payload_text}"'
        elif record.payload_hex:
            payload_display = f" [{record.payload_hex}]"
        
        return {
            "step_info": f"Step {record.step_number}/{self.total_steps}",
            "timestamp": timestamp_str,
            "direction": f"{arrow} {record.direction.upper()}",
            "command": record.command,
            "nonce": f"nonce={record.nonce}",
            "payload": payload_display,
            "frame_hex": record.frame_hex[:64] + "..." if len(record.frame_hex) > 64 else record.frame_hex
        }
    
    def get_session_summary(self) -> List[str]:
        """Get a summary of all steps in the session"""
        summary = []
        for i, record in enumerate(self.records):
            arrow = "→" if record.direction == "request" else "←"
            payload_info = ""
            if record.payload_text:
                payload_info = f' "{record.payload_text[:20]}{"..." if len(record.payload_text) > 20 else ""}"'
            
            summary.append(f"{i+1:2d}. {arrow} {record.command} (nonce={record.nonce}){payload_info}")
        
        return summary