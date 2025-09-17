#!/usr/bin/env python3
"""
Test Mission Scenario

Demonstrates complete LIGHTMAN mission with local server and session recording.
"""

import sys
import threading
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minitel import MiniTelServer
from lightman import LightmanTerminal


def run_test_server():
    """Run test server"""
    server = MiniTelServer(host='localhost', port=8888)
    try:
        server.start()
    except:
        pass


def main():
    """Run test mission scenario"""
    print("🎯 LIGHTMAN Mission Test Scenario")
    print("=" * 50)
    
    # Start test server in background
    print("🚀 Starting test server...")
    server_thread = threading.Thread(target=run_test_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)  # Give server time to start
    
    # Run mission with recording
    print("🎯 Executing LIGHTMAN mission with recording...")
    terminal = LightmanTerminal()
    
    try:
        # Connect with recording enabled
        if terminal.mission_connect('localhost', 8888, enable_recording=True):
            print("✅ Connection established")
            
            # Execute mission
            override_codes = terminal.execute_mission()
            
            if override_codes:
                print(f"🎉 MISSION SUCCESS!")
                print(f"🔐 Override codes: {override_codes}")
                
                # Check recordings
                recordings_dir = Path("recordings")
                recordings = list(recordings_dir.glob("*.json"))
                if recordings:
                    print(f"📝 Session recorded: {recordings[-1]}")
                    
                    # Quick verification of recording
                    import json
                    with open(recordings[-1], 'r') as f:
                        data = json.load(f)
                    
                    print(f"📊 Session stats: {data['total_steps']} steps recorded")
                    commands = [r['command'] for r in data['records']]
                    print(f"🔍 Commands: {' → '.join(commands)}")
                    
                    return True
                else:
                    print("❌ No session recording found")
                    return False
            else:
                print("❌ Mission failed")
                return False
        else:
            print("❌ Connection failed")
            return False
            
    finally:
        terminal._cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)