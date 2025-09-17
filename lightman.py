#!/usr/bin/env python3
"""
LIGHTMAN Mission Terminal

Agent LIGHTMAN's primary infiltration tool for the MiniTel-Lite network.
Retrieves emergency override codes from the JOSHUA system.

Mission Objective:
    Infiltrate MiniTel-Lite network and retrieve emergency override codes
    through authenticated protocol sequence with session recording.

Usage:
    python lightman.py <host> <port> [--record] [--test]
    python lightman.py replay <session_file>

Examples:
    python lightman.py 192.168.1.100 8080 --record
    python lightman.py localhost 8080 --test
    python lightman.py replay recordings/mission_20250917_124530.json
"""

import sys
import argparse
import logging
import signal
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from minitel.enhanced_client import EnhancedMiniTelClient
from session.recorder import SessionRecorder
from tui.replay_app import ReplayTUI


class LightmanTerminal:
    """
    LIGHTMAN Mission Terminal
    
    Primary interface for Agent LIGHTMAN's infiltration operations.
    Handles connection to MiniTel-Lite servers and override code retrieval.
    """
    
    def __init__(self):
        self.client = None
        self.session_recorder = None
        self.logger = self._setup_logging()
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('lightman_mission.log')
            ]
        )
        return logging.getLogger('LIGHTMAN')
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.logger.info("🛑 Mission interrupted - initiating cleanup...")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.client:
            self.client.disconnect()
    
    def print_banner(self):
        """Print mission banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🎯 LIGHTMAN TERMINAL 🎯                   ║
║                                                              ║
║              MiniTel-Lite Network Infiltration              ║
║                Emergency Override Retrieval                 ║
║                                                              ║
║  Mission: Retrieve emergency override codes from JOSHUA     ║
║  Protocol: MiniTel-Lite v3.0 Authentication                 ║
║  Agent: LIGHTMAN                                             ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def mission_connect(self, host: str, port: int, enable_recording: bool = False) -> bool:
        """
        Establish connection to target MiniTel-Lite server
        
        Args:
            host: Target server hostname/IP
            port: Target server port
            enable_recording: Enable session recording
            
        Returns:
            True if connection successful, False otherwise
        """
        self.logger.info(f"🎯 MISSION START: Targeting {host}:{port}")
        
        # Initialize session recorder if requested
        if enable_recording:
            self.session_recorder = SessionRecorder(enabled=True, output_dir="recordings")
            self.logger.info("📝 Session recording enabled")
        
        # Initialize enhanced client
        self.client = EnhancedMiniTelClient(
            host=host, 
            port=port, 
            session_recorder=self.session_recorder,
            max_retries=3
        )
        
        # Attempt connection
        self.logger.info("🔗 Establishing secure connection...")
        if not self.client.connect():
            self.logger.error("💥 MISSION FAILED: Could not establish connection")
            return False
        
        self.logger.info("✅ Connection established - proceeding with infiltration")
        return True
    
    def execute_mission(self) -> str:
        """
        Execute the complete mission sequence
        
        Returns:
            Override codes on success, empty string on failure
        """
        if not self.client or not self.client.connected:
            self.logger.error("🚫 No active connection - mission aborted")
            return ""
        
        self.logger.info("🚀 Initiating protocol sequence...")
        
        # Execute the override code retrieval sequence
        override_codes = self.client.retrieve_override_codes()
        
        if override_codes:
            self.logger.info("🎉 MISSION SUCCESS: Override codes retrieved!")
            self.logger.info(f"🔐 CODES: {override_codes}")
            return override_codes
        else:
            self.logger.error("💥 MISSION FAILED: Could not retrieve override codes")
            return ""
    
    def test_connection(self, host: str, port: int) -> bool:
        """Test connection to server without full mission"""
        self.logger.info(f"🧪 Testing connection to {host}:{port}")
        
        self.client = EnhancedMiniTelClient(host=host, port=port, max_retries=1)
        
        if self.client.test_connection():
            self.logger.info("✅ Connection test successful")
            self.client.disconnect()
            return True
        else:
            self.logger.error("❌ Connection test failed")
            return False
    
    def replay_session(self, session_file: str) -> bool:
        """Replay a recorded session using TUI"""
        self.logger.info(f"🎬 Replaying session: {session_file}")
        
        if not Path(session_file).exists():
            self.logger.error(f"Session file not found: {session_file}")
            return False
        
        try:
            tui = ReplayTUI(session_file)
            return tui.run()
        except Exception as e:
            self.logger.error(f"Replay failed: {e}")
            return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="LIGHTMAN Terminal - MiniTel-Lite Network Infiltration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lightman.py 192.168.1.100 8080 --record
  python lightman.py localhost 8080 --test  
  python lightman.py replay recordings/mission_20250917_124530.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Mission command (default)
    mission_parser = subparsers.add_parser('mission', help='Execute infiltration mission')
    mission_parser.add_argument('host', help='Target server hostname/IP')
    mission_parser.add_argument('port', type=int, help='Target server port')
    mission_parser.add_argument('--record', action='store_true', 
                               help='Enable session recording')
    mission_parser.add_argument('--test', action='store_true',
                               help='Test connection only (no mission execution)')
    
    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay recorded session')
    replay_parser.add_argument('session_file', help='Path to session recording file')
    
    # Handle default case (mission without subcommand)
    if len(sys.argv) > 1 and sys.argv[1] not in ['mission', 'replay']:
        # Insert 'mission' as default subcommand
        sys.argv.insert(1, 'mission')
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    terminal = LightmanTerminal()
    terminal.print_banner()
    
    try:
        if args.command == 'replay':
            # Replay mode
            success = terminal.replay_session(args.session_file)
            sys.exit(0 if success else 1)
            
        elif args.command == 'mission':
            if args.test:
                # Test mode
                success = terminal.test_connection(args.host, args.port)
                sys.exit(0 if success else 1)
            else:
                # Full mission mode
                if not terminal.mission_connect(args.host, args.port, args.record):
                    sys.exit(1)
                
                override_codes = terminal.execute_mission()
                
                if override_codes:
                    print(f"\n🎉 MISSION ACCOMPLISHED!")
                    print(f"🔐 EMERGENCY OVERRIDE CODES: {override_codes}")
                    print(f"📡 Transmit these codes to NORAD command immediately!")
                    sys.exit(0)
                else:
                    print(f"\n💥 MISSION FAILED!")
                    print(f"🔄 Check logs and retry with different parameters")
                    sys.exit(1)
        
    except KeyboardInterrupt:
        terminal.logger.info("🛑 Mission interrupted by user")
        sys.exit(1)
    except Exception as e:
        terminal.logger.error(f"💥 Critical error: {e}")
        sys.exit(1)
    finally:
        terminal._cleanup()


if __name__ == "__main__":
    main()